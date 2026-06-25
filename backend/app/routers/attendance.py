from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from app.database import get_db
from app.models import (
    Class, Schedule, Student, Attendance, Order, Course, Teacher, Classroom,
    LearningCard, CardTransaction
)
from app.schemas import AttendanceSubmit, TransferClassRequest
from app.services.transaction_service import TransactionService
from app.utils import deduct_from_orders_with_detail
from app.services.image_service import ImageService

router = APIRouter(prefix="/attendance")


@router.get("/classes")
def get_attendance_classes(
    course_date: str = Query(...),
    db: Session = Depends(get_db)
):
    target_date = datetime.strptime(course_date, "%Y-%m-%d").date()
    schedules = db.query(Schedule).filter(
        Schedule.course_date == target_date,
        Schedule.status != 'cancelled'
    ).order_by(Schedule.start_time).all()

    result = []
    for schedule in schedules:
        class_ = db.query(Class).get(schedule.class_id)
        course = db.query(Course).get(class_.course_id) if class_ else None
        teacher = db.query(Teacher).get(schedule.teacher_id) if schedule.teacher_id else (class_.teacher if class_ else None)
        classroom = db.query(Classroom).get(schedule.classroom_id) if schedule.classroom_id else (class_.classroom if class_ else None)
        total_students = db.query(LearningCard).filter(
            LearningCard.class_id == schedule.class_id,
            LearningCard.status == 'active'
        ).count()
        attended = db.query(Attendance).filter(
            Attendance.schedule_id == schedule.id,
            Attendance.status.in_(['出勤', '迟到', '请假', '未到', '换班'])
        ).count()
        result.append({
            "schedule_id": schedule.id,
            "class_id": class_.id if class_ else None,
            "class_name": class_.name if class_ else '',
            "course_name": course.name if course else '',
            "start_time": schedule.start_time,
            "duration": schedule.duration,
            "teacher_name": teacher.name if teacher else '',
            "classroom_name": classroom.name if classroom else '',
            "total_students": total_students,
            "attended": attended,
            "status": schedule.status
        })
    return {"code": 0, "data": result}


@router.get("/month-status")
def get_month_status(
    year: int = Query(...),
    month: int = Query(...),
    db: Session = Depends(get_db)
):
    from datetime import date, timedelta
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    schedules = db.query(Schedule).filter(
        Schedule.course_date >= first_day,
        Schedule.course_date <= last_day,
        Schedule.status != 'cancelled'
    ).all()
    date_status = {}
    for schedule in schedules:
        date_str = schedule.course_date.isoformat()
        if date_str not in date_status:
            date_status[date_str] = {'total': 0, 'completed': 0}
        date_status[date_str]['total'] += 1
        if schedule.status == 'completed':
            date_status[date_str]['completed'] += 1
    result = {}
    for date_str, stats in date_status.items():
        if stats['completed'] == stats['total']:
            result[date_str] = 'completed'
        else:
            result[date_str] = 'scheduled'
    return {"code": 0, "data": result}


