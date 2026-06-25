import uuid
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from app.models import Order, StudentCourse, Attendance, Class, LearningCard, Schedule, CardTransaction
from dateutil.relativedelta import relativedelta
from passlib.context import CryptContext
from jose import jwt
from datetime import timedelta
from fastapi import Request
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
import secrets
import logging

logger = logging.getLogger(__name__)


def generate_student_uuid():
    return str(uuid.uuid4())


def calculate_age(birth_date: date) -> int:
    if not birth_date:
        return 0
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def generate_order_no(db: Session) -> str:
    import uuid
    from datetime import datetime
    prefix = datetime.now().strftime("%Y%m%d")
    unique_id = str(uuid.uuid4()).replace('-', '')[-8:]
    order_no = f"{prefix}{unique_id}"
    existing = db.query(Order).filter(Order.order_no == order_no).first()
    if existing:
        return generate_order_no(db)
    return order_no


def calculate_payable_amount(total_price, discount_mode, discount_rate, direct_reduction):
    if discount_mode == 'none' or not discount_mode:
        return total_price, 0.0
    elif discount_mode == 'direct':
        payable = total_price - direct_reduction
        discount = direct_reduction
    elif discount_mode == 'discount':
        payable = total_price * (discount_rate / 10)
        discount = total_price - payable
    elif discount_mode == 'discount_then_direct':
        after_discount = total_price * (discount_rate / 10)
        payable = after_discount - direct_reduction
        discount = total_price - payable
    elif discount_mode == 'direct_then_discount':
        after_direct = total_price - direct_reduction
        payable = after_direct * (discount_rate / 10)
        discount = total_price - payable
    else:
        payable = total_price
        discount = 0.0
    return round(payable, 2), round(discount, 2)


def deduct_from_orders_with_detail(db: Session, student_id: int, course_id: int, deduct_hours: int,
                                   deduct_gift: bool = True, strict_gift_only: bool = False) -> tuple:
    """
    返回 (赠送课时扣除数, 付费课时扣除数, 扣除金额)
    """
    if deduct_hours <= 0:
        return 0, 0, 0.0

    card = db.query(LearningCard).filter(
        LearningCard.student_id == student_id,
        LearningCard.course_id == course_id
    ).first()
    if not card:
        return 0, 0, 0.0

    if strict_gift_only:
        if card.remaining_gift_hours < deduct_hours:
            raise HTTPException(400, f"赠送课时不足，剩余 {card.remaining_gift_hours}，需要扣除 {deduct_hours}")
        return deduct_hours, 0, 0.0

    if deduct_gift:
        gift_take = min(deduct_hours, card.remaining_gift_hours)
        paid_take = deduct_hours - gift_take
    else:
        gift_take = 0
        paid_take = deduct_hours

    amount = 0.0

    if paid_take > 0:
        orders = db.query(Order).filter(
            Order.student_id == student_id,
            Order.course_id == course_id,
            Order.is_active == True,
            Order.is_invalid == False,
            Order.enroll_type.notin_(['尾款补费', '转课时'])
        ).order_by(Order.created_at.asc()).all()

        remaining = paid_take
        for order in orders:
            if remaining <= 0:
                break

            consumed = db.query(func.sum(CardTransaction.paid_hours_change)).filter(
                CardTransaction.order_id == order.id,
                CardTransaction.change_type.in_(['attendance', 'custom_sub', 'transfer_out'])
            ).scalar() or 0
            consumed = -consumed if consumed < 0 else 0
            available = order.purchase_hours - consumed
            if available <= 0:
                continue

            take = min(remaining, available)
            if order.actual_unit_price > 0:
                unit_price = order.actual_unit_price
            else:
                unit_price = order.payable_amount / order.purchase_hours if order.purchase_hours > 0 else 0
            amount += take * unit_price
            remaining -= take

    return gift_take, paid_take, amount


