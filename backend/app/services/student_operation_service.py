from datetime import date, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import Student, LearningCard, Class, Order, EnrollmentHistory, StudentCourse, Refund, CardTransaction, ValidityLog
from app.services.transaction_service import TransactionService
from app.services.card_service import CardService
from app.utils import deduct_from_orders_with_detail, calculate_refund_info, generate_order_no


class StudentOperationService:
    def __init__(self, db: Session):
        self.db = db
        self.tx_service = TransactionService(db)
        self.card_service = CardService(db)

    # ========== 分班 ==========
    def assign_class(self, student_id: int, course_id: int, class_id: int):
        card = self._get_card(student_id, course_id)
        if card.status != 'active':
            raise HTTPException(400, "课程状态不允许分班")
        if card.class_id:
            raise HTTPException(400, "该课程已有班级，请使用转班功能")
        card.class_id = class_id
        self._update_student_course_class(student_id, course_id, class_id)
        self._record_history(student_id, course_id, None, class_id, 'assign')
        return True

    # ========== 转班 ==========
    def transfer_class(self, student_id: int, course_id: int, to_class_id: int):
        card = self._get_card(student_id, course_id)
        if card.status != 'active':
            raise HTTPException(400, "课程状态不允许转班")
        from_class_id = card.class_id
        card.class_id = to_class_id
        self._update_student_course_class(student_id, course_id, to_class_id)
        self._record_history(student_id, course_id, from_class_id, to_class_id, 'transfer')
        return True

    # ========== 退班 ==========
    def drop_class(self, student_id: int, course_id: int):
        card = self._get_card(student_id, course_id)
        if card.status != 'active':
            raise HTTPException(400, "课程状态不允许退班")
        from_class_id = card.class_id
        card.class_id = None
        self._update_student_course_class(student_id, course_id, None)
        self._record_history(student_id, course_id, from_class_id, None, 'drop')
        return True

    # ========== 增减付费课时 ==========
    def adjust_hours(self, student_id: int, course_id: int, change_hours: int, reason: str,
                occurrence_date: date = None, performance: bool = False, teacher_id: int = None):
        """
        增减付费课时
        """
        if change_hours == 0:
            raise HTTPException(400, "变动课时不能为0")
        occ_date = occurrence_date or date.today()
        teacher_id = teacher_id if performance else None

        card = self._get_card(student_id, course_id)

        if change_hours > 0:
            # 增加付费课时
            self.tx_service.record_custom_adjust(
                student_id, course_id, 'custom_add',
                paid_hours=change_hours, reason=reason,
                occurred_date=occ_date, teacher_id=teacher_id
            )
        else:
            # 减少付费课时
            hours_to_sub = abs(change_hours)
            if card.remaining_paid_hours < hours_to_sub:
                raise HTTPException(400, f"剩余付费课时不足，剩余 {card.remaining_paid_hours} 课时")
            
            # 从订单 FIFO 扣除课时和金额
            from app.utils import deduct_from_orders_with_detail
            gift, paid, amount = deduct_from_orders_with_detail(
                self.db, student_id, course_id, hours_to_sub, deduct_gift=False
            )
            
            self.tx_service.record_custom_adjust(
                student_id, course_id, 'custom_sub',
                paid_hours=-paid, gift_hours=-gift, amount=-amount,
                reason=reason, occurred_date=occ_date, teacher_id=teacher_id
            )
        
        # 确保事务提交（如果外层没有自动 commit）
        self.db.commit()
        return True

    # ========== 增减赠送课时 ==========
    def adjust_gift_hours(self, student_id: int, course_id: int, change_hours: int, reason: str,
                      occurrence_date: date = None, performance: bool = False, teacher_id: int = None):
        """
        增减赠送课时
        """
        if change_hours == 0:
            raise HTTPException(400, "变动课时不能为0")
        occ_date = occurrence_date or date.today()
        teacher_id = teacher_id if performance else None

        card = self._get_card(student_id, course_id)
        
        if change_hours > 0:
            change_type = 'gift_add'
        else:
            change_type = 'gift_sub'
            # 检查剩余赠送课时是否足够
            if card.remaining_gift_hours < abs(change_hours):
                raise HTTPException(400, f"剩余赠送课时不足，剩余 {card.remaining_gift_hours} 课时")
        
        self.tx_service.record_custom_adjust(
            student_id, course_id, change_type,
            gift_hours=change_hours, reason=reason,
            occurred_date=occ_date, teacher_id=teacher_id
        )
        
        self.db.commit()
        return True

    # ========== 转课时 ==========
    def transfer_hours(self, student_id: int, from_course_id: int, to_course_id: int,
                        transfer_hours: int, reason: str, to_hours: int = None, to_amount: float = None,
                        make_up_diff: bool = False, pay_amount: float = 0, payment_method: str = '微信',
                        to_class_id: int = None, validity_days: int = None):
        
        if transfer_hours <= 0:
            raise HTTPException(400, "转出课时必须大于0")

        from_card = self._get_card(student_id, from_course_id)
        if from_card.remaining_paid_hours < transfer_hours:
            raise HTTPException(400, f"剩余付费课时不足，剩余 {from_card.remaining_paid_hours} 课时")

        # 计算转出金额（从订单FIFO）
        gift, paid, deducted_amount = deduct_from_orders_with_detail(
            self.db, student_id, from_course_id, transfer_hours, deduct_gift=False
        )
        
        # 记录转出流水
        self.tx_service.record_transfer_out(from_card, transfer_hours, deducted_amount, reason)

        # 处理转入
        to_hours = to_hours or transfer_hours
        to_amount = to_amount or deducted_amount

        to_card = self.tx_service._get_or_create_card(student_id, to_course_id, to_class_id)
        self.tx_service.record_transfer_in(to_card, to_hours, to_amount, reason, validity_days or 0)

        if to_class_id and not to_card.class_id:
            to_card.class_id = to_class_id

        # 补差价逻辑
        diff = to_amount - deducted_amount
        if make_up_diff and diff > 0 and pay_amount > 0:
            # 记录补款（自定义增加金额）
            self.tx_service.record_custom_adjust(
                student_id, to_course_id, 'payment',
                amount=pay_amount, reason=f"转课时补差价 {pay_amount} 元"
            )
            # 创建补费订单（可选）
            repay_order = Order(
                order_no=generate_order_no(self.db),
                student_id=student_id,
                course_id=to_course_id,
                class_id=to_class_id,
                enroll_type='转课时补费',
                purchase_hours=0,
                unit_price=0,
                total_price=0,
                discount_amount=0,
                payable_amount=pay_amount,
                actual_unit_price=0,
                paid_amount=pay_amount,
                total_paid=pay_amount,
                payment_method=payment_method,
                is_active=True,
                is_invalid=False,
                remark=f"转课时补差价 {pay_amount} 元，原转出课程: {from_course_id}"
            )
            self.db.add(repay_order)
            self.db.flush()
            self.tx_service._add_payment_log(
                order_id=repay_order.id,
                amount=pay_amount,
                payment_method=payment_method,
                payment_type='transfer_diff',
                remark=f"转课时补差价 {pay_amount} 元",
                occurred_at=date.today()
            )

        # 刷新两张卡片
        self.tx_service._refresh_card(student_id, from_course_id)
        self.tx_service._refresh_card(student_id, to_course_id)
        
        # 提交事务
        self.db.commit()
        return True

    # ========== 退费 ==========
    def refund(self, student_id: int, course_id: int, refund_hours: int, reason: str,
            refund_method: str = '微信'):
        import traceback
        try:
            self.tx_service._refresh_card(student_id, course_id)
            card = self._get_card(student_id, course_id)
            if card.status not in ['active', 'suspended']:
                raise HTTPException(400, "当前状态不允许退费")

            info = calculate_refund_info(self.db, student_id, course_id, refund_hours)
            if not info.get("can_refund", False):
                raise HTTPException(400, info.get("message", "无法退款"))
            if info["actual_refund_amount"] <= 0:
                raise HTTPException(400, "实际可退金额为0，无法退款")

            if info["arrears"] > 0 and info["refund_amount"] > info["actual_refund_amount"]:
                deduct_arrears = info["refund_amount"] - info["actual_refund_amount"]
                remaining_deduct = deduct_arrears
                orders = self.db.query(Order).filter(
                    Order.student_id == student_id,
                    Order.course_id == course_id,
                    Order.is_active == True,
                    Order.is_invalid == False,
                    Order.enroll_type.notin_(['尾款补费', '转课时'])
                ).order_by(Order.created_at.asc()).all()
                for order in orders:
                    if remaining_deduct <= 0:
                        break
                    due = order.payable_amount - order.total_paid
                    if due <= 0:
                        continue
                    pay = min(remaining_deduct, due)
                    order.total_paid += pay
                    order.paid_amount = order.total_paid
                    remaining_deduct -= pay
                    if pay > 0:
                        self.tx_service._add_payment_log(
                            order_id=order.id,
                            amount=pay,
                            payment_method=refund_method,
                            payment_type='repay',
                            remark=f"退费抵扣尾款 {pay} 元",
                            occurred_at=date.today()
                        )
                        repay_order = Order(
                            order_no=generate_order_no(self.db),
                            student_id=student_id,
                            course_id=course_id,
                            class_id=None,
                            enroll_type='尾款补费',
                            purchase_hours=0,
                            unit_price=0,
                            total_price=0,
                            discount_amount=0,
                            payable_amount=0,
                            actual_unit_price=0,
                            paid_amount=pay,
                            total_paid=pay,
                            is_active=True,
                            is_invalid=False,
                            parent_order_id=order.id,
                            remark=f"退费抵扣尾款 {pay} 元，原订单 {order.order_no}"
                        )
                        self.db.add(repay_order)

            self.tx_service.record_refund(card, refund_hours, info["actual_refund_amount"], reason)
            if card.remaining_paid_hours <= 0 and card.remaining_amount <= 0:
                card.status = 'refunded'
                card.class_id = None

            refund_record = Refund(
                student_id=student_id, course_id=course_id, refund_type='课时退费',
                refund_amount=info["actual_refund_amount"], refund_method=refund_method,
                reason=reason, remark=f"退费{refund_hours}课时"
            )
            self.db.add(refund_record)
            return True
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, f"退费处理失败: {str(e)}")

    # ========== 结业 ==========
    def graduate(self, student_id: int, course_id: int):
        card = self._get_card(student_id, course_id)
        if card.status != 'active':
            raise HTTPException(400, "当前状态不允许结业")

        if card.remaining_paid_hours > 0 or card.remaining_amount > 0 or card.remaining_gift_hours > 0:
            self.tx_service.record_custom_adjust(
                student_id, course_id, 'graduation',
                paid_hours=-card.remaining_paid_hours,
                gift_hours=-card.remaining_gift_hours,
                amount=-card.remaining_amount,
                reason="课程结业清零"
            )

        orders = self.db.query(Order).filter(
            Order.student_id == student_id, Order.course_id == course_id,
            Order.is_active == True, Order.is_invalid == False
        ).all()
        for o in orders:
            o.is_invalid = True
            o.is_active = False

        card.class_id = None
        card.status = 'graduated'
        student_course = self.db.query(StudentCourse).filter(
            StudentCourse.student_id == student_id, StudentCourse.course_id == course_id
        ).first()
        if student_course:
            student_course.class_id = None
            student_course.status = 'graduated'

        other_active_cards = self.db.query(LearningCard).filter(
            LearningCard.student_id == student_id,
            LearningCard.status == 'active'
        ).count()
        if other_active_cards == 0:
            student = self.db.query(Student).get(student_id)
            if student:
                student.is_archived = True
        return True

    # ========== 停课 / 取消停课 ==========
    def suspend(self, student_id: int, course_id: int, start_date: date, end_date: date, reason: str = ''):
        card = self._get_card(student_id, course_id)
        if card.status != 'active':
            raise HTTPException(400, "当前状态不允许停课")
        if start_date > end_date:
            raise HTTPException(400, "开始日期不能晚于结束日期")
        card.suspended_start = start_date
        card.suspended_end = end_date
        card.status = 'suspended'
        # 同时更新 StudentCourse 表（可选）
        student_course = self.db.query(StudentCourse).filter(
            StudentCourse.student_id == student_id, StudentCourse.course_id == course_id
        ).first()
        if student_course:
            student_course.suspended_start = start_date
            student_course.suspended_end = end_date
        # 确保提交事务（由调用方 commit）
        return True

    def cancel_suspend(self, student_id: int, course_id: int):
        card = self._get_card(student_id, course_id)
        card.suspended_start = None
        card.suspended_end = None
        card.status = 'active'
        # 同时更新 StudentCourse
        sc = self.db.query(StudentCourse).filter(
            StudentCourse.student_id == student_id,
            StudentCourse.course_id == course_id
        ).first()
        if sc:
            sc.suspended_start = None
            sc.suspended_end = None
        return True

    # ========== 辅助方法 ==========
    def _get_card(self, student_id: int, course_id: int) -> LearningCard:
        card = self.db.query(LearningCard).filter(
            LearningCard.student_id == student_id, LearningCard.course_id == course_id
        ).first()
        if not card:
            raise HTTPException(404, "课程账户不存在")
        return card

    def _update_student_course_class(self, student_id, course_id, class_id):
        sc = self.db.query(StudentCourse).filter(
            StudentCourse.student_id == student_id, StudentCourse.course_id == course_id
        ).first()
        if sc:
            sc.class_id = class_id

    def _record_history(self, student_id, course_id, from_class_id, to_class_id, action):
        history = EnrollmentHistory(
            student_id=student_id, course_id=course_id,
            from_class_id=from_class_id, to_class_id=to_class_id, action=action
        )
        self.db.add(history)