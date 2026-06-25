import threading
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.models import CardTransaction, LearningCard, Order, Attendance, ValidityLog, PaymentLog
from loguru import logger

# 保留线程锁用于单进程内防重，但主要依赖数据库行锁
_lock_dict = {}
_lock_dict_lock = threading.Lock()

def get_lock(student_id, course_id):
    key = f"{student_id}_{course_id}"
    with _lock_dict_lock:
        if key not in _lock_dict:
            _lock_dict[key] = threading.Lock()
        return _lock_dict[key]


class TransactionService:
    def __init__(self, db: Session):
        self.db = db

    # ========== 卡片管理（带数据库行锁） ==========
    def _get_or_create_card(self, student_id: int, course_id: int, class_id: int = None):
        card = self.db.query(LearningCard).filter(
            LearningCard.student_id == student_id,
            LearningCard.course_id == course_id
        ).with_for_update().first()
        if not card:
            card = LearningCard(
                student_id=student_id,
                course_id=course_id,
                class_id=class_id,
                status='active',
                remaining_paid_hours=0,
                remaining_gift_hours=0,
                remaining_amount=0.0,
                total_leave_quota=0,
                used_leave=0,
                # ★ 新卡 last_refresh_at 设为 None，强制后续全量刷新
                last_refresh_at=None
            )
            self.db.add(card)
            self.db.flush()
        else:
            if card.status != 'active':
                card.status = 'active'
                card.suspended_start = None
                card.suspended_end = None
                self.db.flush()
        return card

    # ========== 流水记录 ==========
    def _add_card_transaction(self, card_id: int, change_type: str,
                               paid_hours_change: int = 0, gift_hours_change: int = 0,
                               amount_change: float = 0.0, leave_change: int = 0,
                               reason: str = '', order_id: int = None,
                               attendance_id: int = None, occurred_at: date = None):
        txn = CardTransaction(
            card_id=card_id,
            change_type=change_type,
            paid_hours_change=paid_hours_change,
            gift_hours_change=gift_hours_change,
            amount_change=amount_change,
            leave_change=leave_change,
            reason=reason,
            order_id=order_id,
            attendance_id=attendance_id,
            occurred_at=occurred_at or date.today()
        )
        self.db.add(txn)
        self.db.flush()
        return txn

    def _add_validity_log(self, card_id: int, change_days: int, reason: str,
                        source_type: str, source_id: int = None, occurred_at: date = None):
        validity_log = ValidityLog(
            card_id=card_id,
            change_days=change_days,
            reason=reason,
            source_type=source_type,
            source_id=source_id,
            occurred_at=occurred_at or date.today()
        )
        self.db.add(validity_log)
        self.db.flush()
        return validity_log

    def _add_payment_log(self, order_id: int, amount: float, payment_method: str,
                         payment_type: str, remark: str = '', occurred_at: datetime = None):
        if occurred_at is None:
            occurred_at = datetime.now()
        payment_log = PaymentLog(
            order_id=order_id,
            amount=amount,
            payment_method=payment_method,
            payment_type=payment_type,
            remark=remark,
            occurred_at=occurred_at
        )
        self.db.add(payment_log)
        self.db.flush()
        return payment_log

    # ========== 有效期计算（排除无效订单） ==========
    def _calculate_validity_excluding_invalid_orders(self, card: LearningCard):
        logs = self.db.query(ValidityLog).filter(ValidityLog.card_id == card.id).order_by(ValidityLog.occurred_at).all()
        if not logs:
            return None

        total_days = 0
        first_valid_date = None

        for log in logs:
            if log.source_type == 'order':
                order = self.db.query(Order).get(log.source_id)
                if order and order.is_invalid:
                    continue
            total_days += log.change_days
            if first_valid_date is None:
                occurred = log.occurred_at
                if hasattr(occurred, 'date'):
                    occurred = occurred.date()
                first_valid_date = occurred

        if total_days <= 0 or first_valid_date is None:
            return None

        start_date = first_valid_date
        today = date.today()
        days_passed = (today - start_date).days
        remaining_days = max(0, total_days - days_passed)
        end_date = today + timedelta(days=remaining_days)

        # 停课顺延（如果有）
        if card.suspended_start and card.suspended_end and card.suspended_start <= end_date:
            suspend_days = (card.suspended_end - card.suspended_start).days + 1
            end_date += timedelta(days=suspend_days)

        return end_date

    # ========== 卡片刷新（增量聚合 + 全量兜底） ==========
    def _refresh_card(self, student_id: int, course_id: int, force_full: bool = False):
        """
        刷新卡片数据：
        - 如果 force_full=True，强制全量聚合
        - 如果卡片没有 last_refresh_at（新卡），也使用全量聚合
        - 否则根据时间决定增量或全量
        """
        card = self.db.query(LearningCard).filter(
            LearningCard.student_id == student_id,
            LearningCard.course_id == course_id
        ).with_for_update().first()
        if not card:
            card = self._get_or_create_card(student_id, course_id)
            # 新卡 last_refresh_at 设为 None
            card.last_refresh_at = None

        now = datetime.now()
        use_incremental = False
        incremental_success = False

        # 判断是否可以使用增量聚合：非强制全量 且 last_refresh_at 存在 且 距现在小于5分钟
        if not force_full and card.last_refresh_at and (now - card.last_refresh_at).total_seconds() < 300:
            use_incremental = True

        if use_incremental:
            try:
                # 增量聚合：只聚合 last_refresh_at 之后的新增流水
                stats = self.db.query(
                    func.sum(CardTransaction.paid_hours_change).label('paid_hours'),
                    func.sum(CardTransaction.gift_hours_change).label('gift_hours'),
                    func.sum(CardTransaction.amount_change).label('amount')
                ).filter(
                    CardTransaction.card_id == card.id,
                    CardTransaction.created_at > card.last_refresh_at
                ).first()

                # 应用增量变更（如果存在）
                if stats.paid_hours is not None:
                    card.remaining_paid_hours += stats.paid_hours
                if stats.gift_hours is not None:
                    card.remaining_gift_hours += stats.gift_hours
                if stats.amount is not None:
                    card.remaining_amount += stats.amount

                # 刷新请假配额和已用次数（从流水全量计算）
                self._refresh_leave_quota(card)
                self._refresh_used_leave(card)

                # 有效期增量计算复杂，直接全量计算（或保持不变）
                validity_end = self._calculate_validity_excluding_invalid_orders(card)
                card.validity_end_date = validity_end if validity_end else None

                incremental_success = True
                logger.debug(f"增量聚合成功: card_id={card.id}, student={student_id}, course={course_id}")
            except Exception as e:
                logger.warning(f"增量聚合失败，降级为全量聚合: {e}")
                use_incremental = False

        # 如果未使用增量或增量失败，则执行全量聚合
        if not use_incremental or not incremental_success:
            # 全量聚合
            base_stats = self.db.query(
                func.sum(CardTransaction.paid_hours_change).label('paid_hours'),
                func.sum(CardTransaction.gift_hours_change).label('gift_hours'),
                func.sum(CardTransaction.amount_change).label('amount')
            ).filter(CardTransaction.card_id == card.id).first()

            card.remaining_paid_hours = base_stats.paid_hours or 0
            card.remaining_gift_hours = base_stats.gift_hours or 0
            card.remaining_amount = base_stats.amount or 0.0

            self._refresh_leave_quota(card)
            self._refresh_used_leave(card)

            validity_end = self._calculate_validity_excluding_invalid_orders(card)
            card.validity_end_date = validity_end if validity_end else None

            logger.info(f"全量聚合完成: card_id={card.id}, student={student_id}, course={course_id}")

        # 更新最后刷新时间
        card.last_refresh_at = now
        self.db.flush()
        return card

    def _refresh_leave_quota(self, card: LearningCard):
        """刷新请假总配额（独立方法，便于复用）"""
        total_quota = self.db.query(func.sum(CardTransaction.leave_change)).filter(
            CardTransaction.card_id == card.id,
            CardTransaction.change_type == 'purchase',
            CardTransaction.leave_change > 0
        ).scalar() or 0
        card.total_leave_quota = total_quota

    def _refresh_used_leave(self, card: LearningCard):
        """刷新已使用请假次数（独立方法，便于复用）"""
        used = self.db.query(func.sum(CardTransaction.leave_change)).filter(
            CardTransaction.card_id == card.id,
            CardTransaction.change_type == 'attendance',
            CardTransaction.leave_change < 0
        ).scalar() or 0
        card.used_leave = abs(used)

    # ========== 统一业务接口 ==========
    def record_purchase(self, order: Order, gift_hours: int = 0):
        card = self._get_or_create_card(order.student_id, order.course_id, order.class_id)
        self._add_card_transaction(
            card_id=card.id,
            change_type='purchase',
            paid_hours_change=order.purchase_hours,
            amount_change=order.payable_amount,
            gift_hours_change=gift_hours,
            leave_change=order.leave_limit_count if order.leave_limit == '限制次数' else 0,
            reason=f"订单 {order.order_no}",
            order_id=order.id,
            occurred_at=order.created_at.date()
        )
        if order.validity_type == 'days' and order.validity_value:
            try:
                days = int(order.validity_value)
                if days > 0:
                    self._add_validity_log(
                        card_id=card.id,
                        change_days=days,
                        reason=f"订单 {order.order_no} 有效期",
                        source_type='order',
                        source_id=order.id,
                        occurred_at=order.created_at.date()
                    )
            except:
                pass
        # ★ 关键：强制全量刷新卡片
        self._refresh_card(order.student_id, order.course_id, force_full=True)
        return card

    def record_attendance(self, attendance: Attendance, paid_deduct: int, gift_deduct: int, leave_deduct: int):
        course_id = attendance.class_.course_id
        card = self._get_or_create_card(attendance.student_id, course_id, attendance.class_id)
        self._add_card_transaction(
            card_id=card.id,
            change_type='attendance',
            paid_hours_change=-paid_deduct,
            gift_hours_change=-gift_deduct,
            amount_change=-attendance.deduct_amount,
            leave_change=-leave_deduct,
            reason=attendance.status,
            attendance_id=attendance.id,
            occurred_at=attendance.created_at.date() if attendance.created_at else date.today()
        )
        self._refresh_card(attendance.student_id, course_id)
        return attendance

    def delete_attendance_transaction(self, attendance_id: int):
        txn = self.db.query(CardTransaction).filter(
            CardTransaction.attendance_id == attendance_id
        ).first()
        if txn:
            card = self.db.query(LearningCard).get(txn.card_id)
            self.db.delete(txn)
            self.db.flush()
            if card:
                self._refresh_card(card.student_id, card.course_id)
        return txn

    def record_temporary_enroll(self, student_id: int, course_id: int, class_id: int,
                                deduct_hours: int = 1, reason: str = '临时插班'):
        from app.utils import deduct_from_orders_with_detail
        card = self._get_or_create_card(student_id, course_id, class_id)
        gift, paid, amount = deduct_from_orders_with_detail(
            self.db, student_id, course_id, deduct_hours, deduct_gift=True
        )
        self._add_card_transaction(
            card_id=card.id,
            change_type='attendance',
            paid_hours_change=-paid,
            gift_hours_change=-gift,
            amount_change=-amount,
            reason=reason,
            occurred_at=date.today()
        )
        self._refresh_card(student_id, course_id)
        return {"paid": paid, "gift": gift, "amount": amount}

    def record_transfer_out(self, card: LearningCard, hours: int, amount: float, reason: str = ''):
        self._add_card_transaction(
            card_id=card.id,
            change_type='transfer_out',
            paid_hours_change=-hours,
            amount_change=-amount,
            reason=reason,
            occurred_at=date.today()
        )
        self._refresh_card(card.student_id, card.course_id)
        return True

    def record_transfer_in(self, card: LearningCard, hours: int, amount: float,
                        reason: str = '', validity_days: int = 0):
        self._add_card_transaction(
            card_id=card.id,
            change_type='transfer_in',
            paid_hours_change=hours,
            amount_change=amount,
            reason=reason,
            occurred_at=date.today()
        )
        if validity_days and validity_days > 0:
            self._add_validity_log(
                card_id=card.id,
                change_days=validity_days,
                reason=f"转课时增加有效期 {validity_days} 天",
                source_type='transfer',
                occurred_at=date.today()
            )
        self._refresh_card(card.student_id, card.course_id)
        return True

    def record_custom_adjust(self, student_id: int, course_id: int, change_type: str,
                             paid_hours: int = 0, gift_hours: int = 0, amount: float = 0.0,
                             reason: str = '', class_id: int = None, occurred_date: date = None,
                             teacher_id: int = None):
        card = self._get_or_create_card(student_id, course_id, class_id)
        self._add_card_transaction(
            card_id=card.id,
            change_type=change_type,
            paid_hours_change=paid_hours,
            gift_hours_change=gift_hours,
            amount_change=amount,
            reason=reason,
            occurred_at=occurred_date or date.today()
        )
        self._refresh_card(student_id, course_id)
        return True

    def record_refund(self, card: LearningCard, refund_hours: int, refund_amount: float, reason: str = ''):
        self._add_card_transaction(
            card_id=card.id,
            change_type='refund',
            paid_hours_change=-refund_hours,
            amount_change=-refund_amount,
            reason=reason,
            occurred_at=date.today()
        )
        self._refresh_card(card.student_id, card.course_id)
        return True

    def extend_validity(self, student_id: int, course_id: int, extend_days: int, reason: str = ''):
        card = self._get_or_create_card(student_id, course_id)
        self._add_validity_log(
            card_id=card.id,
            change_days=extend_days,
            reason=reason or f"手动延长有效期 {extend_days} 天",
            source_type='manual',
            occurred_at=date.today()
        )
        self._refresh_card(student_id, course_id)
        return card