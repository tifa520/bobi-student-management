from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import json

from app.database import get_db
from app.models import MiscFee, Student
from app.services.image_service import ImageService

router = APIRouter()

@router.get("/misc-fees")
def get_misc_fees(
    student_id: Optional[int] = Query(None),
    fee_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(MiscFee)
    if student_id:
        query = query.filter(MiscFee.student_id == student_id)
    if fee_type:
        query = query.filter(MiscFee.fee_type == fee_type)
    if status:
        query = query.filter(MiscFee.status == status)
    if start_date:
        query = query.filter(MiscFee.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        query = query.filter(MiscFee.created_at <= datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))
    total = query.count()
    fees = query.order_by(MiscFee.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    result = []
    for f in fees:
        student = db.query(Student).get(f.student_id)
        # 解析支付方式
        payment_display = f.payment_method
        if f.payment_method and f.payment_method.startswith('['):
            try:
                payments = json.loads(f.payment_method)
                parts = []
                for p in payments:
                    if p.get('type') == 'cash':
                        parts.append(f"{p.get('method', '现金')}(¥{p.get('amount', 0):.2f})")
                    elif p.get('type') == 'points':
                        parts.append(f"{p.get('method', '积分')}({p.get('points', 0)}积分)")
                if parts:
                    payment_display = ', '.join(parts)
            except:
                payment_display = f.payment_method
        result.append({
            "id": f.id,
            "student_id": f.student_id,
            "student_name": student.name if student else '',
            "student_phone": student.phone if student else '',
            "student_avatar": ImageService.get_url(student.avatar) if student else '',
            "fee_type": f.fee_type,
            "source_id": f.source_id,
            "description": f.description,
            "amount": f.amount,
            "paid_amount": f.paid_amount,
            "points_used": f.points_used,
            "status": f.status,
            "payment_method": payment_display,
            "paid_at": str(f.paid_at) if f.paid_at else '',
            "created_at": str(f.created_at)
        })
    return {"code": 0, "data": {"items": result, "total": total}}
