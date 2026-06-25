from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models import Student, Order, Refund, EnrollmentHistory, LearningCard, Course, Class, UserSession, CardTransaction
from jose import jwt
from app.config import SECRET_KEY, ALGORITHM

router = APIRouter()


def get_current_user_from_token(request: Request, db: Session) -> str:
    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        token = token[7:]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                return "管理员"
        except:
            pass
    return "系统"


@router.get("/student/{student_id}/change-logs")
def get_student_change_logs(
    student_id: int,
    request: Request,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    student = db.query(Student).get(student_id)
    if not student:
        raise HTTPException(404, "学员不存在")

    operator = get_current_user_from_token(request, db)

    changes = []

    # 1. 订单变更
    orders = db.query(Order).options(joinedload(Order.course)).filter(
        Order.student_id == student_id,
        Order.is_invalid == False
    ).all()
    for o in orders:
        course_name = o.course.name if o.course else '未知课程'
        if o.enroll_type == "新报":
            change_type = "报名"
            icon = "ShoppingCart"
            color = "#36b459"
        elif o.enroll_type == "续报":
            change_type = "续报"
            icon = "ShoppingCart"
            color = "#409eff"
        elif o.enroll_type == "扩科":
            change_type = "扩科"
            icon = "ShoppingCart"
            color = "#e6a23c"
        elif o.enroll_type == "尾款补费":
            change_type = "尾款补费"
            icon = "Money"
            color = "#e6a23c"
        else:
            change_type = "报名"
            icon = "ShoppingCart"
            color = "#36b459"
        changes.append({
            "id": f"order_{o.id}",
            "type": change_type,
            "category": "order" if o.enroll_type != "尾款补费" else "payment",
            "title": f"{change_type}课程：{course_name}" if o.enroll_type != "尾款补费" else "尾款补费",
            "description": f"购买{o.purchase_hours}课时，应付￥{o.payable_amount}，实付￥{o.total_paid}" if o.enroll_type != "尾款补费" else f"补缴尾款￥{o.total_paid}",
            "operator": operator,
            "created_at": str(o.created_at),
            "icon": icon,
            "color": color
        })

    # 2. 课时变更（从 card_transactions 聚合）
    # 获取该学员的所有课程卡片 ID
    cards = db.query(LearningCard.id).filter(LearningCard.student_id == student_id).subquery()
    transactions = db.query(CardTransaction).filter(
        CardTransaction.card_id.in_(cards),
        CardTransaction.change_type.in_(['custom_add', 'custom_sub', 'gift_add', 'gift_sub', 'transfer_in', 'transfer_out'])
    ).order_by(CardTransaction.created_at.desc()).all()

    type_map = {
        'custom_add': {'title': '增加课时', 'icon': 'Plus', 'color': '#67c23a', 'category': 'custom'},
        'custom_sub': {'title': '减少课时', 'icon': 'Minus', 'color': '#f56c6c', 'category': 'custom'},
        'gift_add': {'title': '增加赠送课时', 'icon': 'Present', 'color': '#e6a23c', 'category': 'custom'},
        'gift_sub': {'title': '减少赠送课时', 'icon': 'Present', 'color': '#f56c6c', 'category': 'custom'},
        'transfer_in': {'title': '转入课时', 'icon': 'Right', 'color': '#67c23a', 'category': 'transfer'},
        'transfer_out': {'title': '转出课时', 'icon': 'Left', 'color': '#f56c6c', 'category': 'transfer'}
    }

    for txn in transactions:
        card = db.query(LearningCard).get(txn.card_id)
        if not card:
            continue
        course = db.query(Course).get(card.course_id)
        course_name = course.name if course else ''
        info = type_map.get(txn.change_type, {'title': '课时变更', 'icon': 'Edit', 'color': '#909399', 'category': 'custom'})
        hours = (txn.paid_hours_change or 0) + (txn.gift_hours_change or 0)
        amount = txn.amount_change or 0.0
        changes.append({
            "id": f"txn_{txn.id}",
            "type": info['title'],
            "category": info['category'],
            "title": f"{info['title']}：{course_name}",
            "description": f"变动{hours}课时，金额￥{amount}，原因：{txn.reason or '无'}",
            "operator": "管理员",
            "created_at": str(txn.created_at),
            "icon": info['icon'],
            "color": info['color']
        })

    # 3. 退费记录
    refunds = db.query(Refund).options(joinedload(Refund.course)).filter(
        Refund.student_id == student_id
    ).all()
    for r in refunds:
        course_name = r.course.name if r.course else ''
        changes.append({
            "id": f"refund_{r.id}",
            "type": "退费",
            "category": "refund",
            "title": f"退费：{course_name}",
            "description": f"退款￥{r.refund_amount}，原因：{r.reason or '无'}",
            "operator": operator,
            "created_at": str(r.created_at),
            "icon": "Money",
            "color": "#f56c6c"
        })

    # 4. 分班/转班/退班记录
    histories = db.query(EnrollmentHistory).options(
        joinedload(EnrollmentHistory.from_class),
        joinedload(EnrollmentHistory.to_class),
        joinedload(EnrollmentHistory.course)
    ).filter(
        EnrollmentHistory.student_id == student_id
    ).all()
    for h in histories:
        from_class_name = h.from_class.name if h.from_class else '未分班'
        to_class_name = h.to_class.name if h.to_class else '未分班'
        course_name = h.course.name if h.course else ''
        if h.action == 'assign':
            action = "分班"
            description = f"分配到「{to_class_name}」"
        elif h.action == 'transfer':
            action = "转班"
            description = f"从「{from_class_name}」转到「{to_class_name}」"
        else:
            action = "退班"
            description = f"从「{from_class_name}」退班"
        changes.append({
            "id": f"history_{h.id}",
            "type": action,
            "category": "class",
            "title": f"{action} - {course_name}",
            "description": description,
            "operator": operator,
            "created_at": str(h.created_at),
            "icon": "School",
            "color": "#409eff"
        })

    # 5. 结业记录
    cards = db.query(LearningCard).options(joinedload(LearningCard.course)).filter(
        LearningCard.student_id == student_id,
        LearningCard.status == 'graduated'
    ).all()
    for card in cards:
        course_name = card.course.name if card.course else ''
        changes.append({
            "id": f"graduate_{card.id}",
            "type": "结业",
            "category": "status",
            "title": f"课程结业：{course_name}",
            "description": f"剩余课时{card.remaining_paid_hours}，剩余金额￥{card.remaining_amount}已清零",
            "operator": operator,
            "created_at": str(card.updated_at),
            "icon": "Finished",
            "color": "#909399"
        })

    # 按时间排序
    changes.sort(key=lambda x: x['created_at'], reverse=True)

    # 日期筛选
    if start_date:
        changes = [c for c in changes if c['created_at'].split(' ')[0] >= start_date]
    if end_date:
        changes = [c for c in changes if c['created_at'].split(' ')[0] <= end_date]

    return {"code": 0, "data": changes[:limit], "total": len(changes)}