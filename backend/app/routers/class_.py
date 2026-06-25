# backend/app/routers/class_.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from typing import Optional
from datetime import date, datetime, timedelta
from app.database import get_db
from app.models import (
    Class, Course, Teacher, Classroom, StudentCourse, Schedule,
    Attendance, Student, Order, LearningCard, Stage
)
from app.schemas import ClassCreate, ClassUpdate
from app.services.image_service import ImageService

router = APIRouter()


@router.get("/classes")
def get_class_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    teacher_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    course_name: Optional[str] = Query(None),
    teacher_name: Optional[str] = Query(None),
    sort_field: Optional[str] = Query(None),
    sort_order: Optional[str] = Query('asc'),
    db: Session = Depends(get_db)
):
    query = db.query(Class).outerjoin(Course, Class.course_id == Course.id).outerjoin(
        Teacher, Class.teacher_id == Teacher.id
    ).outerjoin(Classroom, Class.classroom_id == Classroom.id)

    if search:
        query = query.filter(Class.name.contains(search))
    if teacher_id:
        query = query.filter(Class.teacher_id == teacher_id)
    if status:
        query = query.filter(Class.status == status)
    if course_name:
        query = query.filter(Course.name == course_name)
    if teacher_name:
        query = query.filter(Teacher.name == teacher_name)

    if sort_field:
        order_col = None
        if sort_field == 'course_name':
            order_col = Course.name
        elif sort_field == 'teacher_name':
            order_col = Teacher.name
        elif hasattr(Class, sort_field):
            order_col = getattr(Class, sort_field)
        if order_col:
            query = query.order_by(order_col.asc() if sort_order == 'asc' else order_col.desc())
    else:
        query = query.order_by(Class.created_at.desc())

    total = query.count()
    classes = query.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    today = date.today()
    for cls in classes:
        student_count = db.query(StudentCourse).filter(
            StudentCourse.class_id == cls.id,
            StudentCourse.status == 'active'
        ).count()
        next_session = db.query(Schedule).filter(
            Schedule.class_id == cls.id,
            Schedule.course_date >= today,
            Schedule.status != 'cancelled'
        ).order_by(Schedule.course_date.asc(), Schedule.start_time.asc()).first()
        next_session_time = None
        if next_session:
            next_session_time = datetime.combine(
                next_session.course_date,
                datetime.strptime(next_session.start_time, "%H:%M").time()
            ).isoformat()

        # ★ 获取课阶名称
        stage_name = cls.stage.name if cls.stage else ''

        result.append({
            "id": cls.id,
            "course_id": cls.course_id,
            "name": cls.name,
            "course_name": cls.course.name if cls.course else '',
            "stage_id": cls.stage_id,                      # ★ 新增
            "stage_name": stage_name,                      # ★ 新增
            "teacher_name": cls.teacher.name if cls.teacher else '',
            "classroom_name": cls.classroom.name if cls.classroom else '',
            "status": cls.status,
            "student_count": student_count,
            "next_session_time": next_session_time,
            "duration": cls.duration,
            "deduct_hours": cls.deduct_hours,
            "unit_price": cls.unit_price,
            "start_date": str(cls.start_date) if cls.start_date else None,
            "remark": cls.remark
        })
    return {"code": 0, "data": {"items": result, "total": total}}


@router.post("/classes")
def create_class(data: ClassCreate, db: Session = Depends(get_db)):
    # 检查唯一性
    existing = db.query(Class).filter(
        Class.course_id == data.course_id,
        Class.name == data.name
    ).first()
    if existing:
        raise HTTPException(400, "该课程下班级名称已存在")

    course = db.query(Course).get(data.course_id)
    if not course:
        raise HTTPException(404, "课程不存在")

    # ★ 验证课阶属于该课程
    if data.stage_id:
        stage = db.query(Stage).filter(
            Stage.id == data.stage_id,
            Stage.course_id == data.course_id
        ).first()
        if not stage:
            raise HTTPException(400, "课阶不存在或不属于该课程")
    else:
        # 如果未指定课阶，自动选择该课程的默认课阶（第一个）
        default_stage = db.query(Stage).filter(
            Stage.course_id == data.course_id,
            Stage.is_active == True
        ).order_by(Stage.sort_order.asc()).first()
        if default_stage:
            data.stage_id = default_stage.id

    if data.teacher_id:
        teacher = db.query(Teacher).get(data.teacher_id)
        if not teacher:
            raise HTTPException(404, "教师不存在")
    if data.classroom_id:
        classroom = db.query(Classroom).get(data.classroom_id)
        if not classroom:
            raise HTTPException(404, "教室不存在")

    start_date = None
    if data.start_date:
        try:
            start_date = datetime.strptime(data.start_date, "%Y-%m-%d").date()
        except:
            pass

    new_class = Class(
        name=data.name,
        course_id=data.course_id,
        stage_id=data.stage_id,
        teacher_id=data.teacher_id,
        classroom_id=data.classroom_id,
        duration=data.duration if data.duration is not None else course.duration,
        deduct_hours=data.deduct_hours if data.deduct_hours is not None else course.deduct_hours,
        unit_price=data.unit_price,  # ★ 可空，空则继承课阶
        start_date=start_date,
        remark=data.remark or '',
        status='active'
    )
    db.add(new_class)
    db.commit()
    db.refresh(new_class)
    return {"code": 0, "data": {"id": new_class.id}}


