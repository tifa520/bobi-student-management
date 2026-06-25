from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Classroom, Class

router = APIRouter()


@router.get("/classrooms")
def classroom_list(db: Session = Depends(get_db)):
    rooms = db.query(Classroom).order_by(Classroom.created_at.desc()).all()
    result = [{"id": r.id, "name": r.name, "is_enabled": r.is_enabled} for r in rooms]
    return {"code": 0, "data": result}


@router.get("/classrooms/enabled")
def enabled_classrooms(db: Session = Depends(get_db)):
    rooms = db.query(Classroom).filter(Classroom.is_enabled == True).order_by(Classroom.name).all()
    result = [{"id": r.id, "name": r.name} for r in rooms]
    return {"code": 0, "data": result}


@router.put("/classrooms/{classroom_id}/status")
def update_classroom_status(classroom_id: int, enabled: bool = Query(...), db: Session = Depends(get_db)):
    r = db.query(Classroom).get(classroom_id)
    if not r:
        raise HTTPException(404, "教室不存在")
    r.is_enabled = enabled
    db.commit()
    return {"code": 0, "message": "状态已更新"}


@router.put("/classrooms/{classroom_id}")
def update_classroom(classroom_id: int, name: str = Query(...), is_enabled: bool = Query(None), db: Session = Depends(get_db)):
    r = db.query(Classroom).get(classroom_id)
    if not r:
        raise HTTPException(404, "教室不存在")
    if db.query(Classroom).filter(Classroom.name.ilike(name), Classroom.id != classroom_id).first():
        raise HTTPException(400, "教室名称已存在")
    r.name = name
    if is_enabled is not None:
        r.is_enabled = is_enabled
    db.commit()
    return {"code": 0, "message": "更新成功"}


@router.post("/classrooms")
def create_classroom(name: str = Query(...), is_enabled: bool = Query(True), db: Session = Depends(get_db)):
    if db.query(Classroom).filter(Classroom.name.ilike(name)).first():
        raise HTTPException(400, "教室名称已存在（不区分大小写）")
    r = Classroom(name=name, is_enabled=is_enabled)
    db.add(r); db.commit(); db.refresh(r)
    return {"code": 0, "data": {"id": r.id}}


@router.delete("/classrooms/{classroom_id}")
def delete_classroom(classroom_id: int, db: Session = Depends(get_db)):
    r = db.query(Classroom).get(classroom_id)
    if not r:
        raise HTTPException(404, "教室不存在")
    if db.query(Class).filter(Class.classroom_id == classroom_id).count() > 0:
        raise HTTPException(400, "该教室已被班级使用，无法删除")
    db.delete(r); db.commit()
    return {"code": 0, "message": "已删除"}