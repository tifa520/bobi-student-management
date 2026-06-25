# backend/app/routers/stats.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, or_
from datetime import datetime, timedelta
from typing import Optional, List
from app.database import get_db
from app.models import (
    Order, Student, Course, Class, PaymentLog, 
    Attendance, LearningCard, CardTransaction,
    Item, InventoryTransaction, MiscFee, Refund,
    ActivityRegistration
)
from app.services.image_service import ImageService
import openpyxl
from io import BytesIO
from fastapi.responses import StreamingResponse
from urllib.parse import quote

router = APIRouter(prefix="/stats", tags=["统计"])


# ==================== 通用工具函数 ====================

def parse_date(date_str: str) -> datetime:
    """解析日期字符串"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")


def get_date_filter(query, field, start_date: Optional[str], end_date: Optional[str]):
    """通用日期范围过滤"""
    if start_date:
        query = query.filter(field >= parse_date(start_date))
    if end_date:
        query = query.filter(field <= parse_date(end_date) + timedelta(days=1))
    return query


# ==================== 1. 报名统计 ====================

@router.get("/enroll")
def get_enroll_stats(
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    course_id: Optional[int] = Query(None, description="课程ID"),
    enroll_type: Optional[str] = Query(None, description="报名类型"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """报名统计"""
    query = db.query(Order).filter(
        Order.is_active == True,
        Order.is_invalid == False,
        Order.enroll_type != '尾款补费'
    )
    
    query = get_date_filter(query, Order.created_at, start_date, end_date)
    if course_id:
        query = query.filter(Order.course_id == course_id)
    if enroll_type:
        query = query.filter(Order.enroll_type == enroll_type)
    
    # KPI
    all_ids = [o.id for o in query.all()]
    total_count = len(all_ids)
    new_count = query.filter(Order.enroll_type == '新报').count()
    renew_count = query.filter(Order.enroll_type == '续报').count()
    expand_count = query.filter(Order.enroll_type == '扩科').count()
    total_amount = db.query(func.sum(Order.payable_amount)).filter(Order.id.in_(all_ids)).scalar() or 0 if all_ids else 0
    
    # 趋势
    trend = db.query(
        func.date(Order.created_at).label('date'),
        func.count(Order.id).label('count')
    ).filter(Order.id.in_(all_ids)).group_by(func.date(Order.created_at)).order_by('date').all() if all_ids else []
    
    # 分布
    distribution = db.query(
        Order.enroll_type.label('name'),
        func.count(Order.id).label('value')
    ).filter(Order.id.in_(all_ids)).group_by(Order.enroll_type).all() if all_ids else []
    
    # 分页列表
    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    list_data = []
    for o in orders:
        student = db.query(Student).get(o.student_id)
        course = db.query(Course).get(o.course_id)
        list_data.append({
            "order_no": o.order_no,
            "student_name": student.name if student else '',
            "student_avatar": ImageService.get_url(student.avatar) if student else '',
            "course_name": course.name if course else '',
            "enroll_type": o.enroll_type,
            "payable_amount": float(o.payable_amount),
            "payment_method": o.payment_method,
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M:%S") if o.created_at else ''
        })
    
    return {
        "code": 0,
        "data": {
            "summary": {
                "total_count": total_count,
                "new_count": new_count,
                "renew_count": renew_count,
                "expand_count": expand_count,
                "total_amount": float(total_amount)
            },
            "trend": [{"date": d.date, "value": d.count} for d in trend],
            "distribution": [{"name": d.name, "value": d.value} for d in distribution] if distribution else [],
            "list": list_data,
            "total": total
        }
    }


@router.get("/enroll/export")
def export_enroll_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    course_id: Optional[int] = Query(None),
    enroll_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """导出报名统计"""
    query = db.query(Order).filter(
        Order.is_active == True,
        Order.is_invalid == False,
        Order.enroll_type != '尾款补费'
    )
    query = get_date_filter(query, Order.created_at, start_date, end_date)
    if course_id:
        query = query.filter(Order.course_id == course_id)
    if enroll_type:
        query = query.filter(Order.enroll_type == enroll_type)
    
    orders = query.order_by(Order.created_at.desc()).all()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "报名统计"
    headers = ["订单号", "学员姓名", "课程", "报名类型", "金额", "支付方式", "报名时间"]
    ws.append(headers)
    
    for o in orders:
        student = db.query(Student).get(o.student_id)
        course = db.query(Course).get(o.course_id)
        ws.append([
            o.order_no,
            student.name if student else '',
            course.name if course else '',
            o.enroll_type,
            float(o.payable_amount),
            o.payment_method,
            o.created_at.strftime("%Y-%m-%d %H:%M:%S") if o.created_at else ''
        ])
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    filename = f"报名统计_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"}
    )


# ==================== 2. 收费统计 ====================

@router.get("/payment")
def get_payment_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    payment_method: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """收费统计"""
    query = db.query(PaymentLog)
    query = get_date_filter(query, PaymentLog.occurred_at, start_date, end_date)
    if payment_method:
        query = query.filter(PaymentLog.payment_method == payment_method)
    
    # KPI
    all_logs = query.all()
    total_amount = sum(float(log.amount) for log in all_logs)
    total_count = len(all_logs)
    avg_amount = total_amount / total_count if total_count > 0 else 0
    max_amount = max([float(log.amount) for log in all_logs]) if all_logs else 0
    
    # 趋势（按日）
    trend = db.query(
        func.date(PaymentLog.occurred_at).label('date'),
        func.sum(PaymentLog.amount).label('amount')
    ).filter(PaymentLog.id.in_([l.id for l in all_logs])).group_by(
        func.date(PaymentLog.occurred_at)
    ).order_by('date').all() if all_logs else []
    
    # 分布（按支付方式）
    distribution = db.query(
        PaymentLog.payment_method.label('name'),
        func.sum(PaymentLog.amount).label('value')
    ).filter(PaymentLog.id.in_([l.id for l in all_logs])).group_by(
        PaymentLog.payment_method
    ).all() if all_logs else []
    
    # 分页列表
    total = query.count()
    logs = query.order_by(PaymentLog.occurred_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    list_data = []
    for log in logs:
        order = db.query(Order).get(log.order_id)
        student = db.query(Student).get(order.student_id) if order else None
        list_data.append({
            "order_no": order.order_no if order else '',
            "student_name": student.name if student else '',
            "student_avatar": ImageService.get_url(student.avatar) if student else '',
            "amount": float(log.amount),
            "payment_method": log.payment_method,
            "payment_type": log.payment_type,
            "remark": log.remark,
            "occurred_at": log.occurred_at.strftime("%Y-%m-%d %H:%M:%S") if log.occurred_at else ''
        })
    
    return {
        "code": 0,
        "data": {
            "summary": {
                "total_amount": round(total_amount, 2),
                "total_count": total_count,
                "avg_amount": round(avg_amount, 2),
                "max_amount": round(max_amount, 2)
            },
            "trend": [{"date": d.date, "value": round(float(d.amount), 2)} for d in trend],
            "distribution": [{"name": d.name, "value": round(float(d.value), 2)} for d in distribution] if distribution else [],
            "list": list_data,
            "total": total
        }
    }


# ==================== 3. 课时统计 ====================

@router.get("/hours")
def get_hours_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    course_id: Optional[int] = Query(None),
    class_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """课时统计"""
    # 获取考勤记录（过滤attendance类型）
    query = db.query(CardTransaction).filter(
        CardTransaction.change_type == 'attendance'
    )
    
    # 通过card关联到course进行过滤
    if course_id:
        query = query.join(LearningCard, CardTransaction.card_id == LearningCard.id).filter(
            LearningCard.course_id == course_id
        )
    if class_id:
        query = query.join(LearningCard, CardTransaction.card_id == LearningCard.id).filter(
            LearningCard.class_id == class_id
        )
    
    query = get_date_filter(query, CardTransaction.occurred_at, start_date, end_date)
    
    # KPI
    all_txns = query.all()
    total_hours = sum(abs(txn.paid_hours_change or 0) + abs(txn.gift_hours_change or 0) for txn in all_txns)
    total_amount = sum(abs(txn.amount_change or 0) for txn in all_txns)
    attendance_count = len(all_txns)
    avg_price = total_amount / total_hours if total_hours > 0 else 0
    
    # 趋势（按日）
    trend = db.query(
        func.date(CardTransaction.occurred_at).label('date'),
        func.sum(func.abs(CardTransaction.paid_hours_change) + func.abs(CardTransaction.gift_hours_change)).label('hours')
    ).filter(CardTransaction.id.in_([t.id for t in all_txns])).group_by(
        func.date(CardTransaction.occurred_at)
    ).order_by('date').all() if all_txns else []
    
    # 分布（按课程）
    distribution = db.query(
        Course.name.label('name'),
        func.sum(func.abs(CardTransaction.paid_hours_change) + func.abs(CardTransaction.gift_hours_change)).label('value')
    ).join(LearningCard, CardTransaction.card_id == LearningCard.id).join(
        Course, LearningCard.course_id == Course.id
    ).filter(CardTransaction.id.in_([t.id for t in all_txns])).group_by(
        Course.id, Course.name
    ).all() if all_txns else []
    
    # 分页列表
    total = query.count()
    txns = query.order_by(CardTransaction.occurred_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    list_data = []
    for txn in txns:
        card = db.query(LearningCard).get(txn.card_id)
        student = db.query(Student).get(card.student_id) if card else None
        course = db.query(Course).get(card.course_id) if card else None
        class_obj = db.query(Class).get(card.class_id) if card else None
        hours = abs(txn.paid_hours_change or 0) + abs(txn.gift_hours_change or 0)
        list_data.append({
            "student_name": student.name if student else '',
            "student_avatar": ImageService.get_url(student.avatar) if student else '',
            "course_name": course.name if course else '',
            "class_name": class_obj.name if class_obj else '',
            "hours": hours,
            "amount": float(abs(txn.amount_change or 0)),
            "occurred_at": txn.occurred_at.strftime("%Y-%m-%d %H:%M:%S") if txn.occurred_at else ''
        })
    
    return {
        "code": 0,
        "data": {
            "summary": {
                "total_hours": total_hours,
                "total_amount": round(total_amount, 2),
                "attendance_count": attendance_count,
                "avg_price": round(avg_price, 2)
            },
            "trend": [{"date": d.date, "value": int(d.hours)} for d in trend],
            "distribution": [{"name": d.name, "value": int(d.value)} for d in distribution] if distribution else [],
            "list": list_data,
            "total": total
        }
    }


# ==================== 4. 物品统计 ====================

@router.get("/items")
def get_items_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    payment_method: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """物品销售统计"""
    query = db.query(InventoryTransaction).filter(
        InventoryTransaction.transaction_type.in_(['sale'])
    )
    query = get_date_filter(query, InventoryTransaction.created_at, start_date, end_date)
    if category:
        query = query.join(Item, InventoryTransaction.item_id == Item.id).filter(Item.category == category)
    if payment_method:
        query = query.filter(InventoryTransaction.payment_method == payment_method)
    
    # KPI
    all_txns = query.all()
    total_amount = sum(float(txn.total_amount) for txn in all_txns)
    total_cost = sum(float(txn.cost_of_goods_sold) for txn in all_txns)
    total_profit = total_amount - total_cost
    total_quantity = sum(abs(txn.quantity) for txn in all_txns)
    
    # 趋势（按日）
    trend = db.query(
        func.date(InventoryTransaction.created_at).label('date'),
        func.sum(InventoryTransaction.total_amount).label('amount')
    ).filter(InventoryTransaction.id.in_([t.id for t in all_txns])).group_by(
        func.date(InventoryTransaction.created_at)
    ).order_by('date').all() if all_txns else []
    
    # 分布（按物品）
    distribution = db.query(
        Item.name.label('name'),
        func.sum(InventoryTransaction.total_amount).label('value')
    ).join(Item, InventoryTransaction.item_id == Item.id).filter(
        InventoryTransaction.id.in_([t.id for t in all_txns])
    ).group_by(Item.id, Item.name).order_by(func.sum(InventoryTransaction.total_amount).desc()).limit(10).all() if all_txns else []
    
    # 分页列表
    total = query.count()
    txns = query.order_by(InventoryTransaction.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    list_data = []
    for txn in txns:
        item = db.query(Item).get(txn.item_id)
        list_data.append({
            "item_name": item.name if item else '',
            "item_image": ImageService.get_url(item.image_url) if item else '',
            "category": item.category if item else '',
            "quantity": abs(txn.quantity),
            "unit_price": float(txn.unit_price),
            "total_amount": float(txn.total_amount),
            "cost": float(txn.cost_of_goods_sold),
            "profit": float(txn.total_amount - txn.cost_of_goods_sold),
            "payment_method": txn.payment_method or '-',
            "created_at": txn.created_at.strftime("%Y-%m-%d %H:%M:%S") if txn.created_at else ''
        })
    
    return {
        "code": 0,
        "data": {
            "summary": {
                "total_amount": round(total_amount, 2),
                "total_cost": round(total_cost, 2),
                "total_profit": round(total_profit, 2),
                "total_quantity": total_quantity
            },
            "trend": [{"date": d.date, "value": round(float(d.amount), 2)} for d in trend],
            "distribution": [{"name": d.name, "value": round(float(d.value), 2)} for d in distribution] if distribution else [],
            "list": list_data,
            "total": total
        }
    }


# ==================== 5. 杂费统计 ====================

@router.get("/fees")
def get_fees_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    fee_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """杂费统计"""
    query = db.query(MiscFee)
    query = get_date_filter(query, MiscFee.created_at, start_date, end_date)
    if fee_type:
        query = query.filter(MiscFee.fee_type == fee_type)
    if status:
        query = query.filter(MiscFee.status == status)
    
    # KPI
    all_fees = query.all()
    total_income = sum(float(f.amount) for f in all_fees if f.amount > 0)
    total_expense = sum(float(abs(f.amount)) for f in all_fees if f.amount < 0)
    net_income = total_income - total_expense
    record_count = len(all_fees)
    
    # 趋势（按日）
    trend = db.query(
        func.date(MiscFee.created_at).label('date'),
        func.sum(MiscFee.amount).label('amount')
    ).filter(MiscFee.id.in_([f.id for f in all_fees])).group_by(
        func.date(MiscFee.created_at)
    ).order_by('date').all() if all_fees else []
    
    # 分布（按费用类型）
    distribution = db.query(
        MiscFee.fee_type.label('name'),
        func.sum(MiscFee.amount).label('value')
    ).filter(MiscFee.id.in_([f.id for f in all_fees])).group_by(
        MiscFee.fee_type
    ).all() if all_fees else []
    
    # 分页列表
    total = query.count()
    fees = query.order_by(MiscFee.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    list_data = []
    for f in fees:
        student = db.query(Student).get(f.student_id)
        fee_type_map = {
            'item_sale': '物品销售',
            'activity': '活动收费',
            'refund': '退款',
            'other': '其他'
        }
        status_map = {
            'pending': '待缴费',
            'partial': '部分缴纳',
            'paid': '已结清',
            'refunded': '已退款'
        }
        list_data.append({
            "student_name": student.name if student else '',
            "student_avatar": ImageService.get_url(student.avatar) if student else '',
            "fee_type": fee_type_map.get(f.fee_type, f.fee_type),
            "fee_type_key": f.fee_type,
            "description": f.description,
            "amount": float(f.amount),
            "paid_amount": float(f.paid_amount),
            "points_used": f.points_used,
            "status": status_map.get(f.status, f.status),
            "payment_method": f.payment_method or '-',
            "created_at": f.created_at.strftime("%Y-%m-%d %H:%M:%S") if f.created_at else ''
        })
    
    return {
        "code": 0,
        "data": {
            "summary": {
                "total_income": round(total_income, 2),
                "total_expense": round(total_expense, 2),
                "net_income": round(net_income, 2),
                "record_count": record_count
            },
            "trend": [{"date": d.date, "value": round(float(d.amount), 2)} for d in trend],
            "distribution": [{"name": d.name, "value": round(float(d.value), 2)} for d in distribution] if distribution else [],
            "list": list_data,
            "total": total
        }
    }


# ==================== 6. 退费统计 ====================

@router.get("/refund")
def get_refund_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    refund_type: Optional[str] = Query(None),
    refund_method: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """退费统计"""
    query = db.query(Refund)
    query = get_date_filter(query, Refund.created_at, start_date, end_date)
    if refund_type:
        query = query.filter(Refund.refund_type == refund_type)
    if refund_method:
        query = query.filter(Refund.refund_method == refund_method)
    
    # KPI
    all_refunds = query.all()
    total_amount = sum(float(r.refund_amount) for r in all_refunds)
    total_count = len(all_refunds)
    student_ids = set(r.student_id for r in all_refunds)
    student_count = len(student_ids)
    avg_amount = total_amount / total_count if total_count > 0 else 0
    
    # 趋势（按日）
    trend = db.query(
        func.date(Refund.created_at).label('date'),
        func.sum(Refund.refund_amount).label('amount')
    ).filter(Refund.id.in_([r.id for r in all_refunds])).group_by(
        func.date(Refund.created_at)
    ).order_by('date').all() if all_refunds else []
    
    # 分布（按课程）
    distribution = db.query(
        Course.name.label('name'),
        func.sum(Refund.refund_amount).label('value')
    ).join(Course, Refund.course_id == Course.id).filter(
        Refund.id.in_([r.id for r in all_refunds])
    ).group_by(Course.id, Course.name).order_by(func.sum(Refund.refund_amount).desc()).limit(10).all() if all_refunds else []
    
    # 分页列表
    total = query.count()
    refunds = query.order_by(Refund.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    list_data = []
    for r in refunds:
        student = db.query(Student).get(r.student_id)
        course = db.query(Course).get(r.course_id)
        list_data.append({
            "student_name": student.name if student else '',
            "student_avatar": ImageService.get_url(student.avatar) if student else '',
            "course_name": course.name if course else '',
            "refund_type": r.refund_type,
            "refund_amount": float(r.refund_amount),
            "refund_method": r.refund_method,
            "reason": r.reason,
            "remark": r.remark,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else ''
        })
    
    return {
        "code": 0,
        "data": {
            "summary": {
                "total_amount": round(total_amount, 2),
                "total_count": total_count,
                "student_count": student_count,
                "avg_amount": round(avg_amount, 2)
            },
            "trend": [{"date": d.date, "value": round(float(d.amount), 2)} for d in trend],
            "distribution": [{"name": d.name, "value": round(float(d.value), 2)} for d in distribution] if distribution else [],
            "list": list_data,
            "total": total
        }
    }