@router.get("/students")
def get_class_students(
    schedule_id: int = Query(...),
    db: Session = Depends(get_db)
):
    schedule = db.query(Schedule).get(schedule_id)
    if not schedule:
        raise HTTPException(404, "排课不存在")
    class_id = schedule.class_id
    target_date = schedule.course_date

    class_obj = db.query(Class).get(class_id)
    deduct_hours_per_class = class_obj.deduct_hours if class_obj else 1

    # 查询班级下所有活跃卡片（不在此处过滤停课，后续用 Python 过滤）
    all_cards = db.query(LearningCard).filter(
        LearningCard.class_id == class_id,
        LearningCard.status == 'active'
    ).all()
    
    # 停课过滤：如果当前上课日期在停课期间内，则排除该学员
    cards = []
    for card in all_cards:
        if card.suspended_start and card.suspended_end:
            if card.suspended_start <= target_date <= card.suspended_end:
                continue
        cards.append(card)

    result = []
    for card in cards:
        student = db.query(Student).get(card.student_id)
        if not student:
            continue
        att = db.query(Attendance).filter(
            Attendance.schedule_id == schedule_id,
            Attendance.student_id == student.id
        ).first()

        total_leave = card.total_leave_quota
        used_leave = card.used_leave
        if total_leave == 0:
            leave_display = '不允许'
            remaining_leaves = 0
        else:
            leave_display = f"{used_leave}/{total_leave}"
            remaining_leaves = total_leave - used_leave

        result.append({
            "student_id": student.id,
            "name": student.name,
            "phone": student.phone,
            "avatar": ImageService.get_url(student.avatar),
            "remaining_hours": card.remaining_paid_hours,
            "remaining_gift": card.remaining_gift_hours,
            "total_gift": getattr(card, 'total_gift_hours', 0),
            "deduct_hours": deduct_hours_per_class,
            "status": att.status if att else '未考勤',
            "attendance_id": att.id if att else None,
            "is_temporary": False,
            "leave_display": leave_display,
            "remaining_leaves": remaining_leaves,
            "total_leave_quota": total_leave,
            "used_leave": used_leave,
            "gift_deduct": att.gift_deduct if att else 0,
            "purchased_deduct": att.purchased_deduct if att else 0,
            "deduct_amount": att.deduct_amount if att else 0,
        })

    # 临时插班学员（不在此处过滤停课，临时插班学员可能没有 learning_card）
    temps = db.query(Attendance).filter(
        Attendance.schedule_id == schedule_id,
        Attendance.enrollment_id == None,
        Attendance.status == '未考勤'
    ).all()
    for att in temps:
        student = db.query(Student).get(att.student_id)
        if not student:
            continue
        card = db.query(LearningCard).filter(
            LearningCard.student_id == student.id,
            LearningCard.course_id == class_obj.course_id
        ).first()
        if card:
            remaining_paid = card.remaining_paid_hours
            remaining_gift = card.remaining_gift_hours
        else:
            remaining_paid = 0
            remaining_gift = 0
        result.append({
            "student_id": student.id,
            "name": student.name,
            "phone": student.phone,
            "avatar": ImageService.get_url(student.avatar),
            "remaining_hours": remaining_paid,
            "remaining_gift": remaining_gift,
            "total_gift": getattr(card, 'total_gift_hours', 0) if card else 0,
            "deduct_hours": deduct_hours_per_class,
            "status": att.status,
            "attendance_id": att.id,
            "is_temporary": True,
            "leave_display": "-",
            "remaining_leaves": 0,
            "total_leave_quota": 0,
            "used_leave": 0,
            "gift_deduct": att.gift_deduct,
            "purchased_deduct": att.purchased_deduct,
            "deduct_amount": att.deduct_amount,
        })
    return {"code": 0, "data": result}


@router.post("/submit")
def submit_attendance(data: AttendanceSubmit, db: Session = Depends(get_db)):
    schedule = db.query(Schedule).get(data.schedule_id)
    if not schedule:
        raise HTTPException(400, "排课不存在")
    class_ = db.query(Class).get(schedule.class_id)
    if not class_:
        raise HTTPException(400, "班级不存在")
    teacher_id = class_.teacher_id
    tx_service = TransactionService(db)

    try:
        db.begin_nested()
        for item in data.attendance_list:
            student_id = item['student_id']
            status = item['status']
            deduct_hours = item.get('deduct_hours', 0)
            leave_deduct = item.get('leave_deduct', 0)
            hour_type = item.get('hour_type', '付费')
            remark = item.get('remark', '')

            deduct_amount = 0.0
            if status in ['出勤', '迟到'] and deduct_hours > 0:
                if hour_type == '付费':
                    _, paid, amount = deduct_from_orders_with_detail(
                        db, student_id, class_.course_id, deduct_hours, deduct_gift=False
                    )
                    deduct_amount = amount
                    paid_deduct = paid
                    gift_deduct = 0
                else:
                    deduct_amount = 0.0
                    paid_deduct = 0
                    gift_deduct = deduct_hours
            else:
                paid_deduct = 0
                gift_deduct = 0

            att = Attendance(
                student_id=student_id,
                class_id=schedule.class_id,
                schedule_id=data.schedule_id,
                status=status,
                deduct_hours=deduct_hours,
                deduct_amount=deduct_amount,
                gift_deduct=gift_deduct,
                purchased_deduct=paid_deduct,
                teacher_id=teacher_id,
                class_name=class_.name,
                remark=remark
            )
            db.add(att)
            db.flush()

            tx_service.record_attendance(att, paid_deduct, gift_deduct, leave_deduct)

        schedule.status = 'completed'
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"考勤提交失败: {str(e)}")
    return {"code": 0, "message": "考勤提交成功"}


