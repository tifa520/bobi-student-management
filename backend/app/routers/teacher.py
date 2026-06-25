from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Teacher, Class

router = APIRouter()


@router.get("/teachers")
def teacher_list(db: Session = Depends(get_db)):
    teachers = db.query(Teacher).order_by(Teacher.created_at.desc()).all()
    result = [{"id": t.id, "name": t.name, "phone": t.phone, "role": t.role, "is_enabled": t.is_enabled} for t in teachers]
    return {"code": 0, "data": result}


@router.post("/teachers")
def create_teacher(name: str = Query(...), phone: str = Query(...), role: str = Query('full_time_teacher'), db: Session = Depends(get_db)):
    if db.query(Teacher).filter(Teacher.phone == phone).first():
        raise HTTPException(400, "手机号已存在")
    t = Teacher(name=name, phone=phone, role=role, is_enabled=True)
    db.add(t); db.commit(); db.refresh(t)
    return {"code": 0, "data": {"id": t.id}}


@router.put("/teachers/{teacher_id}")
def update_teacher(teacher_id: int, name: str = Query(...), phone: str = Query(...), role: str = Query(...), db: Session = Depends(get_db)):
    t = db.query(Teacher).get(teacher_id)
    if not t:
        raise HTTPException(404, "教师不存在")
    if db.query(Teacher).filter(Teacher.phone == phone, Teacher.id != teacher_id).first():
        raise HTTPException(400, "手机号已存在")
    t.name = name; t.phone = phone; t.role = role
    db.commit()
    return {"code": 0, "message": "更新成功"}


@router.put("/teachers/{teacher_id}/status")
def update_teacher_status(teacher_id: int, enabled: bool = Query(...), db: Session = Depends(get_db)):
    teacher = db.query(Teacher).get(teacher_id)
    if not teacher:
        raise HTTPException(404, "教师不存在")
    teacher.is_enabled = enabled
    db.commit()
    return {"code": 0, "message": "状态已更新"}


@router.delete("/teachers/{teacher_id}")
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    t = db.query(Teacher).get(teacher_id)
    if not t:
        raise HTTPException(404, "教师不存在")
    if db.query(Class).filter(Class.teacher_id == teacher_id).count() > 0:
        raise HTTPException(400, "该老师正在带班，无法删除")
    db.delete(t); db.commit()
    return {"code": 0, "message": "已删除"}


@router.get("/teachers/enabled")
def enabled_teachers(db: Session = Depends(get_db)):
    teachers = db.query(Teacher).filter(Teacher.is_enabled == True).order_by(Teacher.name).all()
    result = [{"id": t.id, "name": t.name} for t in teachers]
    return {"code": 0, "data": result}