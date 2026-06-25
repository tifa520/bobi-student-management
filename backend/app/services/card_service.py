from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from app.models import LearningCard, CardTransaction, Order, Attendance, Class, Course, StudentCourse, Schedule
from app.utils import deduct_from_orders_with_detail
from sqlalchemy import func


class CardService:
    def __init__(self, db: Session):
        self.db = db

    def _execute_in_transaction(self, func, *args, **kwargs):
        try:
            result = func(*args, **kwargs)
            self.db.flush()
            return result
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"数据库操作失败: {str(e)}")

    def get_or_create_card(self, student_id: int, course_id: int, class_id: int = None) -> LearningCard:
        card = self.db.query(LearningCard).filter(
            LearningCard.student_id == student_id,
            LearningCard.course_id == course_id,
            LearningCard.status.in_(['active', 'suspended'])
        ).first()
        if not card:
            card = LearningCard(
                student_id=student_id,
                course_id=course_id,
                class_id=class_id,
                status='active'
            )
            self.db.add(card)
            self.db.flush()
        return card

    def add_purchase(self, card: LearningCard, order, gift_hours: int = 0):
        def _add():
            card.remaining_paid_hours = (card.remaining_paid_hours or 0) + order.purchase_hours
            card.remaining_amount = (card.remaining_amount or 0.0) + order.payable_amount
            if gift_hours > 0:
                card.remaining_gift_hours = (card.remaining_gift_hours or 0) + gift_hours
            transaction = CardTransaction(
                card_id=card.id,
                order_id=order.id,
                change_type='purchase',
                paid_hours_change=order.purchase_hours,
                amount_change=order.payable_amount,
                gift_hours_change=gift_hours,
                reason=f"订单 {order.order_no}",
                occurred_at=order.created_at.date()
            )
            self.db.add(transaction)
            return card
        return self._execute_in_transaction(_add)

    def deduct_class_hours(self, card: LearningCard, deduct_hours: int, deduct_amount: float,
                           gift_deduct: int = 0, purchased_deduct: int = 0,
                           attendance_id: int = None, reason: str = ''):
        def _deduct():
            card.remaining_paid_hours -= deduct_hours
            card.remaining_amount -= deduct_amount
            if gift_deduct > 0:
                card.remaining_gift_hours -= gift_deduct
            transaction = CardTransaction(
                card_id=card.id,
                attendance_id=attendance_id,
                change_type='attendance',
                paid_hours_change=-deduct_hours,
                amount_change=-deduct_amount,
                gift_hours_change=-gift_deduct,
                reason=reason,
                occurred_at=date.today()
            )
            self.db.add(transaction)
            return card
        return self._execute_in_transaction(_deduct)

    def transfer_out(self, card: LearningCard, hours: int, amount: float, reason: str = ''):
        def _transfer_out():
            card.remaining_paid_hours -= hours
            card.remaining_amount -= amount
            transaction = CardTransaction(
                card_id=card.id,
                change_type='transfer_out',
                paid_hours_change=-hours,
                amount_change=-amount,
                reason=reason,
                occurred_at=date.today()
            )
            self.db.add(transaction)
            return card
        return self._execute_in_transaction(_transfer_out)

    def transfer_in(self, card: LearningCard, hours: int, amount: float, reason: str = ''):
        def _transfer_in():
            card.remaining_paid_hours += hours
            card.remaining_amount += amount
            transaction = CardTransaction(
                card_id=card.id,
                change_type='transfer_in',
                paid_hours_change=hours,
                amount_change=amount,
                reason=reason,
                occurred_at=date.today()
            )
            self.db.add(transaction)
            return card
        return self._execute_in_transaction(_transfer_in)

    def custom_add(self, card: LearningCard, hours: int, reason: str = ''):
        def _add():
            card.remaining_paid_hours += hours
            transaction = CardTransaction(
                card_id=card.id,
                change_type='custom_add',
                paid_hours_change=hours,
                reason=reason,
                occurred_at=date.today()
            )
            self.db.add(transaction)
            return card
        return self._execute_in_transaction(_add)

    def custom_sub(self, card: LearningCard, hours: int, amount: float, reason: str = ''):
        def _sub():
            card.remaining_paid_hours -= hours
            card.remaining_amount -= amount
            transaction = CardTransaction(
                card_id=card.id,
                change_type='custom_sub',
                paid_hours_change=-hours,
                amount_change=-amount,
                reason=reason,
                occurred_at=date.today()
            )
            self.db.add(transaction)
            return card
        return self._execute_in_transaction(_sub)

    def add_gift(self, card: LearningCard, hours: int, reason: str = ''):
        def _add_gift():
            card.remaining_gift_hours = (card.remaining_gift_hours or 0) + hours
            transaction = CardTransaction(
                card_id=card.id,
                change_type='gift_add',
                gift_hours_change=hours,
                reason=reason,
                occurred_at=date.today()
            )
            self.db.add(transaction)
            return card
        return self._execute_in_transaction(_add_gift)

    def sub_gift(self, card: LearningCard, hours: int, reason: str = ''):
        def _sub_gift():
            card.remaining_gift_hours -= hours
            transaction = CardTransaction(
                card_id=card.id,
                change_type='gift_sub',
                gift_hours_change=-hours,
                reason=reason,
                occurred_at=date.today()
            )
            self.db.add(transaction)
            return card
        return self._execute_in_transaction(_sub_gift)

    def refund(self, card: LearningCard, hours: int, amount: float, reason: str = ''):
        def _refund():
            card.remaining_paid_hours -= hours
            card.remaining_amount -= amount
            transaction = CardTransaction(
                card_id=card.id,
                change_type='refund',
                paid_hours_change=-hours,
                amount_change=-amount,
                reason=reason,
                occurred_at=date.today()
            )
            self.db.add(transaction)
            return card
        return self._execute_in_transaction(_refund)

    def graduate(self, card: LearningCard):
        def _graduate():
            if card.remaining_paid_hours > 0 or card.remaining_amount > 0:
                transaction = CardTransaction(
                    card_id=card.id,
                    change_type='graduation',
                    paid_hours_change=-card.remaining_paid_hours,
                    amount_change=-card.remaining_amount,
                    gift_hours_change=-card.remaining_gift_hours,
                    reason="课程结业",
                    occurred_at=date.today()
                )
                self.db.add(transaction)
            card.remaining_paid_hours = 0
            card.remaining_amount = 0.0
            card.remaining_gift_hours = 0
            card.status = 'graduated'
            return card
        return self._execute_in_transaction(_graduate)

    def update_validity(self, card: LearningCard, validity_days: int = None):
        def _update():
            if validity_days is not None and validity_days > 0:
                if card.manual_validity_days:
                    card.manual_validity_days += validity_days
                else:
                    card.manual_validity_days = validity_days
                if card.validity_end_date:
                    card.validity_end_date = card.validity_end_date + timedelta(days=validity_days)
                else:
                    card.validity_end_date = date.today() + timedelta(days=validity_days)
            else:
                card.manual_validity_days = None
                card.validity_end_date = self._calculate_validity_from_orders(card)
            return card
        return self._execute_in_transaction(_update)

    def _calculate_validity_from_orders(self, card: LearningCard):
        orders = self.db.query(Order).filter(
            Order.student_id == card.student_id,
            Order.course_id == card.course_id,
            Order.is_active == True,
            Order.is_invalid == False,
            Order.enroll_type.notin_(['尾款补费', '转课时'])
        ).order_by(Order.created_at.asc()).all()
        if not orders:
            return None
        start_date = orders[0].created_at.date()
        total_days = 0
        for o in orders:
            if o.validity_type == 'days' and o.validity_value:
                try:
                    total_days += int(o.validity_value)
                except:
                    pass
        if total_days == 0:
            return None
        end_date = start_date + timedelta(days=total_days)
        if card.suspended_start and card.suspended_end:
            freeze_start = max(card.suspended_start, start_date)
            freeze_end = min(card.suspended_end, end_date)
            if freeze_end >= freeze_start:
                freeze_days = (freeze_end - freeze_start).days + 1
                end_date += timedelta(days=freeze_days)
        return end_date

    def verify_card_consistency(self, student_id: int, course_id: int) -> dict:
        """
        校验卡片数据与流水是否一致，不修改任何数据
        用于定期检查数据一致性，发现问题时发出告警
        """
        from sqlalchemy import func
        
        card = self._get_or_create_card(student_id, course_id)
        if not card:
            return {
                "exists": False,
                "message": f"课程账户不存在: student={student_id}, course={course_id}"
            }
        
        # 从流水表聚合实际应剩余的数据
        stats = self.db.query(
            func.sum(CardTransaction.paid_hours_change).label('paid_hours'),
            func.sum(CardTransaction.gift_hours_change).label('gift_hours'),
            func.sum(CardTransaction.amount_change).label('amount')
        ).filter(CardTransaction.card_id == card.id).first()
        
        ledger_paid = stats.paid_hours or 0
        ledger_gift = stats.gift_hours or 0
        ledger_amount = stats.amount or 0.0
        
        is_consistent = (
            card.remaining_paid_hours == ledger_paid and
            card.remaining_gift_hours == ledger_gift and
            abs(card.remaining_amount - ledger_amount) < 0.01
        )
        
        return {
            "exists": True,
            "card": {
                "remaining_paid_hours": card.remaining_paid_hours,
                "remaining_gift_hours": card.remaining_gift_hours,
                "remaining_amount": round(card.remaining_amount, 2)
            },
            "ledger": {
                "remaining_paid_hours": ledger_paid,
                "remaining_gift_hours": ledger_gift,
                "remaining_amount": round(ledger_amount, 2)
            },
            "is_consistent": is_consistent,
            "diff": {
                "paid_hours": card.remaining_paid_hours - ledger_paid,
                "gift_hours": card.remaining_gift_hours - ledger_gift,
                "amount": round(card.remaining_amount - ledger_amount, 2)
            }
        }

    # 可选：提供一个仅用于紧急修复的带备份功能的方法
    def emergency_rebuild_with_backup(self, student_id: int, course_id: int, operator: str = 'system') -> dict:
        """
        紧急重建卡片（会删除流水！仅限数据严重异常时使用）
        重建前会自动备份被删除的流水到备份表
        """
        from app.models import CardTransactionBackup
        
        card = self._get_or_create_card(student_id, course_id)
        if not card:
            return {"success": False, "message": "课程账户不存在"}
        
        # 1. 备份将被删除的流水
        transactions = self.db.query(CardTransaction).filter(
            CardTransaction.card_id == card.id
        ).all()
        
        for txn in transactions:
            backup = CardTransactionBackup(
                original_id=txn.id,
                card_id=txn.card_id,
                order_id=txn.order_id,
                attendance_id=txn.attendance_id,
                change_type=txn.change_type,
                paid_hours_change=txn.paid_hours_change,
                amount_change=txn.amount_change,
                gift_hours_change=txn.gift_hours_change,
                leave_change=txn.leave_change,
                reason=txn.reason,
                occurred_at=txn.occurred_at,
                created_at=txn.created_at,
                backup_at=datetime.now(),
                backup_by=operator,
                backup_reason="emergency_rebuild"
            )
            self.db.add(backup)
        
        # 2. 删除原流水
        self.db.query(CardTransaction).filter(CardTransaction.card_id == card.id).delete()
        
        # 3. 重建（复用原有逻辑）
        self._rebuild_card_from_scratch_internal(student_id, course_id)
        
        return {
            "success": True,
            "message": f"已备份 {len(transactions)} 条流水记录到 backup 表",
            "backup_count": len(transactions)
        }

    def _rebuild_card_from_scratch_internal(self, student_id: int, course_id: int):
        """内部重建方法（不删除流水，仅用于紧急重建调用）"""
        # 原有重建逻辑，但不包含删除流水的步骤
        card = self._get_or_create_card(student_id, course_id)
        card.remaining_paid_hours = 0
        card.remaining_gift_hours = 0
        card.remaining_amount = 0.0
        card.validity_end_date = None
        card.manual_validity_days = None
        card.status = 'active'
        card.suspended_start = None
        card.suspended_end = None
        card.total_leave_quota = 0
        card.used_leave = 0
        
        # 从订单重新生成购买流水
        orders = self.db.query(Order).filter(
            Order.student_id == student_id,
            Order.course_id == course_id,
            Order.is_active == True,
            Order.is_invalid == False
        ).order_by(Order.created_at.asc()).all()
        for o in orders:
            self.add_purchase(card, o, o.gift_hours)
        
        # 从考勤记录生成扣费流水
        attendances = self.db.query(Attendance).join(Schedule, Attendance.schedule_id == Schedule.id)\
            .join(Class, Schedule.class_id == Class.id)\
            .filter(Attendance.student_id == student_id, Class.course_id == course_id)\
            .order_by(Attendance.created_at.asc()).all()
        for a in attendances:
            if a.deduct_hours > 0:
                self.deduct_class_hours(card, a.deduct_hours, a.deduct_amount, a.gift_deduct, a.purchased_deduct, a.id, a.status)
        
        # 有效期重建
        card.validity_end_date = self._calculate_validity_from_orders(card)
        
        # 请假配额重建
        total_leave_quota = self.db.query(func.sum(Order.leave_limit_count)).filter(
            Order.student_id == student_id,
            Order.course_id == course_id,
            Order.is_active == True,
            Order.is_invalid == False,
            Order.leave_limit == '限制次数'
        ).scalar() or 0
        card.total_leave_quota = total_leave_quota
        card.used_leave = 0
        
        leave_attendances = self.db.query(Attendance).join(Schedule, Attendance.schedule_id == Schedule.id)\
            .join(Class, Schedule.class_id == Class.id)\
            .filter(Attendance.student_id == student_id, Class.course_id == course_id, Attendance.status.in_(['请假', '未到']))\
            .order_by(Attendance.created_at.asc()).all()
        for att in leave_attendances:
            if card.used_leave < card.total_leave_quota:
                card.used_leave += 1
        
        return card


def get_card_details(card: LearningCard) -> dict:
    validity_display = '-'
    if card.validity_end_date:
        validity_display = card.validity_end_date.strftime('%Y-%m-%d')
    elif card.manual_validity_days:
        validity_display = (date.today() + timedelta(days=card.manual_validity_days)).strftime('%Y-%m-%d')
    return {
        "card_id": card.id,
        "student_id": card.student_id,
        "course_id": card.course_id,
        "class_id": card.class_id,
        "remaining_hours": card.remaining_paid_hours,
        "remaining_amount": card.remaining_amount,
        "remaining_gift_hours": card.remaining_gift_hours,
        "validity_display": validity_display,
        "manual_validity_days": card.manual_validity_days,
        "status": card.status,
        "suspended_start": card.suspended_start.strftime('%Y-%m-%d') if card.suspended_start else None,
        "suspended_end": card.suspended_end.strftime('%Y-%m-%d') if card.suspended_end else None
    }