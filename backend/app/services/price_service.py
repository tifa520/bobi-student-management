# backend/app/services/price_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import Class, Stage, Course


def get_class_pricing(db: Session, class_id: int) -> dict:
    """
    获取班级的实际定价，按优先级：班级自定义 > 课阶 > 课程
    返回：{ unit_price, duration, deduct_hours, source, source_id }
    """
    class_obj = db.query(Class).get(class_id)
    if not class_obj:
        raise HTTPException(404, "班级不存在")

    # 1. 优先使用班级自定义价格
    if class_obj.unit_price is not None:
        return {
            "unit_price": class_obj.unit_price,
            "duration": class_obj.duration or 60,
            "deduct_hours": class_obj.deduct_hours or 1,
            "source": "class",
            "source_id": class_obj.id
        }

    # 2. 其次使用课阶价格
    if class_obj.stage_id:
        stage = db.query(Stage).get(class_obj.stage_id)
        if stage and stage.is_active and stage.unit_price > 0:
            return {
                "unit_price": stage.unit_price,
                "duration": stage.duration or 60,
                "deduct_hours": stage.deduct_hours or 1,
                "source": "stage",
                "source_id": stage.id
            }

    # 3. 最后使用课程默认价格
    course = db.query(Course).get(class_obj.course_id)
    return {
        "unit_price": course.unit_price or 0,
        "duration": course.duration or 60,
        "deduct_hours": course.deduct_hours or 1,
        "source": "course",
        "source_id": course.id
    }


def get_stage_pricing(db: Session, stage_id: int) -> dict:
    """获取课阶的定价"""
    stage = db.query(Stage).get(stage_id)
    if not stage:
        raise HTTPException(404, "课阶不存在")
    return {
        "unit_price": stage.unit_price or 0,
        "duration": stage.duration or 60,
        "deduct_hours": stage.deduct_hours or 1,
        "source": "stage",
        "source_id": stage.id
    }