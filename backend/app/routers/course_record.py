from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Attendance, Student, Class, Course, Schedule, Teacher, LearningCard, CardTransaction
import io
import openpyxl
from fastapi.responses import StreamingResponse
from urllib.parse import quote
from app.services.image_service import ImageService

router = APIRouter()


def _get_card_transaction_records(db, filters, change_types, page, page_size):
    """从 card_transactions 聚合记录，支持多种变更类型"""
    # 不使用错误的预加载
    query = db.query(CardTransaction).options(
        joinedload(CardTransaction.card).joinedload(LearningCard.student),
        joinedload(CardTransaction.card).joinedload(LearningCard.course),
        joinedload(CardTransaction.card).joinedload(LearningCard.class_),
        joinedload(CardTransaction.attendance)
    ).filter(CardTransaction.change_type.in_(change_types))

    if filters.get('student_id'):
        query = query.join(CardTransaction.card).join(LearningCard.student).filter(Student.id == filters['student_id'])
    if filters.get('course_id'):
        query = query.join(CardTransaction.card).join(LearningCard.course).filter(Course.id == filters['course_id'])
    if filters.get('class_id'):
        query = query.join(CardTransaction.card).join(LearningCard.class_).filter(Class.id == filters['class_id'])
    if filters.get('start_date'):
        query = query.filter(CardTransaction.occurred_at >= datetime.strptime(filters['start_date'], "%Y-%m-%d"))
    if filters.get('end_date'):
        query = query.filter(CardTransaction.occurred_at <= datetime.strptime(filters['end_date'], "%Y-%m-%d") + timedelta(days=1))

    total = query.count()
    records = query.order_by(CardTransaction.occurred_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for txn in records:
        card = txn.card
        student = card.student if card else None
        course = card.course if card else None
        class_obj = card.class_ if card else None
        
        teacher = None
        attendance_status = None
        if txn.attendance:
            att = txn.attendance
            attendance_status = att.status
            # 获取 teacher 信息（如果有关联）
            if att.teacher_id:
                teacher = db.query(Teacher).get(att.teacher_id)

        # 映射类型
        type_map = {
            'attendance': '考勤',
            'custom_add': '自定义增加课时',
            'custom_sub': '自定义减少课时',
            'gift_add': '增加赠送课时',
            'gift_sub': '减少赠送课时',
            'transfer_in': '转入课时',
            'transfer_out': '转出课时',
            'purchase': '购课',
            'refund': '退费',
            'graduation': '结业'
        }
        display_type = type_map.get(txn.change_type, txn.change_type)
        hour_type = '付费' if txn.paid_hours_change != 0 else ('赠送' if txn.gift_hours_change != 0 else '-')
        deduct_hours = (txn.paid_hours_change or 0) + (txn.gift_hours_change or 0)
        deduct_amount = txn.amount_change or 0.0

        result.append({
            "type": display_type,
            "student_name": student.name if student else '',
            "student_phone": student.phone if student else '',
            "student_avatar": ImageService.get_url(student.avatar) if student else '',
            "occurrence_date": txn.occurred_at.strftime('%Y-%m-%d') if txn.occurred_at else '',
            "class_time": txn.occurred_at.strftime('%Y-%m-%d') if txn.occurred_at else '',
            "class_name": class_obj.name if class_obj else '',
            "course_name": course.name if course else '',
            "hour_type": hour_type,
            "deduct_hours": deduct_hours,
            "deduct_amount": deduct_amount,
            "teacher_name": teacher.name if teacher else '',
            "attendance_status": attendance_status,
            "remark": txn.reason,
            "created_at": str(txn.created_at)
        })
    return result, total


@router.get("/attendance-records")
def get_attendance_records(
    class_id: Optional[int] = Query(None),
    student_id: Optional[int] = Query(None),
    course_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db)
):
    filters = {
        'class_id': class_id, 'student_id': student_id, 'course_id': course_id,
        'start_date': start_date, 'end_date': end_date
    }
    records, total = _get_card_transaction_records(
        db, filters, ['attendance'], page, page_size
    )
    return {"code": 0, "data": {"records": records, "total": total}}


@router.get("/custom-records")
def get_custom_records(
    class_id: Optional[int] = Query(None),
    student_id: Optional[int] = Query(None),
    course_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db)
):
    filters = {
        'class_id': class_id, 'student_id': student_id, 'course_id': course_id,
        'start_date': start_date, 'end_date': end_date
    }
    records, total = _get_card_transaction_records(
        db, filters, ['custom_add', 'custom_sub'], page, page_size
    )
    return {"code": 0, "data": {"records": records, "total": total}}


@router.get("/gift-records")
def get_gift_records(
    class_id: Optional[int] = Query(None),
    student_id: Optional[int] = Query(None),
    course_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db)
):
    filters = {
        'class_id': class_id, 'student_id': student_id, 'course_id': course_id,
        'start_date': start_date, 'end_date': end_date
    }
    records, total = _get_card_transaction_records(
        db, filters, ['gift_add', 'gift_sub'], page, page_size
    )
    return {"code": 0, "data": {"records": records, "total": total}}


@router.get("/transfer-records")
def get_transfer_records(
    class_id: Optional[int] = Query(None),
    student_id: Optional[int] = Query(None),
    course_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db)
):
    filters = {
        'class_id': class_id, 'student_id': student_id, 'course_id': course_id,
        'start_date': start_date, 'end_date': end_date
    }
    records, total = _get_card_transaction_records(
        db, filters, ['transfer_in', 'transfer_out'], page, page_size
    )
    return {"code": 0, "data": {"records": records, "total": total}}


@router.get("/export")
def export_course_records(
    class_id: Optional[int] = Query(None),
    course_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    record_type: Optional[str] = Query('attendance'),
    db: Session = Depends(get_db)
):
    type_map = {
        'attendance': '考勤记录',
        'custom': '自定义增减课时记录',
        'gift': '赠送课时记录',
        'transfer': '转入转出记录'
    }
    change_types_map = {
        'attendance': ['attendance'],
        'custom': ['custom_add', 'custom_sub'],
        'gift': ['gift_add', 'gift_sub'],
        'transfer': ['transfer_in', 'transfer_out']
    }
    change_types = change_types_map.get(record_type, [])
    filters = {
        'class_id': class_id, 'course_id': course_id,
        'start_date': start_date, 'end_date': end_date
    }
    records, _ = _get_card_transaction_records(db, filters, change_types, 1, 10000)

    filename = f"{type_map.get(record_type, '课消记录')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = type_map.get(record_type, "课消记录")
    if records:
        headers = list(records[0].keys())
        ws.append(headers)
        for row in records:
            ws.append([row.get(h, '') for h in headers])
    else:
        ws.append(["无数据"])
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    encoded_filename = quote(filename)
    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers=headers
    )