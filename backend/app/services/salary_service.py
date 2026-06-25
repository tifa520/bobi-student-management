from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException

from app.models import (
    Teacher, Course, Class, Schedule, Attendance, Student, LearningCard,
    SalaryRule, SalaryRuleTier, TeacherSalary, TeacherSalaryDetail, TeacherSalaryAdjustment,
    IntegralRecord, SystemConfig
)
from app.services.transaction_service import TransactionService
from loguru import logger


class SalaryService:
    def __init__(self, db: Session):
        self.db = db

    # ========== 辅助方法 ==========
    def _get_teacher_month_attendances(self, teacher_id: int, settlement_month: str):
        """获取某教师某月的所有有效考勤记录（出勤/迟到）"""
        year, month = map(int, settlement_month.split('-'))
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year+1, 1, 1).date()
        else:
            end_date = datetime(year, month+1, 1).date()

        attendances = self.db.query(Attendance).join(
            Schedule, Attendance.schedule_id == Schedule.id
        ).filter(
            Schedule.teacher_id == teacher_id,
            Schedule.course_date >= start_date,
            Schedule.course_date < end_date,
            Attendance.status.in_(['出勤', '迟到'])
        ).all()
        return attendances

    def _get_applicable_rules(self, teacher_id: int):
        """获取教师适用的所有启用规则（按优先级：班级 > 课程 > 教师）"""
        teacher = self.db.query(Teacher).get(teacher_id)
        if not teacher:
            return []

        # 获取教师所教班级
        class_ids = [c.id for c in teacher.classes if c.status == 'active']
        # 获取教师所教课程（通过班级）
        course_ids = list(set([c.course_id for c in teacher.classes if c.status == 'active']))

        rules = []
        if class_ids:
            class_rules = self.db.query(SalaryRule).filter(
                SalaryRule.applicable_type == 'class',
                SalaryRule.applicable_id.in_(class_ids),
                SalaryRule.is_enabled == True
            ).all()
            rules.extend(class_rules)
        if course_ids:
            course_rules = self.db.query(SalaryRule).filter(
                SalaryRule.applicable_type == 'course',
                SalaryRule.applicable_id.in_(course_ids),
                SalaryRule.is_enabled == True
            ).all()
            rules.extend(course_rules)
        teacher_rules = self.db.query(SalaryRule).filter(
            SalaryRule.applicable_type == 'teacher',
            SalaryRule.applicable_id == teacher_id,
            SalaryRule.is_enabled == True
        ).all()
        rules.extend(teacher_rules)

        # 去重并保持顺序（班级优先）
        unique = {r.id: r for r in rules}
        return list(unique.values())

    def _calculate_rule_amount_from_attendances(self, rule: SalaryRule, attendances: list, teacher_id: int) -> dict | None:
        """根据考勤记录计算单条规则的金额（支持固定和阶梯）"""
        if not attendances:
            return None

        # 计算总值（根据计薪标准）
        if rule.calculation_type == 'actual_attendance_amount':
            total_value = sum(a.deduct_amount for a in attendances)
        elif rule.calculation_type == 'attendance_count':
            total_value = len(attendances)
        elif rule.calculation_type == 'consumed_hours':
            total_value = sum(a.deduct_hours for a in attendances)
        elif rule.calculation_type == 'class_count':
            total_value = len(attendances)
        elif rule.calculation_type == 'consumed_amount':
            total_value = sum(a.deduct_amount for a in attendances)
        else:
            return None

        if total_value == 0:
            return None

        # 计算金额
        if rule.commission_type == 'fixed':
            if rule.fixed_ratio > 0:
                amount = total_value * (rule.fixed_ratio / 100)
                unit_price = rule.fixed_ratio
            else:
                amount = total_value * rule.fixed_unit_price
                unit_price = rule.fixed_unit_price
        else:  # tiered
            tiers = rule.tiers
            if not tiers:
                return None
            # 按区间查找
            matched_tier = None
            for tier in sorted(tiers, key=lambda t: t.min_value):
                if total_value >= tier.min_value and (tier.max_value is None or total_value < tier.max_value):
                    matched_tier = tier
                    break
            if not matched_tier:
                return None
            if matched_tier.ratio:
                amount = total_value * (matched_tier.ratio / 100)
                unit_price = matched_tier.ratio
            else:
                amount = total_value * matched_tier.unit_price
                unit_price = matched_tier.unit_price

        # 获取适用对象名称
        target_name = ''
        if rule.applicable_type == 'teacher':
            teacher = self.db.query(Teacher).get(rule.applicable_id)
            target_name = teacher.name if teacher else ''
        elif rule.applicable_type == 'course':
            course = self.db.query(Course).get(rule.applicable_id)
            target_name = course.name if course else ''
        elif rule.applicable_type == 'class':
            cls = self.db.query(Class).get(rule.applicable_id)
            target_name = cls.name if cls else ''

        return {
            'rule_id': rule.id,
            'rule_name': rule.rule_name,
            'target_type': rule.applicable_type,
            'target_id': rule.applicable_id,
            'target_name': target_name,
            'calculation_type': rule.calculation_type,
            'calculated_value': total_value,
            'unit_price': unit_price,
            'calculated_amount': amount
        }

    # ========== 薪酬计算主流程 ==========
    def calculate_teacher_salary(self, teacher_id: int, settlement_month: str) -> TeacherSalary:
        """为教师结算指定月份的薪酬"""
        existing = self.db.query(TeacherSalary).filter(
            TeacherSalary.teacher_id == teacher_id,
            TeacherSalary.settlement_month == settlement_month
        ).first()
        if existing:
            raise HTTPException(400, f"{settlement_month} 月份薪酬已结算，请勿重复操作")

        # 1. 获取当月考勤记录（仅出勤/迟到）
        attendances = self._get_teacher_month_attendances(teacher_id, settlement_month)
        total_classes = len(attendances)
        total_attendance_count = total_classes
        total_consumed_hours = sum(a.deduct_hours for a in attendances)
        total_consumed_amount = sum(a.deduct_amount for a in attendances)

        # 2. 获取适用规则
        rules = self._get_applicable_rules(teacher_id)

        # 3. 逐规则计算
        details = []
        base_amount = 0.0
        for rule in rules:
            detail = self._calculate_rule_amount_from_attendances(rule, attendances, teacher_id)
            if detail:
                details.append(detail)
                base_amount += detail['calculated_amount']

        # 4. 创建主记录
        salary = TeacherSalary(
            teacher_id=teacher_id,
            settlement_month=settlement_month,
            total_classes=total_classes,
            total_attendance_count=total_attendance_count,
            total_consumed_hours=total_consumed_hours,
            total_consumed_amount=total_consumed_amount,
            base_amount=base_amount,
            adjust_amount=0.0,
            final_amount=base_amount,
            status='calculated'
        )
        self.db.add(salary)
        self.db.flush()

        # 5. 保存明细
        for d in details:
            detail_obj = TeacherSalaryDetail(
                salary_id=salary.id,
                rule_id=d['rule_id'],
                rule_name=d['rule_name'],
                target_type=d['target_type'],
                target_id=d['target_id'],
                target_name=d['target_name'],
                calculation_type=d['calculation_type'],
                calculated_value=d['calculated_value'],
                unit_price=d['unit_price'],
                calculated_amount=d['calculated_amount']
            )
            self.db.add(detail_obj)

        self.db.commit()
        return salary

    # ========== 薪酬调整 ==========
    def apply_adjustment(self, salary_id: int, adjust_amount: float, reason: str, operator_id: int = None, operator_name: str = 'system') -> TeacherSalaryAdjustment:
        salary = self.db.query(TeacherSalary).filter(TeacherSalary.id == salary_id).first()
        if not salary:
            raise HTTPException(404, "薪酬记录不存在")
        if salary.status != 'calculated':
            raise HTTPException(400, "只有未确认的薪酬才能调整")

        adjustment = TeacherSalaryAdjustment(
            salary_id=salary_id,
            adjust_amount=adjust_amount,
            reason=reason,
            operator_id=operator_id,
            operator_name=operator_name
        )
        self.db.add(adjustment)

        new_adjust_total = (salary.adjust_amount or 0) + adjust_amount
        salary.adjust_amount = new_adjust_total
        salary.final_amount = salary.base_amount + new_adjust_total
        self.db.commit()
        return adjustment