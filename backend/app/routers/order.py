# backend/app/routers/order.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Order, Student, Course, Class, PaymentLog, IntegralRecord, Stage
from app.schemas import BatchRepay
from app.services.transaction_service import TransactionService
import io
import openpyxl
from fastapi.responses import StreamingResponse
from app.utils import generate_order_no

router = APIRouter()


@router.get("/orders")
def order_list(
    search: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    filter_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Order).filter(Order.enroll_type != '尾款补费')
    if search:
        query = query.join(Student).filter(Student.name.contains(search))
    if start_date:
        query = query.filter(Order.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        query = query.filter(Order.created_at <= datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))

    orders = query.order_by(Order.created_at.desc()).all()
    result = []
    for o in orders:
        student = db.query(Student).get(o.student_id)
        course = db.query(Course).get(o.course_id)
        class_ = db.query(Class).get(o.class_id) if o.class_id else None
        stage = db.query(Stage).get(o.stage_id) if o.stage_id else None  # ★ 新增

        if o.is_invalid:
            arrears = 0
        else:
            arrears = max(0, o.payable_amount - o.total_paid)

        payment_logs = db.query(PaymentLog).filter(
            PaymentLog.order_id == o.id,
            PaymentLog.payment_type.in_(['initial', 'repay'])
        ).order_by(PaymentLog.occurred_at).all()
        payment_history = [{
            "amount": log.amount,
            "method": log.payment_method,
            "type": log.payment_type,
            "occurred_at": log.occurred_at.isoformat() if log.occurred_at else '',
            "remark": log.remark
        } for log in payment_logs]

        result.append({
            "id": o.id,
            "order_no": o.order_no,
            "created_at": str(o.created_at),
            "student_id": o.student_id,
            "student_name": student.name if student else '',
            "student_phone": student.phone if student else '',
            "student_avatar": student.avatar if student else '',
            "course_name": course.name if course else '',
            "class_name": class_.name if class_ else '',
            "course_id": o.course_id,
            "enroll_type": o.enroll_type,
            "purchase_hours": o.purchase_hours,
            "total_price": o.total_price,
            "discount_amount": o.discount_amount,
            "payable_amount": o.payable_amount,
            "paid_amount": o.paid_amount,
            "total_paid": o.total_paid,
            "payment_method": o.payment_method,
            "gift_hours": o.gift_hours,
            "gift_note": o.gift_note,
            "leave_limit": o.leave_limit,
            "leave_limit_count": o.leave_limit_count,
            "validity_type": o.validity_type,
            "validity_value": o.validity_value,
            "discount_mode": o.discount_mode,
            "discount_rate": o.discount_rate,
            "direct_reduction": o.direct_reduction,
            "arrears": arrears,
            "is_invalid": o.is_invalid,
            "parent_order_id": o.parent_order_id,
            "parent_order_no": o.parent_order.order_no if o.parent_order else None,
            "remark": o.remark,
            "payment_history": payment_history,
            # ★ 新增课阶相关字段
            "stage_id": o.stage_id,
            "stage_name": stage.name if stage else '',
            "unit_price": o.unit_price,
            "price_source": o.price_source
        })
    return {"code": 0, "data": result}


@router.post("/orders/{order_id}/invalid")
def invalid_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(404, "订单不存在")

    from app.models import CardTransaction
    consumed = db.query(CardTransaction).filter(
        CardTransaction.order_id == order_id,
        CardTransaction.change_type.in_(['attendance', 'transfer_out', 'custom_sub'])
    ).first()
    if consumed:
        raise HTTPException(400, "该订单已有课消或转出记录，无法作废")

    order.is_invalid = True
    order.is_active = False
    db.flush()

    if order.gift_hours > 0:
        from app.services.transaction_service import TransactionService
        tx = TransactionService(db)
        card = tx._get_or_create_card(order.student_id, order.course_id, order.class_id)
        tx._add_card_transaction(
            card_id=card.id,
            change_type='gift_sub',
            gift_hours_change=-order.gift_hours,
            reason=f"订单作废，扣回赠送课时 {order.gift_hours}",
            order_id=order.id,
            occurred_at=order.created_at.date()
        )
        tx._refresh_card(order.student_id, order.course_id)
    else:
        from app.services.transaction_service import TransactionService
        tx = TransactionService(db)
        tx._refresh_card(order.student_id, order.course_id)

    db.commit()
    return {"code": 0, "message": "订单已作废"}


@router.get("/orders/{order_id}/can-invalidate")
def check_order_can_invalidate(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).get(order_id)
    if not order:
        return {"code": 0, "data": {"can_invalidate": False, "reason": "订单不存在"}}
    if order.is_invalid:
        return {"code": 0, "data": {"can_invalidate": False, "reason": "订单已作废"}}
    from app.models import CardTransaction
    consumed = db.query(CardTransaction).filter(
        CardTransaction.order_id == order_id,
        CardTransaction.change_type.in_(['attendance', 'transfer_out', 'custom_sub'])
    ).first()
    if consumed:
        return {"code": 0, "data": {"can_invalidate": False, "reason": "已有课消或转出记录"}}
    return {"code": 0, "data": {"can_invalidate": True, "reason": ""}}