@router.get("/other-classes")
def get_other_classes(
    class_id: int = Query(...),
    db: Session = Depends(get_db)
):
    class_ = db.query(Class).get(class_id)
    if not class_:
        return {"code": 0, "data": []}
    others = db.query(Class).filter(
        Class.course_id == class_.course_id,
        Class.id != class_id,
        Class.status == 'active'
    ).all()
    result = [{"id": c.id, "name": c.name} for c in others]
    return {"code": 0, "data": result}


@router.get("/upcoming-schedules")
def upcoming_schedules(
    class_id: int = Query(...),
    db: Session = Depends(get_db)
):
    today = date.today()
    schedules = db.query(Schedule).filter(
        Schedule.class_id == class_id,
        Schedule.course_date >= today,
        Schedule.status == 'scheduled'
    ).order_by(Schedule.course_date, Schedule.start_time).limit(20).all()
    result = [{
        "id": s.id,
        "course_date": str(s.course_date),
        "start_time": s.start_time,
        "duration": s.duration
    } for s in schedules]
    return {"code": 0, "data": result}


@router.post("/transfer")
def transfer_class_student(data: TransferClassRequest, db: Session = Depends(get_db)):
    from_schedule = db.query(Schedule).get(data.from_schedule_id)
    from_class = db.query(Class).get(from_schedule.class_id) if from_schedule else None
    from_class_name = from_class.name if from_class else None

    existing = db.query(Attendance).filter(
        Attendance.schedule_id == data.from_schedule_id,
        Attendance.student_id == data.student_id
    ).first()
    if existing:
        existing.status = '换班'
        existing.deduct_hours = 0
        if not existing.class_name and from_class_name:
            existing.class_name = from_class_name
    else:
        att = Attendance(
            student_id=data.student_id,
            class_id=from_schedule.class_id if from_schedule else None,
            class_name=from_class_name,
            schedule_id=data.from_schedule_id,
            status='换班',
            deduct_hours=0
        )
        db.add(att)

    to_class = db.query(Class).get(data.to_class_id)
    to_class_name = to_class.name if to_class else None

    target_att = Attendance(
        student_id=data.student_id,
        class_id=data.to_class_id,
        class_name=to_class_name,
        schedule_id=data.to_schedule_id,
        status='未考勤',
        deduct_hours=0,
        enrollment_id=None
    )
    db.add(target_att)
    db.commit()
    return {"code": 0, "message": "临时转班成功"}


@router.get("/unattended")
def get_unattended_schedules(db: Session = Depends(get_db)):
    today = date.today()
    schedules = db.query(Schedule).filter(
        Schedule.course_date <= today,
        Schedule.status != 'completed'
    ).order_by(Schedule.course_date.asc(), Schedule.start_time.asc()).all()
    result = []
    current_date = None
    group = None
    for s in schedules:
        class_ = db.query(Class).get(s.class_id)
        if not class_:
            continue
        course = db.query(Course).get(class_.course_id)
        teacher = db.query(Teacher).get(s.teacher_id) if s.teacher_id else class_.teacher
        classroom = db.query(Classroom).get(s.classroom_id) if s.classroom_id else class_.classroom
        item = {
            "schedule_id": s.id,
            "course_date": s.course_date.isoformat(),
            "start_time": s.start_time,
            "class_name": class_.name,
            "course_name": course.name if course else '',
            "teacher_name": teacher.name if teacher else '',
            "classroom_name": classroom.name if classroom else '',
            "duration": s.duration,
            "status": s.status
        }
        date_str = s.course_date.isoformat()
        if date_str != current_date:
            if group:
                result.append(group)
            group = {"date": date_str, "sessions": []}
            current_date = date_str
        group["sessions"].append(item)
    if group:
        result.append(group)
    return {"code": 0, "data": result}


