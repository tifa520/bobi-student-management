"""学员移动端门户接口"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import Student, StudentCourse, Attendance, Schedule, Class, Course, Stage, StudentWork, IntegralRecord
from app.utils import create_access_token
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError

router = APIRouter(prefix="/student-portal", tags=["学员门户"])


# ============================================================
# 认证依赖
# ============================================================
def get_current_student(request: Request, db: Session = Depends(get_db)):
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(401, "未提供认证令牌")
    token = token[7:]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(401, "令牌已过期")
    except JWTError:
        raise HTTPException(401, "令牌无效")

    student_id = payload.get("student_id")
    role = payload.get("role", "")
    if role != "student" or not student_id:
        raise HTTPException(403, "仅限学员访问")

    student = db.query(Student).get(int(student_id))
    if not student:
        raise HTTPException(401, "学员不存在")
    return student


# ============================================================
# Pydantic 模型
# ============================================================
class StudentLoginRequest(BaseModel):
    phone: str
    password: Optional[str] = ""


class LeaveSubmitRequest(BaseModel):
    schedule_ids: List[int]
    reason: Optional[str] = ""


class SwapClassRequest(BaseModel):
    schedule_id: int
    target_class_id: int
    reason: Optional[str] = ""


# ============================================================
# 辅助函数：获取学员课程分组（课程 → 课阶 → 班级）
# ============================================================
def get_student_course_groups(student_id: int, db: Session):
    """获取学员已报名课程，按 课程→课阶→班级 分组"""
    sc_list = db.query(StudentCourse).options(
        joinedload(StudentCourse.course),
        joinedload(StudentCourse.class_),
    ).filter(
        StudentCourse.student_id == student_id,
        StudentCourse.status == 'active'
    ).all()

    groups = []
    for sc in sc_list:
        course = sc.course
        class_obj = sc.class_
        stage = None
        if class_obj and class_obj.stage_id:
            stage = db.query(Stage).get(class_obj.stage_id)

        groups.append({
            "course_id": course.id if course else 0,
            "course_name": course.name if course else "",
            "stage_id": stage.id if stage else 0,
            "stage_name": stage.name if stage else "",
            "class_id": class_obj.id if class_obj else 0,
            "class_name": class_obj.name if class_obj else "",
            "remaining_hours": sc.remaining_hours or 0,
            "remaining_gift": sc.remaining_gift or 0,
            "total_deducted": sc.total_deducted or 0,
            "leave_used": sc.leave_used or 0,
            "total_purchased": sc.total_purchased or 0,
        })

    return groups


# ============================================================
# 1. 学员登录
# ============================================================
@router.post("/login")
def student_login(data: StudentLoginRequest, db: Session = Depends(get_db)):
    phone = data.phone.strip()
    if not phone or len(phone) < 6:
        raise HTTPException(400, "请输入正确的手机号")

    student = db.query(Student).filter(Student.phone == phone).first()
    if not student:
        raise HTTPException(401, "手机号未注册")

    password = data.password if data.password else phone[-6:]
    if password != phone[-6:]:
        raise HTTPException(401, "密码错误")

    access_token = create_access_token({
        "student_id": str(student.id),
        "phone": student.phone,
        "role": "student"
    })

    return {
        "code": 0,
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "student": {
                "id": student.id,
                "name": student.name,
                "phone": student.phone,
                "gender": student.gender,
                "avatar": student.avatar or "",
                "enrollment_date": str(student.enrollment_date) if student.enrollment_date else "",
            }
        }
    }


# ============================================================
# 2. 首页仪表盘（按课程-课阶-班级分组）
# ============================================================
@router.get("/dashboard")
def student_dashboard(student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    groups = get_student_course_groups(student.id, db)

    total_remaining = sum(g["remaining_hours"] for g in groups)
    total_gift = sum(g["remaining_gift"] for g in groups)
    total_deducted = sum(g["total_deducted"] for g in groups)
    total_leave = sum(g["leave_used"] for g in groups)

    return {
        "code": 0,
        "data": {
            "student": {
                "id": student.id, "name": student.name, "phone": student.phone,
                "gender": student.gender, "age": student.age,
                "avatar": student.avatar or "",
                "total_integral": student.total_integral or 0,
            },
            "stats": {
                "total_remaining": total_remaining,
                "total_gift": total_gift,
                "total_deducted": total_deducted,
                "total_leave": total_leave,
            },
            "groups": groups,
        }
    }


# ============================================================
# 3. 课程表（按课程-课阶-班级分组显示未来排课）
# ============================================================
@router.get("/timetable")
def student_timetable(student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    groups = get_student_course_groups(student.id, db)
    today = datetime.now().date()

    result = []
    for g in groups:
        if not g["class_id"]:
            continue

        schedules = db.query(Schedule).filter(
            Schedule.class_id == g["class_id"],
            Schedule.course_date >= today,
            Schedule.status == 'active'
        ).order_by(Schedule.course_date.asc(), Schedule.start_time.asc()).limit(20).all()

        schedule_list = []
        for s in schedules:
            # 检查考勤状态
            att = db.query(Attendance).filter(
                Attendance.schedule_id == s.id,
                Attendance.student_id == student.id
            ).first()
            schedule_list.append({
                "schedule_id": s.id,
                "course_date": str(s.course_date),
                "start_time": s.start_time,
                "duration": s.duration or 60,
                "attendance_status": att.status if att else None,
            })

        if schedule_list:
            result.append({
                "course_id": g["course_id"],
                "course_name": g["course_name"],
                "stage_id": g["stage_id"],
                "stage_name": g["stage_name"],
                "class_id": g["class_id"],
                "class_name": g["class_name"],
                "schedules": schedule_list,
            })

    return {"code": 0, "data": {"groups": result}}


# ============================================================
# 4. 作品列表（倒序，含图片）
# ============================================================
@router.get("/works")
def student_works(student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    works = db.query(StudentWork).filter(
        StudentWork.student_id == student.id
    ).order_by(desc(StudentWork.created_at)).all()

    result = []
    for w in works:
        result.append({
            "id": w.id,
            "name": w.name or "",
            "img_url": w.thumbnail_url or w.original_url or "",
            "original_url": w.original_url or "",
            "type": w.type or "",
            "created_at": str(w.created_at) if w.created_at else "",
        })

    return {"code": 0, "data": {"list": result, "total": len(result)}}


# ============================================================
# 5. 考勤记录（按课程-课阶-班级分组）
# ============================================================
@router.get("/attendance")
def student_attendance(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    groups = get_student_course_groups(student.id, db)

    # 收集所有 class_id
    class_ids = list(set(g["class_id"] for g in groups if g["class_id"]))
    class_map = {g["class_id"]: g for g in groups}

    result = []
    for class_id in class_ids:
        g = class_map.get(class_id, {})

        attendances = db.query(Attendance).filter(
            Attendance.student_id == student.id,
            Attendance.class_id == class_id
        ).order_by(desc(Attendance.created_at)).limit(page_size).all()

        att_list = []
        for att in attendances:
            schedule = db.query(Schedule).get(att.schedule_id) if att.schedule_id else None
            att_list.append({
                "id": att.id,
                "status": att.status,
                "deduct_hours": att.deduct_hours or 0,
                "gift_deduct": att.gift_deduct or 0,
                "course_date": str(schedule.course_date) if schedule else "",
                "start_time": schedule.start_time if schedule else "",
                "remark": att.remark or "",
                "created_at": str(att.created_at) if att.created_at else "",
            })

        if att_list:
            result.append({
                "course_id": g.get("course_id", 0),
                "course_name": g.get("course_name", ""),
                "stage_id": g.get("stage_id", 0),
                "stage_name": g.get("stage_name", ""),
                "class_id": class_id,
                "class_name": g.get("class_name", ""),
                "attendances": att_list,
            })

    return {"code": 0, "data": {"groups": result}}


# ============================================================
# 6. 积分（统计 + 记录）
# ============================================================
@router.get("/points")
def student_points(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    total = student.total_integral or 0

    query = db.query(IntegralRecord).filter(
        IntegralRecord.student_id == student.id
    ).order_by(desc(IntegralRecord.created_at))

    total_count = query.count()
    records = query.offset((page - 1) * page_size).limit(page_size).all()

    record_list = []
    for r in records:
        record_list.append({
            "id": r.id,
            "change_amount": r.change_amount,
            "reason": r.reason or "",
            "remark": r.remark or "",
            "created_at": str(r.created_at) if r.created_at else "",
        })

    return {
        "code": 0,
        "data": {
            "total_integral": total,
            "records": record_list,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
        }
    }


# ============================================================
# 7. 可请假排课列表
# ============================================================
@router.get("/schedules")
def student_schedules(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    active_courses = db.query(StudentCourse).filter(
        StudentCourse.student_id == student.id,
        StudentCourse.status == 'active'
    ).all()

    class_ids = [c.class_id for c in active_courses if c.class_id]
    if not class_ids:
        return {"code": 0, "data": {"list": [], "total": 0}}

    today = datetime.now().date()
    schedules = db.query(Schedule).filter(
        Schedule.class_id.in_(class_ids),
        Schedule.course_date >= today,
        Schedule.status == 'active'
    ).order_by(Schedule.course_date.asc(), Schedule.start_time.asc()).limit(30).all()

    result = []
    for s in schedules:
        class_info = db.query(Class).get(s.class_id)
        existing = db.query(Attendance).filter(
            Attendance.schedule_id == s.id,
            Attendance.student_id == student.id
        ).first()

        result.append({
            "schedule_id": s.id,
            "class_id": s.class_id,
            "class_name": class_info.name if class_info else "",
            "course_date": str(s.course_date),
            "start_time": s.start_time,
            "end_time": s.end_time,
            "existing_status": existing.status if existing else None,
        })

    return {"code": 0, "data": {"list": result, "total": len(result)}}


# ============================================================
# 8. 提交请假
# ============================================================
@router.post("/leave")
def submit_leave(
    data: LeaveSubmitRequest,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    if not data.schedule_ids:
        raise HTTPException(400, "请选择要请假的课程")

    for schedule_id in data.schedule_ids:
        schedule = db.query(Schedule).get(schedule_id)
        if not schedule:
            continue

        existing = db.query(Attendance).filter(
            Attendance.schedule_id == schedule_id,
            Attendance.student_id == student.id
        ).first()

        if existing:
            existing.status = '请假'
            existing.deduct_hours = 0
            existing.remark = data.reason or existing.remark
        else:
            att = Attendance(
                student_id=student.id,
                class_id=schedule.class_id,
                schedule_id=schedule_id,
                status='请假',
                deduct_hours=0,
                remark=data.reason or "",
            )
            db.add(att)

    db.commit()
    return {"code": 0, "message": "请假申请已提交"}


# ============================================================
# 9. 换班申请
# ============================================================
@router.post("/class-swap")
def submit_class_swap(
    data: SwapClassRequest,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    schedule = db.query(Schedule).get(data.schedule_id)
    if not schedule:
        raise HTTPException(400, "排课不存在")

    target_class = db.query(Class).get(data.target_class_id)
    if not target_class:
        raise HTTPException(400, "目标班级不存在")

    existing = db.query(Attendance).filter(
        Attendance.schedule_id == data.schedule_id,
        Attendance.student_id == student.id
    ).first()

    if existing:
        existing.class_id = data.target_class_id
        existing.remark = data.reason or existing.remark
    else:
        att = Attendance(
            student_id=student.id,
            class_id=data.target_class_id,
            schedule_id=data.schedule_id,
            status='已签到',
            deduct_hours=0,
            remark=data.reason or "",
        )
        db.add(att)

    db.commit()
    return {"code": 0, "message": "换班申请已提交"}


# ============================================================
# 10. 可选班级列表
# ============================================================
@router.get("/classes")
def student_classes(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    active_courses = db.query(StudentCourse).filter(
        StudentCourse.student_id == student.id,
        StudentCourse.status == 'active'
    ).all()

    result = []
    seen = set()
    for c in active_courses:
        if c.class_id and c.class_id not in seen:
            seen.add(c.class_id)
            class_info = db.query(Class).get(c.class_id)
            if class_info:
                result.append({
                    "class_id": class_info.id,
                    "class_name": class_info.name,
                })

    return {"code": 0, "data": {"list": result}}