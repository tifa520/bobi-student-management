from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import json

from app.database import get_db
from app.models import (
    Student, Item, InventoryBatch, InventoryTransaction, MiscFee, IntegralRecord, SystemConfig,
    Teacher, Course, Class, Schedule, Attendance,
    SalaryRule, SalaryRuleTier, TeacherSalary, TeacherSalaryDetail, TeacherSalaryAdjustment
)
from app.utils import get_current_user
from app.services.salary_service import SalaryService
from loguru import logger

router = APIRouter()

# ---------- 请求模型 ----------
class TierCreate(BaseModel):
    min_value: float
    max_value: Optional[float] = None
    unit_price: float = 0.0
    ratio: Optional[float] = None
    is_per_person: bool = False

class SalaryRuleCreate(BaseModel):
    rule_name: str
    applicable_type: str
    applicable_id: int
    calculation_type: str
    commission_type: str
    fixed_ratio: float = 0.0
    fixed_unit_price: float = 0.0
    tiers: List[TierCreate] = []
    is_enabled: bool = True
    remark: str = ''

class SalaryRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    is_enabled: Optional[bool] = None
    fixed_ratio: Optional[float] = None
    fixed_unit_price: Optional[float] = None
    tiers: Optional[List[TierCreate]] = None
    remark: Optional[str] = None

class AdjustRequest(BaseModel):
    adjust_amount: float
    reason: str

class PayRequest(BaseModel):
    payment_method: str = '银行转账'
    remark: Optional[str] = ''

