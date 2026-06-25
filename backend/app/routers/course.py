from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from app.database import get_db
from app.models import Course, Class, CoursePackage, Stage
from app.schemas import (
    StageCreate, StageUpdate, 
    CourseCreate, CourseUpdate,
    PackageCreate, PackageUpdate
)
from loguru import logger

router = APIRouter()


# ================================================================
# 一、课程管理
# ================================================================

@router.get("/courses")
def course_list(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取课程列表，每个课程包含其下的所有课阶"""
    query = db.query(Course).options(
        joinedload(Course.stages)
    )
    if search:
        query = query.filter(Course.name.contains(search))
    
    total = query.count()
    courses = query.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for c in courses:
        stages = c.stages or []
        result.append({
            "id": c.id,
            "name": c.name,
            "stages": [{
                "id": s.id,
                "name": s.name,
                "charge_mode": s.charge_mode or '课时',
                "unit_price": s.unit_price or 0.0,
                "duration": s.duration or 60,
                "deduct_hours": s.deduct_hours or 1,
                "is_active": s.is_active
            } for s in stages]
        })
    
    return {"code": 0, "data": {"items": result, "total": total}}


@router.get("/courses/list")
def course_list_simple(db: Session = Depends(get_db)):
    """获取课程名称和ID（用于前端下拉选择）"""
    courses = db.query(Course).order_by(Course.name).all()
    return {
        "code": 0,
        "data": [{"id": c.id, "name": c.name} for c in courses]
    }


@router.get("/courses/{course_id}")
def course_detail(course_id: int, db: Session = Depends(get_db)):
    """获取课程详情（含课阶）"""
    course = db.query(Course).options(
        joinedload(Course.stages)
    ).get(course_id)
    if not course:
        raise HTTPException(404, "课程不存在")
    
    return {
        "code": 0,
        "data": {
            "id": course.id,
            "name": course.name,
            "stages": [{
                "id": s.id,
                "name": s.name,
                "charge_mode": s.charge_mode or '课时',
                "unit_price": s.unit_price or 0.0,
                "duration": s.duration or 60,
                "deduct_hours": s.deduct_hours or 1,
                "is_active": s.is_active
            } for s in (course.stages or [])]
        }
    }


@router.post("/courses")
def create_course(data: CourseCreate, db: Session = Depends(get_db)):
    """创建课程，同时创建其下的课阶"""
    existing = db.query(Course).filter(Course.name == data.name).first()
    if existing:
        raise HTTPException(400, "课程名称已存在")
    
    # 1. 创建课程
    course = Course(
        name=data.name,
        charge_mode=None,
        duration=None,
        deduct_hours=None,
        unit_price=None
    )
    db.add(course)
    db.flush()
    
    # 2. 创建课阶
    if not data.stages:
        default_stage = Stage(
            course_id=course.id,
            name=f"{data.name} 默认课阶",
            charge_mode='课时',
            unit_price=0.0,
            duration=60,
            deduct_hours=1,
            sort_order=1,
            is_active=True
        )
        db.add(default_stage)
    else:
        for idx, stage_data in enumerate(data.stages):
            stage = Stage(
                course_id=course.id,
                name=stage_data.name,
                charge_mode=stage_data.charge_mode or '课时',
                unit_price=stage_data.unit_price or 0.0,
                duration=stage_data.duration or 60,
                deduct_hours=stage_data.deduct_hours or 1,
                sort_order=idx + 1,
                is_active=True
            )
            db.add(stage)
    
    db.commit()
    return {"code": 0, "data": {"id": course.id}, "message": "创建成功"}


@router.put("/courses/{course_id}")
def update_course(
    course_id: int,
    data: CourseUpdate,
    db: Session = Depends(get_db)
):
    """更新课程名称，并全量替换课阶列表"""
    course = db.query(Course).get(course_id)
    if not course:
        raise HTTPException(404, "课程不存在")
    
    # 1. 更新课程名称
    if data.name is not None:
        existing = db.query(Course).filter(
            Course.name == data.name,
            Course.id != course_id
        ).first()
        if existing:
            raise HTTPException(400, "课程名称已存在")
        course.name = data.name
    
    # 2. 全量替换课阶
    if data.stages is not None:
        db.query(Stage).filter(Stage.course_id == course_id).delete()
        
        for idx, stage_data in enumerate(data.stages):
            new_stage = Stage(
                course_id=course_id,
                name=stage_data.name,
                charge_mode=stage_data.charge_mode or '课时',
                unit_price=stage_data.unit_price or 0.0,
                duration=stage_data.duration or 60,
                deduct_hours=stage_data.deduct_hours or 1,
                sort_order=idx + 1,
                is_active=True
            )
            db.add(new_stage)
    
    db.commit()
    return {"code": 0, "message": "更新成功"}


@router.delete("/courses/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db)):
    """删除课程及其所有课阶"""
    course = db.query(Course).get(course_id)
    if not course:
        raise HTTPException(404, "课程不存在")
    
    class_count = db.query(Class).filter(Class.course_id == course_id).count()
    if class_count > 0:
        raise HTTPException(400, f"该课程已被 {class_count} 个班级引用，无法删除")
    
    db.query(Stage).filter(Stage.course_id == course_id).delete()
    db.delete(course)
    db.commit()
    return {"code": 0, "message": "已删除"}


# ================================================================
# 二、课阶管理
# ================================================================

@router.get("/courses/{course_id}/stages")
def get_course_stages(
    course_id: int,
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """获取指定课程下的所有课阶"""
    course = db.query(Course).get(course_id)
    if not course:
        raise HTTPException(404, "课程不存在")
    
    query = db.query(Stage).filter(Stage.course_id == course_id)
    if is_active is not None:
        query = query.filter(Stage.is_active == is_active)
    
    stages = query.order_by(Stage.sort_order.asc(), Stage.id.asc()).all()
    result = [{
        "id": s.id,
        "course_id": s.course_id,
        "name": s.name,
        "charge_mode": s.charge_mode or '课时',
        "description": s.description or '',
        "sort_order": s.sort_order,
        "is_active": s.is_active,
        "unit_price": s.unit_price or 0.0,
        "duration": s.duration or 60,
        "deduct_hours": s.deduct_hours or 1,
        "target_level": s.target_level,
        "min_age": s.min_age,
        "max_age": s.max_age,
        "created_at": s.created_at.isoformat() if s.created_at else '',
        "updated_at": s.updated_at.isoformat() if s.updated_at else '',
        "class_count": db.query(Class).filter(Class.stage_id == s.id).count(),
    } for s in stages]
    return {"code": 0, "data": result}


@router.post("/courses/{course_id}/stages")
def create_stage(
    course_id: int,
    data: StageCreate,
    db: Session = Depends(get_db)
):
    """为课程创建单个课阶"""
    course = db.query(Course).get(course_id)
    if not course:
        raise HTTPException(404, "课程不存在")
    
    existing = db.query(Stage).filter(
        Stage.course_id == course_id,
        Stage.name == data.name
    ).first()
    if existing:
        raise HTTPException(400, "该课程下已存在同名课阶")
    
    stage = Stage(
        course_id=course_id,
        name=data.name,
        charge_mode=data.charge_mode or '课时',
        description=data.description or '',
        sort_order=data.sort_order or 0,
        is_active=data.is_active,
        unit_price=data.unit_price or 0.0,
        duration=data.duration or 60,
        deduct_hours=data.deduct_hours or 1,
        target_level=data.target_level,
        min_age=data.min_age,
        max_age=data.max_age
    )
    db.add(stage)
    db.commit()
    db.refresh(stage)
    return {"code": 0, "data": {"id": stage.id}, "message": "课阶创建成功"}


@router.put("/courses/{course_id}/stages/{stage_id}")
def update_stage(
    course_id: int,
    stage_id: int,
    data: StageUpdate,
    db: Session = Depends(get_db)
):
    """更新单个课阶"""
    stage = db.query(Stage).filter(
        Stage.course_id == course_id,
        Stage.id == stage_id
    ).first()
    if not stage:
        raise HTTPException(404, "课阶不存在")
    
    if data.name is not None and data.name != stage.name:
        existing = db.query(Stage).filter(
            Stage.course_id == course_id,
            Stage.name == data.name,
            Stage.id != stage_id
        ).first()
        if existing:
            raise HTTPException(400, "该课程下已存在同名课阶")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(stage, field, value)
    
    db.commit()
    return {"code": 0, "message": "更新成功"}


@router.delete("/courses/{course_id}/stages/{stage_id}")
def delete_stage(
    course_id: int,
    stage_id: int,
    db: Session = Depends(get_db)
):
    """删除单个课阶"""
    stage = db.query(Stage).filter(
        Stage.course_id == course_id,
        Stage.id == stage_id
    ).first()
    if not stage:
        raise HTTPException(404, "课阶不存在")
    
    class_count = db.query(Class).filter(Class.stage_id == stage_id).count()
    if class_count > 0:
        raise HTTPException(400, f"该课阶已被 {class_count} 个班级使用，无法删除")
    
    db.delete(stage)
    db.commit()
    return {"code": 0, "message": "已删除"}


# ================================================================
# 三、套餐管理（保留完整功能）
# ================================================================

@router.get("/courses/{course_id}/packages")
def get_course_packages(
    course_id: int,
    db: Session = Depends(get_db)
):
    """获取课程下的所有套餐"""
    course = db.query(Course).get(course_id)
    if not course:
        raise HTTPException(404, "课程不存在")
    
    packages = db.query(CoursePackage).filter(
        CoursePackage.course_id == course_id
    ).order_by(CoursePackage.sort_order.asc()).all()
    
    return {"code": 0, "data": [{
        "id": p.id,
        "course_id": p.course_id,
        "stage_id": p.stage_id,
        "name": p.name,
        "purchase_hours": p.purchase_hours,
        "gift_hours": p.gift_hours,
        "discount_mode": p.discount_mode,
        "discount_rate": p.discount_rate,
        "direct_reduction": p.direct_reduction,
        "validity_days": p.validity_days,
        "leave_limit": p.leave_limit,
        "leave_limit_count": p.leave_limit_count,
        "sort_order": p.sort_order,
        "is_default": p.is_default,
        "remark": p.remark,
        "created_at": p.created_at.isoformat() if p.created_at else '',
        "updated_at": p.updated_at.isoformat() if p.updated_at else ''
    } for p in packages]}


@router.post("/packages")
def create_package(
    data: PackageCreate,
    db: Session = Depends(get_db)
):
    """创建课程套餐"""
    course = db.query(Course).get(data.course_id)
    if not course:
        raise HTTPException(404, "课程不存在")
    
    # 如果指定了课阶，验证课阶属于该课程
    if data.stage_id:
        stage = db.query(Stage).filter(
            Stage.id == data.stage_id,
            Stage.course_id == data.course_id
        ).first()
        if not stage:
            raise HTTPException(400, "课阶不存在或不属于该课程")
    
    pkg = CoursePackage(**data.model_dump())
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return {"code": 0, "data": {"id": pkg.id}, "message": "创建成功"}


@router.put("/packages/{package_id}")
def update_package(
    package_id: int,
    data: PackageUpdate,
    db: Session = Depends(get_db)
):
    """更新课程套餐"""
    pkg = db.query(CoursePackage).get(package_id)
    if not pkg:
        raise HTTPException(404, "套餐不存在")
    
    # 如果修改了课阶，验证课阶属于该课程
    if data.stage_id is not None:
        stage = db.query(Stage).filter(
            Stage.id == data.stage_id,
            Stage.course_id == pkg.course_id
        ).first()
        if not stage:
            raise HTTPException(400, "课阶不存在或不属于该课程")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pkg, field, value)
    
    db.commit()
    return {"code": 0, "message": "更新成功"}


@router.delete("/packages/{package_id}")
def delete_package(
    package_id: int,
    db: Session = Depends(get_db)
):
    """删除课程套餐"""
    pkg = db.query(CoursePackage).get(package_id)
    if not pkg:
        raise HTTPException(404, "套餐不存在")
    
    db.delete(pkg)
    db.commit()
    return {"code": 0, "message": "已删除"}