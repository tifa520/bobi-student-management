from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import json

from app.database import get_db
from app.models import Student, Item, InventoryBatch, InventoryTransaction, IntegralRecord, SystemConfig, SalesOrder, SalesOrderItem
from app.utils import get_current_user
from loguru import logger
from app.services.image_service import ImageService

router = APIRouter()

# ---------- 请求模型 ----------
class OrderItem(BaseModel):
    item_id: int
    quantity: int

class PaymentItem(BaseModel):
    type: str          # 'cash' or 'points'
    amount: float = 0.0
    points: int = 0
    method: str        # 微信支付、支付宝、现金、积分等

class SalesOrderCreate(BaseModel):
    student_id: int
    items: List[OrderItem]
    payments: List[PaymentItem]

# ---------- FIFO 成本扣除（保持不变）----------
def deduct_cost_by_fifo(db: Session, item_id: int, sell_quantity: int) -> dict:
    batches = db.query(InventoryBatch).filter(
        InventoryBatch.item_id == item_id,
        InventoryBatch.remaining_quantity > 0
    ).order_by(InventoryBatch.purchase_date.asc()).with_for_update().all()
    if not batches:
        return {"total_cost": 0, "details": []}
    remaining = sell_quantity
    total_cost = 0
    details = []
    for batch in batches:
        if remaining <= 0:
            break
        take = min(remaining, batch.remaining_quantity)
        cost = take * batch.unit_cost
        total_cost += cost
        details.append({
            "batch_id": batch.id,
            "batch_no": batch.batch_no,
            "quantity": take,
            "unit_cost": batch.unit_cost,
            "cost": cost
        })
        batch.remaining_quantity -= take
        remaining -= take
    db.flush()
    return {"total_cost": total_cost, "details": details}

# ---------- 销售下单 ----------
@router.post("/sales/order")
def create_sales_order(order_data: SalesOrderCreate, request: Request, db: Session = Depends(get_db)):
    try:
        # 获取操作人（可选）
        try:
            get_current_user(request, db)
        except:
            pass

        # 1. 获取学员并加行锁
        student = db.query(Student).filter(Student.id == order_data.student_id).with_for_update().first()
        if not student:
            raise HTTPException(404, "学员不存在")

        # 2. 获取积分汇率
        rate_config = db.query(SystemConfig).filter(SystemConfig.key == 'exchange_rate').first()
        exchange_rate = int(rate_config.value) if rate_config else 10

        # 3. 校验商品库存，计算总金额
        total_amount = 0.0
        items_detail = []          # 存储商品详情，用于后续流水和 JSON
        for it in order_data.items:
            item = db.query(Item).filter(Item.id == it.item_id).with_for_update().first()
            if not item or item.item_type != 'sale':
                raise HTTPException(400, f"商品 {it.item_id} 不是销售商品")
            if item.stock < it.quantity:
                raise HTTPException(400, f"商品 {item.name} 库存不足")
            item_total = item.sale_price * it.quantity
            total_amount += item_total
            items_detail.append({
                "item": item,
                "quantity": it.quantity,
                "unit_price": item.sale_price,
                "total": item_total,
                "stock_before": item.stock
            })

        # 4. 解析支付方式，计算现金总额和积分总额
        total_cash = 0.0
        total_points = 0
        payment_details = []       # 存储支付明细，用于 JSON
        for p in order_data.payments:
            if p.type == 'cash':
                total_cash += p.amount
                payment_details.append({"method": p.method, "type": "cash", "amount": p.amount})
            elif p.type == 'points':
                total_points += p.points
                payment_details.append({"method": p.method, "type": "points", "points": p.points})
            else:
                raise HTTPException(400, f"不支持的支付类型: {p.type}")

        # 5. 校验支付总额
        total_paid_value = total_cash + total_points / exchange_rate
        if abs(total_paid_value - total_amount) > 0.01:
            raise HTTPException(400, f"支付总额 {total_paid_value:.2f} ≠ 应付总额 {total_amount:.2f}")

        # 6. 校验积分余额
        if total_points > student.total_integral:
            raise HTTPException(400, f"积分不足，需要 {total_points}，可用 {student.total_integral}")

        # 7. 扣减积分（如有）
        if total_points > 0:
            student.total_integral -= total_points
            db.add(IntegralRecord(
                student_id=student.id,
                change_amount=-total_points,
                reason=f"购买商品抵扣 {total_points/exchange_rate:.2f} 元"
            ))

        # 8. 处理每个商品：扣库存、记库存流水、FIFO成本
        for d in items_detail:
            item = d["item"]
            qty = d["quantity"]
            # 扣库存
            item.stock -= qty
            # 成本 FIFO
            cost_res = deduct_cost_by_fifo(db, item.id, qty)
            # 销售库存流水
            db.add(InventoryTransaction(
                item_id=item.id,
                transaction_type='sale',
                quantity=-qty,
                before_stock=d["stock_before"],
                after_stock=item.stock,
                unit_price=item.sale_price,
                total_amount=d["total"],
                cost_of_goods_sold=cost_res["total_cost"],
                payment_method=",".join([p.method for p in order_data.payments]),
                remark=f"销售 {item.name} x{qty}"
            ))
            # 批次成本流水
            for cost in cost_res["details"]:
                db.add(InventoryTransaction(
                    item_id=item.id,
                    batch_id=cost["batch_id"],
                    transaction_type='cost_deduct',
                    quantity=-cost["quantity"],
                    before_stock=0,
                    after_stock=0,
                    unit_price=cost["unit_cost"],
                    total_amount=-cost["cost"],
                    remark=f"批次 {cost['batch_no']} 扣除成本"
                ))

        # 9. 构建 JSON 存储字段
        payment_json = json.dumps(payment_details, ensure_ascii=False)
        # 生成订单号
        order_no = f"SALE_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 10. 创建销售订单主表
        sales_order = SalesOrder(
            order_no=order_no,
            student_id=student.id,
            total_amount=total_amount,
            paid_amount=total_cash,
            used_points=total_points,
            status='paid',
            payment_details=payment_json,
            remark=""  # 可存额外备注
        )
        db.add(sales_order)
        db.flush()  # 获取自增 id

        # 11. 创建销售订单商品明细
        for d in items_detail:
            order_item = SalesOrderItem(
                order_id=sales_order.id,
                item_id=d["item"].id,
                quantity=d["quantity"],
                unit_price=d["unit_price"],
                subtotal=d["total"]
            )
            db.add(order_item)

        db.commit()
        return {
            "code": 0,
            "message": "下单成功",
            "data": {"order_no": order_no}
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"销售订单创建失败: {str(e)}")
        raise HTTPException(500, f"下单失败: {str(e)}")

