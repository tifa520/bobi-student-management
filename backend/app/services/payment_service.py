from datetime import date
from sqlalchemy.orm import Session
from app.models import PaymentLog, Order


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
    
    def record_payment(self, order_id: int, amount: float, payment_method: str, 
                       payment_type: str, remark: str = ''):
        """记录支付流水"""
        payment_log = PaymentLog(
            order_id=order_id,
            amount=amount,
            payment_method=payment_method,
            payment_type=payment_type,
            remark=remark,
            occurred_at=date.today()
        )
        self.db.add(payment_log)
        self.db.flush()
        
        # 更新订单已付金额
        order = self.db.query(Order).get(order_id)
        if order:
            order.total_paid += amount
            order.paid_amount = order.total_paid
        
        return payment_log
    
    def get_order_payment_history(self, order_id: int):
        """获取订单支付历史"""
        return self.db.query(PaymentLog).filter(
            PaymentLog.order_id == order_id
        ).order_by(PaymentLog.occurred_at).all()