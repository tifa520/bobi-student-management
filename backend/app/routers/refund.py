from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import Student, StudentCourse, Course, Order, Purchase, Refund, ArchivedStudentCourse
from app.schemas import RefundCreate

router = APIRouter()


@router.get("/student/{student_id}/course/{course_id}")
def refund_info(student_id: int, course_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).get(student_id)
    if not student:
        raise HTTPException(404, "学员不存在")
    course = db.query(Course).get(course_id)
    if not course:
        raise HTTPException(404, "课程不存在")
    sc = db.query(StudentCourse).filter(
        StudentCourse.student_id == student_id,
        StudentCourse.course_id == course_id
    ).first()
    if not sc:
        raise HTTPException(404, "学员没有此课程记录")

    total_deducted = sc.total_deducted + sc.total_custom_sub

    orders = db.query(Order).filter(
        Order.student_id == student_id,
        Order.course_id == course_id,
        Order.is_active == True,
        Order.is_invalid == False
    ).all()
    total_paid = sum(o.total_paid for o in orders)
    total_purchased = sc.total_purchased

    if total_purchased > 0:
        consumed_amount = (total_paid / total_purchased) * total_deducted
    else:
        consumed_amount = 0
    refundable = round(max(0, total_paid - consumed_amount), 2)

    return {"code": 0, "data": {
        "student_name": student.name,
        "student_phone": student.phone,
        "course_name": course.name,
        "total_purchased": total_purchased,
        "total_deducted": total_deducted,
        "remaining_hours": sc.remaining_hours,
        "remaining_amount": sc.remaining_amount,
        "total_paid": total_paid,
        "refundable_amount": refundable
    }}


@router.post("/create")
def create_refund(data: RefundCreate, db: Session = Depends(get_db)):
    student = db.query(Student).get(data.student_id)
    if not student:
        raise HTTPException(404, "学员不存在")
    sc = db.query(StudentCourse).filter(
        StudentCourse.student_id == data.student_id,
        StudentCourse.course_id == data.course_id
    ).first()
    if not sc:
        raise HTTPException(404, "学员没有此课程记录")

    refund = Refund(
        student_id=data.student_id,
        course_id=data.course_id,
        refund_type=data.refund_type,
        refund_amount=data.refund_amount,
        refund_method=data.refund_method,
        reason=data.reason,
        remark=data.remark
    )
    db.add(refund)

    archive = ArchivedStudentCourse(
        student_id=data.student_id,
        course_id=data.course_id,
        snapshot_data={
            "total_purchased": sc.total_purchased,
            "total_deducted": sc.total_deducted,
            "remaining_hours": sc.remaining_hours,
            "remaining_amount": sc.remaining_amount,
            "status": sc.status
        },
        action='refunded'
    )
    db.add(archive)

    orders = db.query(Order).filter(
        Order.student_id == data.student_id,
        Order.course_id == data.course_id,
        Order.is_active == True,
        Order.is_invalid == False
    ).all()
    for order in orders:
        order.is_active = False

    sc.status = 'refunded'
    sc.class_id = None
    sc.remaining_hours = 0
    sc.remaining_amount = 0.0
    sc.remaining_gift = 0

    db.commit()
    return {"code": 0, "message": "退费成功"}