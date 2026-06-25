from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, desc
from typing import Optional, List
from datetime import date, datetime, timedelta
from pydantic import BaseModel
from app.database import get_db
from app.models import Student, StudentCourse, Class, IntegralRecord, Teacher
from app.schemas import ScoreChange
from app.services.image_service import ImageService

router = APIRouter()

# ========== 积分变动记录列表 ==========
@router.get("/records")
def get_integral_records(
    student_name: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    record_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(IntegralRecord).join(Student, IntegralRecord.student_id == Student.id)
    if student_name:
        query = query.filter(Student.name.contains(student_name))
    if start_date:
        query = query.filter(IntegralRecord.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        query = query.filter(IntegralRecord.created_at <= datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))
    if record_type == 'reward':
        query = query.filter(IntegralRecord.change_amount > 0)
    elif record_type == 'penalty':
        query = query.filter(IntegralRecord.change_amount < 0)
    total = query.count()
    records = query.order_by(IntegralRecord.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    result = []
    for r in records:
        student = db.query(Student).get(r.student_id)
        result.append({
            "id": r.id,
            "student_id": r.student_id,
            "student_name": student.name if student else '',
            "student_phone": student.phone if student else '',
            "student_avatar": ImageService.get_url(student.avatar) if student else '',   # 新增头像字段
            "change_amount": r.change_amount,
            "reason": r.reason,
            "remark": r.remark or '',
            "created_at": str(r.created_at)
        })
    return {"code": 0, "data": {"items": result, "total": total}}


# ========== 获取班级学员列表（积分管理页面使用） ==========
@router.get("/class-students")
def get_class_students(
    class_id: int = Query(...),
    db: Session = Depends(get_db)
):
    student_courses = db.query(StudentCourse).filter(
        StudentCourse.class_id == class_id,
        StudentCourse.status == 'active'
    ).all()
    result = []
    for sc in student_courses:
        student = db.query(Student).get(sc.student_id)
        if student:
            result.append({
                "student_id": student.id,
                "name": student.name,
                "phone": student.phone,
                "total_integral": student.total_integral,
                "avatar": student.avatar or ""   # 头像字段，用于积分管理页面
            })
    return {"code": 0, "data": result}


# ========== 批量提交积分变动 ==========
class BatchScoreChangeItem(BaseModel):
    student_id: int
    change_amount: int
    reason: str
    remark: Optional[str] = ""

class BatchScoreChange(BaseModel):
    items: List[BatchScoreChangeItem]

@router.post("/batch-submit")
def batch_submit_score(data: BatchScoreChange, db: Session = Depends(get_db)):
    for item in data.items:
        student = db.query(Student).get(item.student_id)
        if not student:
            continue
        student.total_integral += item.change_amount
        record = IntegralRecord(
            student_id=item.student_id,
            change_amount=item.change_amount,
            reason=item.reason,
            remark=item.remark or ''
        )
        db.add(record)
    db.commit()
    return {"code": 0, "message": "积分已更新"}


# ========== 原有接口 ==========
@router.get("/classes-with-students")
def classes_with_students(db: Session = Depends(get_db)):
    classes = db.query(Class).all()
    result = []
    for cls in classes:
        student_courses = db.query(StudentCourse).filter(StudentCourse.class_id == cls.id, StudentCourse.status == 'active').all()
        students = []
        for sc in student_courses:
            student = db.query(Student).get(sc.student_id)
            if student:
                students.append({"student_id": student.id, "name": student.name, "total_integral": student.total_integral})
        result.append({"class_id": cls.id, "class_name": cls.name, "students": students})
    return {"code": 0, "data": result}


@router.get("/student/{student_id}")
def student_score(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).get(student_id)
    if not student:
        raise HTTPException(404, "学员不存在")
    records = db.query(IntegralRecord).filter(IntegralRecord.student_id == student_id).order_by(IntegralRecord.created_at.desc()).all()
    history = [{"id": r.id, "change_amount": r.change_amount, "reason": r.reason, "remark": r.remark or '', "created_at": str(r.created_at)} for r in records]
    return {"code": 0, "data": {"student_id": student.id, "name": student.name, "total_integral": student.total_integral, "history": history}}


@router.post("/submit")
def submit_score(data: List[ScoreChange], db: Session = Depends(get_db)):
    for item in data:
        student = db.query(Student).get(item.student_id)
        if not student:
            continue
        student.total_integral += item.change_amount
        record = IntegralRecord(
            student_id=item.student_id,
            change_amount=item.change_amount,
            reason=item.reason,
            remark=getattr(item, 'remark', '')
        )
        db.add(record)
    db.commit()
    return {"code": 0, "message": "积分已更新"}


@router.get("/ranking")
def score_ranking(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    students = db.query(Student).filter(Student.is_archived == False).order_by(Student.total_integral.desc()).limit(limit).all()
    result = [{"id": s.id, "name": s.name, "total_integral": s.total_integral} for s in students]
    return {"code": 0, "data": result}