# ---------- 规则管理 ----------
@router.get("/salary/rules")
def get_salary_rules(
    applicable_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(SalaryRule)
    if applicable_type:
        query = query.filter(SalaryRule.applicable_type == applicable_type)
    rules = query.all()
    result = []
    for r in rules:
        result.append({
            "id": r.id,
            "rule_name": r.rule_name,
            "applicable_type": r.applicable_type,
            "applicable_id": r.applicable_id,
            "calculation_type": r.calculation_type,
            "commission_type": r.commission_type,
            "fixed_ratio": r.fixed_ratio,
            "fixed_unit_price": r.fixed_unit_price,
            "is_enabled": r.is_enabled,
            "remark": r.remark,
            "tiers": [{"min_value": t.min_value, "max_value": t.max_value, "unit_price": t.unit_price, "ratio": t.ratio, "is_per_person": t.is_per_person} for t in r.tiers]
        })
    return {"code": 0, "data": result}

@router.post("/salary/rules")
def create_salary_rule(data: SalaryRuleCreate, db: Session = Depends(get_db)):
    rule = SalaryRule(
        rule_name=data.rule_name,
        applicable_type=data.applicable_type,
        applicable_id=data.applicable_id,
        calculation_type=data.calculation_type,
        commission_type=data.commission_type,
        fixed_ratio=data.fixed_ratio,
        fixed_unit_price=data.fixed_unit_price,
        is_enabled=data.is_enabled,
        remark=data.remark
    )
    db.add(rule)
    db.flush()
    for tier_data in data.tiers:
        tier = SalaryRuleTier(
            rule_id=rule.id,
            min_value=tier_data.min_value,
            max_value=tier_data.max_value,
            unit_price=tier_data.unit_price,
            ratio=tier_data.ratio,
            is_per_person=tier_data.is_per_person
        )
        db.add(tier)
    db.commit()
    return {"code": 0, "message": "创建成功", "data": {"id": rule.id}}

@router.put("/salary/rules/{rule_id}")
def update_salary_rule(rule_id: int, data: SalaryRuleUpdate, db: Session = Depends(get_db)):
    rule = db.query(SalaryRule).get(rule_id)
    if not rule:
        raise HTTPException(404, "规则不存在")
    if data.rule_name is not None:
        rule.rule_name = data.rule_name
    if data.is_enabled is not None:
        rule.is_enabled = data.is_enabled
    if data.fixed_ratio is not None:
        rule.fixed_ratio = data.fixed_ratio
    if data.fixed_unit_price is not None:
        rule.fixed_unit_price = data.fixed_unit_price
    if data.remark is not None:
        rule.remark = data.remark
    if data.tiers is not None:
        db.query(SalaryRuleTier).filter(SalaryRuleTier.rule_id == rule_id).delete()
        for tier_data in data.tiers:
            tier = SalaryRuleTier(
                rule_id=rule.id,
                min_value=tier_data.min_value,
                max_value=tier_data.max_value,
                unit_price=tier_data.unit_price,
                ratio=tier_data.ratio,
                is_per_person=tier_data.is_per_person
            )
            db.add(tier)
    db.commit()
    return {"code": 0, "message": "更新成功"}

@router.delete("/salary/rules/{rule_id}")
def delete_salary_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(SalaryRule).get(rule_id)
    if not rule:
        raise HTTPException(404, "规则不存在")
    db.delete(rule)
    db.commit()
    return {"code": 0, "message": "删除成功"}

# ---------- 薪酬计算 ----------
@router.post("/salary/calculate")
def calculate_salary(
    teacher_id: int = Query(...),
    settlement_month: str = Query(..., regex=r'^\d{4}-\d{2}$'),
    db: Session = Depends(get_db)
):
    service = SalaryService(db)
    salary = service.calculate_teacher_salary(teacher_id, settlement_month)
    return {"code": 0, "message": "薪酬计算成功", "data": {"salary_id": salary.id}}

@router.get("/salary/salaries")
def get_salaries(
    teacher_id: Optional[int] = Query(None),
    settlement_month: Optional[str] = Query(None),
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(TeacherSalary)
    if teacher_id:
        query = query.filter(TeacherSalary.teacher_id == teacher_id)
    if settlement_month:
        query = query.filter(TeacherSalary.settlement_month == settlement_month)
    total = query.count()
    salaries = query.order_by(TeacherSalary.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    result = []
    for s in salaries:
        teacher = db.query(Teacher).get(s.teacher_id)
        result.append({
            "id": s.id,
            "teacher_id": s.teacher_id,
            "teacher_name": teacher.name if teacher else '',
            "settlement_month": s.settlement_month,
            "total_classes": s.total_classes,
            "total_attendance_count": s.total_attendance_count,
            "total_consumed_hours": s.total_consumed_hours,
            "total_consumed_amount": s.total_consumed_amount,
            "base_amount": s.base_amount,
            "adjust_amount": s.adjust_amount,
            "final_amount": s.final_amount,
            "status": s.status,
            "created_at": s.created_at.isoformat(),
            "paid_at": s.paid_at.isoformat() if s.paid_at else None,
            "payment_method": s.payment_method or ''
        })
    return {"code": 0, "data": {"items": result, "total": total}}

@router.get("/salary/salaries/{salary_id}")
def get_salary_detail(salary_id: int, db: Session = Depends(get_db)):
    salary = db.query(TeacherSalary).filter(TeacherSalary.id == salary_id).first()
    if not salary:
        raise HTTPException(404, "薪酬记录不存在")

    teacher = db.query(Teacher).get(salary.teacher_id)
    details = db.query(TeacherSalaryDetail).filter(TeacherSalaryDetail.salary_id == salary_id).all()
    adjustments = db.query(TeacherSalaryAdjustment).filter(TeacherSalaryAdjustment.salary_id == salary_id).order_by(TeacherSalaryAdjustment.created_at.desc()).all()

    # 获取考勤明细（该教师该月份的有效考勤）
    year, month = salary.settlement_month.split('-')
    start_date = datetime(int(year), int(month), 1).date()
    if month == '12':
        end_date = datetime(int(year)+1, 1, 1).date()
    else:
        end_date = datetime(int(year), int(month)+1, 1).date()

    attendances = db.query(Attendance).join(
        Schedule, Attendance.schedule_id == Schedule.id
    ).filter(
        Schedule.teacher_id == salary.teacher_id,
        Schedule.course_date >= start_date,
        Schedule.course_date < end_date,
        Attendance.status.in_(['出勤', '迟到'])
    ).all()

    attendance_details = []
    for a in attendances:
        class_name = ''
        if a.class_id:
            cls = db.query(Class).get(a.class_id)
            class_name = cls.name if cls else ''
        attendance_details.append({
            "date": a.created_at.strftime("%Y-%m-%d"),
            "class_name": class_name,
            "status": a.status,
            "deduct_hours": a.deduct_hours,
            "deduct_amount": a.deduct_amount
        })

    return {
        "code": 0,
        "data": {
            "id": salary.id,
            "teacher_id": salary.teacher_id,
            "teacher_name": teacher.name if teacher else '',
            "settlement_month": salary.settlement_month,
            "total_classes": salary.total_classes,
            "total_attendance_count": salary.total_attendance_count,
            "total_consumed_hours": salary.total_consumed_hours,
            "total_consumed_amount": salary.total_consumed_amount,
            "base_amount": salary.base_amount,
            "adjust_amount": salary.adjust_amount,
            "final_amount": salary.final_amount,
            "status": salary.status,
            "created_at": salary.created_at.isoformat(),
            "details": [{
                "id": d.id,
                "rule_name": d.rule_name,
                "target_type": d.target_type,
                "target_name": d.target_name,
                "calculation_type": d.calculation_type,
                "calculated_value": d.calculated_value,
                "unit_price": d.unit_price,
                "calculated_amount": d.calculated_amount
            } for d in details],
            "adjustments": [{
                "id": a.id,
                "adjust_amount": a.adjust_amount,
                "reason": a.reason,
                "operator_name": a.operator_name,
                "created_at": a.created_at.isoformat()
            } for a in adjustments],
            "attendance_details": attendance_details
        }
    }

@router.post("/salary/salaries/{salary_id}/pay")
def pay_salary(
    salary_id: int,
    data: PayRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        current_user = get_current_user(request, db)
    except:
        raise HTTPException(401, "未授权")
    
    salary = db.query(TeacherSalary).filter(TeacherSalary.id == salary_id).first()
    if not salary:
        raise HTTPException(404, "薪酬记录不存在")
    if salary.status != 'confirmed':
        raise HTTPException(400, "只有已确认的薪酬才能发放")
    if salary.status == 'paid':
        raise HTTPException(400, "薪酬已发放，请勿重复操作")
    
    salary.status = 'paid'
    salary.paid_at = datetime.now()
    salary.payment_method = data.payment_method
    # 可以记录 remark 到 salary 的 remark 字段或单独字段，这里简化
    if data.remark:
        salary.remark = (salary.remark or '') + f'\n发放备注: {data.remark}'
    db.commit()
    return {"code": 0, "message": "发放成功"}



@router.post("/salary/salaries/{salary_id}/adjust")
def adjust_salary(
    salary_id: int,
    data: AdjustRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        current_user = get_current_user(request, db)
        operator_name = current_user.name
        operator_id = current_user.id
    except:
        operator_name = 'system'
        operator_id = None
    service = SalaryService(db)
    adjustment = service.apply_adjustment(salary_id, data.adjust_amount, data.reason, operator_id, operator_name)
    return {"code": 0, "message": "调整成功", "data": {"adjustment_id": adjustment.id}}

@router.post("/salary/salaries/{salary_id}/confirm")
def confirm_salary(
    salary_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        current_user = get_current_user(request, db)
    except:
        raise HTTPException(401, "未授权")
    salary = db.query(TeacherSalary).filter(TeacherSalary.id == salary_id).first()
    if not salary:
        raise HTTPException(404, "薪酬记录不存在")
    if salary.status != 'calculated':
        raise HTTPException(400, "只有已计算状态的薪酬才能确认")
    salary.status = 'confirmed'
    db.commit()
    return {"code": 0, "message": "薪酬已确认"}