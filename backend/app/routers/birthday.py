from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract
from app.database import get_db
from app.models import Student
from app.services.image_service import ImageService

router = APIRouter()

@router.get("/students/birthdays")
def get_birthdays_by_month(
    year: int = Query(...),
    month: int = Query(...),
    db: Session = Depends(get_db)
):
    students = db.query(Student).filter(
        extract('month', Student.birthday) == month,
        Student.is_archived == False,
        Student.birthday.isnot(None)
    ).all()
    
    result = {}
    for s in students:
        day = s.birthday.day
        date_str = f"{year}-{month:02d}-{day:02d}"
        if date_str not in result:
            result[date_str] = []
        result[date_str].append({
            "id": s.id,
            "name": s.name,
            "avatar": ImageService.get_url(s.avatar)
        })
    return {"code": 0, "data": result}
