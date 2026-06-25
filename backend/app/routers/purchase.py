from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Purchase, Student
from app.schemas import PurchaseCreate

router = APIRouter()


@router.get("/records")
def purchase_list(student_id: int = Query(None), db: Session = Depends(get_db)):
    query = db.query(Purchase)
    if student_id:
        query = query.filter(Purchase.student_id == student_id)
    records = query.order_by(Purchase.created_at.desc()).all()
    result = [{"id": r.id, "student_id": r.student_id, "student_name": db.query(Student).get(r.student_id).name if r.student_id else '',
               "items": r.items, "total_amount": r.total_amount, "payment_method": r.payment_method, "created_at": str(r.created_at)} for r in records]
    return {"code": 0, "data": result}


@router.post("/create")
def create_purchase(data: PurchaseCreate, db: Session = Depends(get_db)):
    student = db.query(Student).get(data.student_id)
    if not student:
        raise HTTPException(404, "学员不存在")
    purchase = Purchase(student_id=data.student_id, items=data.items, total_amount=data.total_amount, payment_method=data.payment_method)
    db.add(purchase); db.commit(); db.refresh(purchase)
    return {"code": 0, "data": {"id": purchase.id}, "message": "购买成功"}