# ---------- 订单列表 ----------
@router.get("/sales/orders")
def get_sales_orders(
    request: Request,
    search: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    # 权限：仅管理员可查看所有订单
    try:
        current_user = get_current_user(request, db)
        is_admin = current_user.role.name == 'admin' if current_user.role else False
    except:
        is_admin = False
    if not is_admin:
        return {"code": 0, "data": {"items": [], "total": 0}}

    query = db.query(SalesOrder).join(Student, SalesOrder.student_id == Student.id)
    if search:
        query = query.filter(
            (SalesOrder.order_no.contains(search)) | (Student.name.contains(search))
        )
    if status:
        query = query.filter(SalesOrder.status == status)
    if start_date:
        query = query.filter(SalesOrder.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        query = query.filter(SalesOrder.created_at <= datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))

    total = query.count()
    orders = query.order_by(SalesOrder.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()

    result = []
    for order in orders:
        student = db.query(Student).get(order.student_id)
        # 解析支付明细 JSON
        payment_details = []
        if order.payment_details:
            try:
                payment_details = json.loads(order.payment_details) if isinstance(order.payment_details, str) else order.payment_details
            except:
                payment_details = []
        result.append({
            "id": order.id,
            "order_no": order.order_no,
            "student_id": order.student_id,
            "student_avatar": ImageService.get_url(student.avatar) if student else '',
            "student_name": student.name if student else '',
            "student_phone": student.phone if student else '',
            "total_amount": order.total_amount,
            "paid_amount": order.paid_amount,
            "used_points": order.used_points,
            "status": order.status,
            "payment_details": payment_details,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat() if order.updated_at else None
        })
    return {"code": 0, "data": {"items": result, "total": total}}

# ---------- 订单详情 ----------
@router.get("/sales/orders/{order_id}")
def get_sales_order_detail(order_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        get_current_user(request, db)
    except:
        pass
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    student = db.query(Student).get(order.student_id)
    # 获取商品明细
    items = db.query(SalesOrderItem).filter(SalesOrderItem.order_id == order.id).all()
    items_list = [{
        "item_id": it.item_id,
        "item_name": it.item.name,
        "quantity": it.quantity,
        "unit_price": it.unit_price,
        "subtotal": it.subtotal
    } for it in items]
    # 解析支付明细
    payment_details = []
    if order.payment_details:
        try:
            payment_details = json.loads(order.payment_details) if isinstance(order.payment_details, str) else order.payment_details
        except:
            payment_details = []
    return {
        "code": 0,
        "data": {
            "id": order.id,
            "order_no": order.order_no,
            "student_id": order.student_id,
            "student_name": student.name if student else '',
            "student_phone": student.phone if student else '',
            "total_amount": order.total_amount,
            "paid_amount": order.paid_amount,
            "used_points": order.used_points,
            "status": order.status,
            "payment_details": payment_details,
            "items": items_list,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat() if order.updated_at else None
        }
    }

# ---------- 订单退款 ----------
@router.post("/sales/orders/{order_id}/refund")
def refund_sales_order(order_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        current_user = get_current_user(request, db)
    except:
        raise HTTPException(401, "未授权")

    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).with_for_update().first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.status != 'paid':
        raise HTTPException(400, "只有已支付的订单才能退款")
    if order.status == 'refunded':
        raise HTTPException(400, "订单已经退款过了")

    # 获取商品明细（用于恢复库存）
    items = db.query(SalesOrderItem).filter(SalesOrderItem.order_id == order.id).all()

    try:
        # 1. 退回积分
        if order.used_points > 0:
            student = db.query(Student).filter(Student.id == order.student_id).with_for_update().first()
            if student:
                student.total_integral += order.used_points
                db.add(IntegralRecord(
                    student_id=student.id,
                    change_amount=order.used_points,
                    reason=f"订单退款返还积分 (订单号: {order.order_no})"
                ))

        # 2. 恢复库存
        for item in items:
            db_item = db.query(Item).filter(Item.id == item.item_id).with_for_update().first()
            if db_item:
                before = db_item.stock
                db_item.stock += item.quantity
                db.add(InventoryTransaction(
                    item_id=db_item.id,
                    transaction_type='refund',
                    quantity=item.quantity,
                    before_stock=before,
                    after_stock=db_item.stock,
                    unit_price=item.unit_price,
                    total_amount=item.subtotal,
                    remark=f"订单退款恢复库存，原订单 {order.order_no}"
                ))

        # 3. 更新订单状态
        order.status = 'refunded'

        db.commit()
        return {"code": 0, "message": "退款成功"}
    except Exception as e:
        db.rollback()
        logger.error(f"退款失败: {str(e)}")
        raise HTTPException(500, f"退款失败: {str(e)}")