@router.get("/classes/{class_id}")
def get_class_detail(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(Class).options(
        joinedload(Class.course),
        joinedload(Class.teacher),
        joinedload(Class.classroom),
        joinedload(Class.stage)  # ★ 新增
    ).get(class_id)
    if not cls:
        raise HTTPException(404, "班级不存在")

    student_count = db.query(StudentCourse).filter(
        StudentCourse.class_id == class_id,
        StudentCourse.status == 'active'
    ).count()

    return {"code": 0, "data": {
        "id": cls.id,
        "name": cls.name,
        "course_id": cls.course_id,
        "course_name": cls.course.name if cls.course else '',
        "stage_id": cls.stage_id,                  # ★ 新增
        "stage_name": cls.stage.name if cls.stage else '',  # ★ 新增
        "teacher_id": cls.teacher_id,
        "teacher_name": cls.teacher.name if cls.teacher else '',
        "classroom_id": cls.classroom_id,
        "classroom_name": cls.classroom.name if cls.classroom else '',
        "duration": cls.duration,
        "deduct_hours": cls.deduct_hours,
        "unit_price": cls.unit_price,
        "start_date": str(cls.start_date) if cls.start_date else None,
        "remark": cls.remark,
        "student_count": student_count,
        "status": cls.status
    }}


@router.get("/classes/by-course/{course_id}")
def get_classes_by_course(
    course_id: int,
    stage_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """获取课程下的班级，可按课阶筛选"""
    query = db.query(Class).filter(
        Class.course_id == course_id,
        Class.status == 'active'
    )
    if stage_id:
        query = query.filter(Class.stage_id == stage_id)

    classes = query.order_by(Class.name).all()
    return {"code": 0, "data": [{"id": c.id, "name": c.name, "stage_id": c.stage_id} for c in classes]}


@router.put("/classes/{class_id}")
def update_class(class_id: int, data: ClassUpdate, db: Session = Depends(get_db)):
    cls = db.query(Class).get(class_id)
    if not cls:
        raise HTTPException(404, "班级不存在")

    if data.name and data.name != cls.name:
        dup = db.query(Class).filter(
            Class.course_id == (data.course_id or cls.course_id),
            Class.name == data.name,
            Class.id != class_id
        ).first()
        if dup:
            raise HTTPException(400, "该课程下班级名称已存在")

    # ★ 验证课阶属于该课程
    stage_id = data.stage_id if data.stage_id is not None else cls.stage_id
    if stage_id:
        stage = db.query(Stage).filter(
            Stage.id == stage_id,
            Stage.course_id == (data.course_id or cls.course_id)
        ).first()
        if not stage:
            raise HTTPException(400, "课阶不存在或不属于该课程")

    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == 'start_date' and value:
            value = datetime.strptime(value, "%Y-%m-%d").date()
        setattr(cls, field, value)

    db.commit()
    return {"code": 0, "message": "更新成功"}


@router.delete("/classes/{class_id}")
def delete_class(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(Class).get(class_id)
    if not cls:
        raise HTTPException(404, "班级不存在")
    if db.query(StudentCourse).filter(
        StudentCourse.class_id == class_id,
        StudentCourse.status == 'active'
    ).count():
        raise HTTPException(400, "该班级仍有在读学员，无法删除")
    db.delete(cls)
    db.commit()
    return {"code": 0, "message": "已删除"}


@router.post("/classes/{class_id}/close")
def close_class(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(Class).get(class_id)
    if not cls:
        raise HTTPException(404, "班级不存在")
    cls.status = 'closed'
    db.commit()
    return {"code": 0, "message": "班级已结课"}


@router.get("/classes/{class_id}/students")
def get_class_students(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(Class).get(class_id)
    if not cls:
        raise HTTPException(404, "班级不存在")

    student_courses = db.query(StudentCourse).filter(
        StudentCourse.class_id == class_id,
        StudentCourse.status == 'active'
    ).all()

    result = []
    for sc in student_courses:
        student = db.query(Student).get(sc.student_id)
        if not student:
            continue

        card = db.query(LearningCard).filter(
            LearningCard.student_id == student.id,
            LearningCard.course_id == cls.course_id,
            LearningCard.status == 'active'
        ).first()

        remaining_hours = 0
        remaining_amount = 0.0
        validity_date = None
        if card:
            remaining_hours = card.remaining_paid_hours or 0
            remaining_amount = card.remaining_amount or 0.0
            if card.validity_end_date:
                validity_date = card.validity_end_date.strftime('%Y-%m-%d')

        orders = db.query(Order).filter(
            Order.student_id == student.id,
            Order.course_id == cls.course_id,
            Order.is_active == True,
            Order.is_invalid == False
        ).all()

        total_leaves = 0
        unlimited = False
        for o in orders:
            if o.leave_limit == '不限制':
                unlimited = True
                break
            elif o.leave_limit == '限制次数':
                total_leaves += (o.leave_limit_count or 0)

        used_leaves = db.query(Attendance).join(
            Class, Attendance.class_id == Class.id
        ).filter(
            Attendance.student_id == student.id,
            Class.course_id == cls.course_id,
            Attendance.status == '请假'
        ).count()

        if unlimited:
            total_leaves_display = "不限"
        else:
            total_leaves_display = total_leaves

        result.append({
            "student_id": student.id,
            "name": student.name,
            "phone": student.phone,
            "avatar": ImageService.get_url(student.avatar),
            "birthday": str(student.birthday) if student.birthday else None,
            "remaining_hours": remaining_hours,
            "remaining_amount": remaining_amount,
            "validity_date": validity_date,
            "used_leaves": used_leaves,
            "total_leaves": total_leaves_display
        })

    return {"code": 0, "data": result}


@router.get("/classes/{class_id}/schedules")
def get_class_schedules(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(Class).get(class_id)
    if not cls:
        raise HTTPException(404, "班级不存在")

    today = date.today()
    all_schedules = db.query(Schedule).filter(
        Schedule.class_id == class_id
    ).order_by(Schedule.course_date.asc()).all()

    upcoming = []
    history = []
    for s in all_schedules:
        teacher = db.query(Teacher).get(s.teacher_id)
        classroom = db.query(Classroom).get(s.classroom_id)
        start_dt = datetime.strptime(s.start_time, "%H:%M")
        end_dt = start_dt + timedelta(minutes=s.duration)
        end_time = end_dt.strftime("%H:%M")

        item = {
            "schedule_id": s.id,
            "course_date": s.course_date.isoformat(),
            "start_time": s.start_time,
            "end_time": end_time,
            "duration": s.duration,
            "teacher_name": teacher.name if teacher else '',
            "classroom_name": classroom.name if classroom else '',
            "teacher_id": s.teacher_id,
            "classroom_id": s.classroom_id,
            "status": s.status
        }

        if s.course_date >= today and s.status != 'cancelled':
            upcoming.append(item)
        else:
            total_students = db.query(StudentCourse).filter(
                StudentCourse.class_id == class_id,
                StudentCourse.status == 'active'
            ).count()
            attended = db.query(Attendance).filter(
                Attendance.schedule_id == s.id,
                Attendance.status.in_(['出勤', '迟到'])
            ).count()
            attendance_rate = round(attended / total_students * 100) if total_students > 0 else 0
            item["student_count"] = total_students
            item["attended_count"] = attended
            item["attendance_rate"] = attendance_rate
            history.append(item)

    return {"code": 0, "data": {"upcoming": upcoming, "history": history}}


@router.get("/classes/{class_id}/attendance")
def get_class_attendance(
    class_id: int,
    month: str = Query(..., regex=r'^\d{4}-\d{2}$'),
    db: Session = Depends(get_db)
):
    cls = db.query(Class).get(class_id)
    if not cls:
        raise HTTPException(404, "班级不存在")

    year, mon = map(int, month.split('-'))
    start_date = date(year, mon, 1)
    if mon == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, mon + 1, 1)

    student_courses = db.query(StudentCourse).filter(
        StudentCourse.class_id == class_id,
        StudentCourse.status == 'active'
    ).all()

    students = []
    for sc in student_courses:
        student = db.query(Student).get(sc.student_id)
        if student:
            students.append({
                "student_id": student.id,
                "name": student.name,
                "phone": student.phone,
                "avatar": ImageService.get_url(student.avatar)
            })

    schedules = db.query(Schedule).filter(
        Schedule.class_id == class_id,
        Schedule.course_date >= start_date,
        Schedule.course_date < end_date,
        Schedule.status != 'cancelled'
    ).order_by(Schedule.course_date).all()

    result = []
    for student in students:
        row = {
            "student_id": student["student_id"],
            "name": student["name"],
            "phone": student["phone"],
            "avatar": student["avatar"],
            "attendance": {}
        }
        for s in schedules:
            att = db.query(Attendance).filter(
                Attendance.schedule_id == s.id,
                Attendance.student_id == student["student_id"]
            ).first()
            status = att.status if att else '缺勤'
            row["attendance"][s.course_date.isoformat()] = status
        result.append(row)

    return {"code": 0, "data": result}


@router.post("/classes/{class_id}/schedules")
def create_schedules(
    class_id: int,
    dates: str = Query(...),
    start_time: str = Query(...),
    duration: int = Query(...),
    teacher_id: Optional[int] = Query(None),
    classroom_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    date_list = [d.strip() for d in dates.split(',') if d.strip()]
    if not date_list:
        raise HTTPException(400, "请提供至少一个日期")

    class_obj = db.query(Class).get(class_id)
    if not class_obj:
        raise HTTPException(404, "班级不存在")

    created = 0
    conflicts = []
    for date_str in date_list:
        try:
            course_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            continue

        if classroom_id:
            existing = db.query(Schedule).filter(
                Schedule.classroom_id == classroom_id,
                Schedule.course_date == course_date,
                Schedule.start_time == start_time,
                Schedule.status != 'cancelled'
            ).first()
            if existing:
                conflicts.append(f"{course_date} {start_time} 教室已被占用")
                continue

        existing_schedule = db.query(Schedule).filter(
            Schedule.class_id == class_id,
            Schedule.course_date == course_date
        ).first()
        if existing_schedule:
            continue

        schedule = Schedule(
            class_id=class_id,
            teacher_id=teacher_id,
            classroom_id=classroom_id,
            course_date=course_date,
            start_time=start_time,
            duration=duration,
            status='scheduled'
        )
        db.add(schedule)
        created += 1

    if conflicts:
        raise HTTPException(400, f"排课冲突: {'; '.join(conflicts)}")
    db.commit()
    return {"code": 0, "message": f"成功创建 {created} 条排课"}


@router.put("/schedules/{schedule_id}")
def update_schedule(
    schedule_id: int,
    course_date: str = Query(...),
    start_time: str = Query(...),
    duration: int = Query(...),
    teacher_id: Optional[int] = Query(None),
    classroom_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    schedule = db.query(Schedule).get(schedule_id)
    if not schedule:
        raise HTTPException(404, "排课不存在")

    try:
        new_date = datetime.strptime(course_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(400, "日期格式错误")

    if classroom_id:
        existing = db.query(Schedule).filter(
            Schedule.classroom_id == classroom_id,
            Schedule.course_date == new_date,
            Schedule.start_time == start_time,
            Schedule.id != schedule_id,
            Schedule.status != 'cancelled'
        ).first()
        if existing:
            raise HTTPException(400, "该时间段教室已被占用")

    schedule.course_date = new_date
    schedule.start_time = start_time
    schedule.duration = duration
    schedule.teacher_id = teacher_id
    schedule.classroom_id = classroom_id
    db.commit()
    return {"code": 0, "message": "更新成功"}


@router.delete("/schedules/{schedule_id}")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(Schedule).get(schedule_id)
    if not schedule:
        raise HTTPException(404, "排课不存在")
    db.delete(schedule)
    db.commit()
    return {"code": 0, "message": "删除成功"}