@router.post("/orders/{order_id}/repay")
def repay_order(
    order_id: int,
    amount: float = Query(...),
    payment_method: str = Query('微信'),
    db: Session = Depends(get_db)
):
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.is_invalid:
        raise HTTPException(400, "已作废订单不能补缴")

    current_arrears = max(0, order.payable_amount - order.total_paid)
    if amount <= 0 or amount > current_arrears:
        raise HTTPException(400, "补缴金额无效")

    repay_order = Order(
        order_no=generate_order_no(db),
        student_id=order.student_id,
        course_id=order.course_id,
        class_id=order.class_id,
        enroll_type='尾款补费',
        purchase_hours=0,
        unit_price=0,
        total_price=0,
        discount_amount=0,
        payable_amount=0,
        actual_unit_price=0,
        paid_amount=amount,
        total_paid=amount,
        payment_method=payment_method,
        is_active=True,
        is_invalid=False,
        parent_order_id=order.id,
        remark=f"补缴订单 {order.order_no} 尾款 {amount} 元"
    )
    db.add(repay_order)
    db.flush()

    tx_service = TransactionService(db)
    tx_service._add_payment_log(
        order_id=order.id,
        amount=amount,
        payment_method=payment_method,
        payment_type='repay',
        remark=f"补缴尾款 {amount} 元",
        occurred_at=datetime.now()
    )

    order.total_paid += amount
    order.paid_amount = order.total_paid

    points = int(amount * 10)
    if points > 0:
        student = db.query(Student).get(order.student_id)
        if student:
            student.total_integral = (student.total_integral or 0) + points
            integral_record = IntegralRecord(
                student_id=student.id,
                change_amount=points,
                reason="尾款补费赠送积分",
                remark=f"补费{amount:.2f}元，赠送{points}积分"
            )
            db.add(integral_record)

    db.commit()
    return {"code": 0, "message": "补款成功", "data": {"repay_order_id": repay_order.id}}


@router.post("/repay/batch")
def batch_repay(data: BatchRepay, db: Session = Depends(get_db)):
    if not data.items:
        raise HTTPException(400, "请选择订单")
    results = []
    for item in data.items:
        try:
            order = db.query(Order).get(item.order_id)
            if not order:
                continue
            current_arrears = max(0, order.payable_amount - order.total_paid)
            repay_amount = min(item.amount, current_arrears)
            if repay_amount <= 0:
                continue
            tx_service = TransactionService(db)
            tx_service._add_payment_log(
                order_id=order.id,
                amount=repay_amount,
                payment_method=order.payment_method,
                payment_type='repay',
                remark=f"批量补缴尾款 {repay_amount} 元",
                occurred_at=datetime.now()
            )
            order.total_paid += repay_amount
            order.paid_amount = order.total_paid
            results.append({"order_id": order.id, "amount": repay_amount})
        except Exception as e:
            pass
    db.commit()
    return {"code": 0, "message": f"成功补缴 {len(results)} 笔"}


@router.get("/orders/export")
def export_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.enroll_type != '尾款补费').all()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "订单列表"
    headers = ["订单号", "报名时间", "学员姓名", "联系方式", "课程", "课阶", "班级", "购买课时", "原价", "优惠", "应付", "实付", "欠款", "支付方式"]
    ws.append(headers)
    for o in orders:
        student = db.query(Student).get(o.student_id)
        course = db.query(Course).get(o.course_id)
        class_ = db.query(Class).get(o.class_id) if o.class_id else None
        stage = db.query(Stage).get(o.stage_id) if o.stage_id else None
        arrears = max(0, o.payable_amount - o.total_paid)
        ws.append([
            o.order_no,
            str(o.created_at),
            student.name if student else '',
            student.phone if student else '',
            course.name if course else '',
            stage.name if stage else '',
            class_.name if class_ else '',
            o.purchase_hours,
            o.total_price,
            o.discount_amount,
            o.payable_amount,
            o.total_paid,
            arrears,
            o.payment_method
        ])
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": "attachment; filename=orders.xlsx"}
    )


@router.get("/repay-records")
def get_repay_records(
    search: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Order).filter(
        Order.enroll_type == '尾款补费',
        Order.is_invalid == False
    )

    if search:
        query = query.join(Student, Order.student_id == Student.id).filter(
            (Student.name.contains(search)) | (Order.order_no.contains(search))
        )
    if start_date:
        query = query.filter(Order.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        query = query.filter(Order.created_at <= datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))

    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for order in orders:
        student = db.query(Student).get(order.student_id)
        course = db.query(Course).get(order.course_id)
        parent_order = db.query(Order).get(order.parent_order_id) if order.parent_order_id else None
        stage = db.query(Stage).get(order.stage_id) if order.stage_id else None

        if parent_order:
            before_arrears = parent_order.payable_amount - (parent_order.total_paid - order.paid_amount)
            before_arrears = max(0, before_arrears)
        else:
            before_arrears = 0

        repay_amount = order.paid_amount
        after_arrears = max(0, before_arrears - repay_amount)
        points_granted = int(repay_amount * 10) if repay_amount > 0 else 0
        payment_method = order.payment_method
        operator = "系统"
        operate_time = order.created_at

        result.append({
            "id": order.id,
            "student_id": student.id if student else None,
            "student_name": student.name if student else '',
            "student_phone": student.phone if student else '',
            "student_avatar": student.avatar if student else '',
            "order_no": order.order_no,
            "parent_order_no": parent_order.order_no if parent_order else '',
            "repay_time": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "course_name": course.name if course else '',
            "stage_name": stage.name if stage else '',  # ★ 新增
            "before_arrears": round(before_arrears, 2),
            "repay_amount": round(repay_amount, 2),
            "after_arrears": round(after_arrears, 2),
            "payment_method": payment_method,
            "points_granted": points_granted,
            "operator": operator,
            "operate_time": operate_time.strftime("%Y-%m-%d %H:%M:%S"),
            "remark": order.remark
        })

    return {"code": 0, "data": {"items": result, "total": total}}