@router.post("/temporary-enroll")
def temporary_enroll(
    schedule_id: int = Query(...),
    student_id: int = Query(...),
    db: Session = Depends(get_db)
):
    schedule = db.query(Schedule).get(schedule_id)
    if not schedule:
        raise HTTPException(404, "排课不存在")
    class_ = db.query(Class).get(schedule.class_id)
    if not class_:
        raise HTTPException(404, "班级不存在")

    existing = db.query(Attendance).filter(
        Attendance.schedule_id == schedule_id,
        Attendance.student_id == student_id
    ).first()
    if existing:
        raise HTTPException(400, "该学员已在此次排课中，不能重复插班")

    tx_service = TransactionService(db)
    result = tx_service.record_temporary_enroll(
        student_id=student_id,
        course_id=class_.course_id,
        class_id=schedule.class_id,
        deduct_hours=1,
        reason="临时插班"
    )

    att = Attendance(
        student_id=student_id,
        class_id=schedule.class_id,
        class_name=class_.name,
        schedule_id=schedule_id,
        status='出勤',
        deduct_hours=1,
        deduct_amount=result["amount"],
        gift_deduct=result["gift"],
        purchased_deduct=result["paid"],
        teacher_id=class_.teacher_id,
        remark="临时插班"
    )
    db.add(att)
    db.commit()

    return {"code": 0, "message": "临时插班成功"}


@router.put("/record/{attendance_id}")
def update_attendance_record(
    attendance_id: int,
    status: str = Query(...),
    deduct_hours: int = Query(...),
    hour_type: str = Query(...),
    db: Session = Depends(get_db)
):
    old_att = db.query(Attendance).get(attendance_id)
    if not old_att:
        raise HTTPException(404, "考勤记录不存在")

    schedule = db.query(Schedule).get(old_att.schedule_id)
    if not schedule:
        raise HTTPException(404, "排课不存在")
    class_ = db.query(Class).get(schedule.class_id)
    if not class_:
        raise HTTPException(404, "班级不存在")

    student_id = old_att.student_id
    course_id = class_.course_id

    paid_deduct = 0
    gift_deduct = 0
    deduct_amount = 0.0
    leave_deduct = 1 if status in ['请假', '未到'] else 0

    if status in ['出勤', '迟到'] and deduct_hours > 0:
        if hour_type == '付费':
            from app.utils import deduct_from_orders_with_detail
            gift, paid, amount = deduct_from_orders_with_detail(
                db, student_id, course_id, deduct_hours, deduct_gift=False
            )
            paid_deduct = paid
            gift_deduct = gift
            deduct_amount = amount
        else:
            paid_deduct = 0
            gift_deduct = deduct_hours
            deduct_amount = 0.0

    tx_service = TransactionService(db)

    try:
        old_txns = db.query(CardTransaction).filter(CardTransaction.attendance_id == attendance_id).all()
        for txn in old_txns:
            db.delete(txn)
        db.delete(old_att)
        db.flush()

        new_att = Attendance(
            student_id=student_id,
            class_id=schedule.class_id,
            class_name=class_.name,
            schedule_id=schedule.id,
            status=status,
            deduct_hours=deduct_hours,
            deduct_amount=deduct_amount,
            gift_deduct=gift_deduct,
            purchased_deduct=paid_deduct,
            teacher_id=class_.teacher_id,
            remark=old_att.remark
        )
        db.add(new_att)
        db.flush()
        tx_service.record_attendance(new_att, paid_deduct, gift_deduct, leave_deduct)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"考勤更新失败: {str(e)}")

    return {"code": 0, "message": "考勤已更新"}