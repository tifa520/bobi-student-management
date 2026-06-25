from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import GiftExchange, Student
from app.schemas import GiftExchangeCreate

router = APIRouter()


@router.get("/exchanges")
def gift_list(student_id: Optional[int] = Query(None), gift_type: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(GiftExchange)
    if student_id:
        query = query.filter(GiftExchange.student_id == student_id)
    if gift_type:
        query = query.filter(GiftExchange.gift_type == gift_type)
    records = query.order_by(GiftExchange.created_at.desc()).all()
    result = [{"id": r.id, "student_id": r.student_id, "student_name": db.query(Student).get(r.student_id).name if r.student_id else '',
               "gift_type": r.gift_type, "gift_name": r.gift_name, "activity_name": r.activity_name,
               "quantity": r.quantity, "created_at": str(r.created_at)} for r in records]
    return {"code": 0, "data": result}


@router.post("/exchange")
def exchange_gift(data: GiftExchangeCreate, db: Session = Depends(get_db)):
    student = db.query(Student).get(data.student_id)
    if not student:
        raise HTTPException(404, "学员不存在")
    gift = GiftExchange(student_id=data.student_id, gift_type=data.gift_type, gift_name=data.gift_name,
                        activity_name=data.activity_name or '', quantity=data.quantity)
    db.add(gift); db.commit(); db.refresh(gift)
    return {"code": 0, "data": {"id": gift.id}, "message": "兑换成功"}