def calculate_refund_info(db: Session, student_id: int, course_id: int, refund_hours: int) -> dict:
    from app.models import CardTransaction
    from sqlalchemy import func

    card = db.query(LearningCard).filter(
        LearningCard.student_id == student_id,
        LearningCard.course_id == course_id
    ).first()
    if not card:
        raise HTTPException(404, "课程账户不存在")

    remaining_hours = card.remaining_paid_hours or 0
    remaining_amount = card.remaining_amount or 0.0

    if refund_hours <= 0:
        raise HTTPException(400, "退款课时必须大于0")
    if refund_hours > remaining_hours:
        raise HTTPException(400, f"退款课时不能超过剩余课时 {remaining_hours}")

    orders = db.query(Order).filter(
        Order.student_id == student_id,
        Order.course_id == course_id,
        Order.is_active == True,
        Order.is_invalid == False,
        Order.enroll_type.notin_(['尾款补费', '转课时'])
    ).order_by(Order.created_at.asc()).all()

    total_purchased_hours = sum(o.purchase_hours for o in orders)
    total_purchased_amount = sum(o.payable_amount for o in orders)

    order_consumed_hours = {}
    for order in orders:
        consumed = db.query(func.sum(CardTransaction.paid_hours_change)).filter(
            CardTransaction.order_id == order.id,
            CardTransaction.change_type.in_(['attendance', 'custom_sub', 'transfer_out'])
        ).scalar() or 0
        consumed = -consumed if consumed < 0 else 0
        order_consumed_hours[order.id] = consumed

    remaining_to_refund = refund_hours
    refund_amount = 0.0
    for order in orders:
        if remaining_to_refund <= 0:
            break
        available = order.purchase_hours - order_consumed_hours[order.id]
        if available <= 0:
            continue
        take = min(remaining_to_refund, available)
        unit_price = order.payable_amount / order.purchase_hours if order.purchase_hours > 0 else 0
        refund_amount += take * unit_price
        remaining_to_refund -= take

    total_consumed_hours = sum(order_consumed_hours.values())
    total_consumed_amount = 0.0
    for order in orders:
        unit_price = order.payable_amount / order.purchase_hours if order.purchase_hours > 0 else 0
        total_consumed_amount += order_consumed_hours[order.id] * unit_price

    total_arrears = 0.0
    for order in orders:
        if order.payable_amount > order.total_paid:
            total_arrears += order.payable_amount - order.total_paid

    if refund_amount > total_arrears:
        actual_refund = refund_amount - total_arrears
        can_refund = True
        message = ""
    else:
        actual_refund = 0
        can_refund = False
        message = f"预计退款金额 ¥{refund_amount:.2f} 小于等于尾款 ¥{total_arrears:.2f}，无法退款"

    after_remaining_hours = remaining_hours - refund_hours
    after_remaining_amount = max(0, remaining_amount - actual_refund)

    return {
        "total_purchased_hours": total_purchased_hours,
        "total_purchased_amount": round(total_purchased_amount, 2),
        "total_consumed_hours": total_consumed_hours,
        "total_consumed_amount": round(total_consumed_amount, 2),
        "remaining_hours": remaining_hours,
        "remaining_amount": round(remaining_amount, 2),
        "refund_hours": refund_hours,
        "refund_amount": round(refund_amount, 2),
        "after_remaining_hours": after_remaining_hours,
        "after_remaining_amount": round(after_remaining_amount, 2),
        "arrears": round(total_arrears, 2),
        "actual_refund_amount": round(actual_refund, 2),
        "can_refund": can_refund,
        "message": message
    }


# ========== 安全相关函数 ==========
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception as e:
        logger.error(f"解码令牌时发生未知错误: {e}")
        return None

def get_current_user(request: Request, db: Session):
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(401, "未提供认证令牌")
    token = token[7:]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "令牌无效或已过期")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(401, "令牌格式错误")
    from app.models import User
    user = db.query(User).get(int(user_id))
    if not user or not user.is_enabled:
        raise HTTPException(401, "用户不存在或已禁用")
    return user

def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_refresh_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except jwt.JWTError:
        return None

def generate_secure_secret_key():
    return secrets.token_hex(32)