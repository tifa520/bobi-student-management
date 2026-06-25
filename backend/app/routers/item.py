from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from typing import Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Item, InventoryTransaction, InventoryBatch, MiscFee, Student, IntegralRecord, SystemConfig
import json
import uuid
from sqlalchemy import select, func
from app.services.image_service import ImageService

router = APIRouter()


def deduct_cost_by_fifo(db: Session, item_id: int, sell_quantity: int) -> dict:
    """
    按 FIFO 原则扣除库存批次成本（带行锁，防止并发超卖）
    """
    # 使用 FOR UPDATE 行锁，防止其他事务同时修改同一批次
    batches = db.query(InventoryBatch).filter(
        InventoryBatch.item_id == item_id,
        InventoryBatch.remaining_quantity > 0
    ).order_by(InventoryBatch.purchase_date.asc()).with_for_update().all()
    
    if not batches:
        return {"total_cost": 0, "details": []}
    
    remaining = sell_quantity
    total_cost = 0
    cost_details = []
    
    for batch in batches:
        if remaining <= 0:
            break
        
        take = min(remaining, batch.remaining_quantity)
        cost = take * batch.unit_cost
        total_cost += cost
        
        cost_details.append({
            "batch_id": batch.id,
            "batch_no": batch.batch_no,
            "quantity": take,
            "unit_cost": batch.unit_cost,
            "cost": cost
        })
        
        # 直接更新（已加锁，安全）
        batch.remaining_quantity -= take
        remaining -= take
    
    # 立即 flush 但不 commit（让事务持有锁直到提交）
    db.flush()
    
    return {
        "total_cost": total_cost,
        "details": cost_details
    }


def _extract_relative_path_from_url(url: str) -> str:
    """将 /media/xxx/yyy.jpg 转换为 xxx/yyy.jpg"""
    if url and url.startswith('/media/'):
        return url[7:]  # 去掉 '/media/'
    return url


@router.get("/items")
def get_items(
    item_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Item)
    if item_type:
        query = query.filter(Item.item_type == item_type)
    if category:
        query = query.filter(Item.category == category)
    if keyword:
        query = query.filter(Item.name.contains(keyword))
    total = query.count()
    items = query.order_by(Item.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {"code": 0, "data": {"items": [i.to_dict() for i in items], "total": total}}


@router.post("/items")
def create_item(data: dict, db: Session = Depends(get_db)):
    if 'image_url' in data and data['image_url']:
        data['image_url'] = _extract_relative_path_from_url(data['image_url'])
    item = Item(
        name=data['name'],
        category=data.get('category', '其他'),
        item_type=data['item_type'],
        points=data.get('points', 0),
        sale_price=data.get('sale_price', 0),
        cost_price=data.get('cost_price', 0),
        stock=data.get('stock', 0),
        unit=data.get('unit', '个'),
        status=data.get('status', '上架'),
        image_url=data.get('image_url'),
        remark=data.get('remark', ''),
        pay_option=data.get('pay_option', 'both')
    )
    db.add(item)
    db.flush()
    
    # 如果初始库存 > 0，创建初始批次
    if item.stock > 0:
        batch_no = f"INIT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        batch = InventoryBatch(
            item_id=item.id,
            batch_no=batch_no,
            quantity=item.stock,
            remaining_quantity=item.stock,
            unit_cost=item.cost_price,
            total_cost=item.stock * item.cost_price,
            purchase_date=datetime.now(),
            remark="初始库存"
        )
        db.add(batch)
        db.flush()
        
        # 记录入库流水
        txn = InventoryTransaction(
            item_id=item.id,
            batch_id=batch.id,
            transaction_type='purchase',
            quantity=item.stock,
            before_stock=0,
            after_stock=item.stock,
            unit_price=item.cost_price,
            total_amount=item.stock * item.cost_price,
            remark="初始库存入库"
        )
        db.add(txn)
    
    db.commit()
    db.refresh(item)
    return {"code": 0, "data": {"id": item.id}}


@router.put("/items/{item_id}")
def update_item(item_id: int, data: dict, db: Session = Depends(get_db)):
    if 'image_url' in data and data['image_url']:
        data['image_url'] = _extract_relative_path_from_url(data['image_url'])
    item = db.query(Item).get(item_id)
    if not item:
        raise HTTPException(404, "物品不存在")
    allowed = ['name', 'category', 'item_type', 'points', 'sale_price', 'cost_price', 'unit', 'status', 'image_url', 'remark', 'pay_option']
    for field in allowed:
        if field in data:
            setattr(item, field, data[field])
    db.commit()
    return {"code": 0, "message": "更新成功"}


@router.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).get(item_id)
    if not item:
        raise HTTPException(404, "物品不存在")
    if item.stock > 0:
        raise HTTPException(400, "仍有库存，无法删除")
    # 检查是否有未消耗的批次
    batches = db.query(InventoryBatch).filter(InventoryBatch.item_id == item_id, InventoryBatch.remaining_quantity > 0).first()
    if batches:
        raise HTTPException(400, "仍有批次库存，无法删除")
    db.delete(item)
    db.commit()
    return {"code": 0, "message": "已删除"}


@router.post("/items/{item_id}/stock-in")
def stock_in(
    item_id: int,
    quantity: int = Query(..., gt=0),
    unit_price: float = Query(0.0),
    remark: str = Query(''),
    purchase_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    item = db.query(Item).get(item_id)
    if not item:
        raise HTTPException(404, "物品不存在")
    
    # 生成批次号
    batch_no = f"{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    # 解析采购日期
    if purchase_date:
        p_date = datetime.strptime(purchase_date, "%Y-%m-%d")
    else:
        p_date = datetime.now()
    
    # 创建批次
    batch = InventoryBatch(
        item_id=item_id,
        batch_no=batch_no,
        quantity=quantity,
        remaining_quantity=quantity,
        unit_cost=unit_price,
        total_cost=quantity * unit_price,
        purchase_date=p_date,
        remark=remark
    )
    db.add(batch)
    db.flush()
    
    # 更新库存
    before = item.stock
    item.stock += quantity
    after = item.stock
    
    # 记录库存流水
    txn = InventoryTransaction(
        item_id=item_id,
        batch_id=batch.id,
        transaction_type='purchase',
        quantity=quantity,
        before_stock=before,
        after_stock=after,
        unit_price=unit_price,
        total_amount=quantity * unit_price,
        remark=remark
    )
    db.add(txn)
    
    db.commit()
    return {"code": 0, "message": "入库成功", "data": {"stock": item.stock, "batch_no": batch_no}}


@router.post("/items/{item_id}/sell")
def sell_item(
    item_id: int,
    student_id: int = Query(...),
    quantity: int = Query(..., gt=0),
    paid_amount: float = Query(0),
    points_used: int = Query(0),
    payment_method: str = Query('wechat'),
    db: Session = Depends(get_db)
):
    """销售商品（带事务锁）"""
    # 使用事务块，确保原子性
    try:
        # 1. 加锁查询商品信息
        item = db.query(Item).filter(Item.id == item_id).with_for_update().first()
        if not item or item.item_type != 'sale':
            raise HTTPException(400, "物品不是销售商品")
        if item.stock < quantity:
            raise HTTPException(400, f"库存不足，当前库存 {item.stock}")
        
        # 2. 加锁查询学员信息
        student = db.query(Student).filter(Student.id == student_id).with_for_update().first()
        if not student:
            raise HTTPException(404, "学员不存在")
        
        # 3. 支付方式校验
        total_amount = item.sale_price * quantity
        pay_option = item.pay_option
        
        if pay_option == 'cash' and points_used > 0:
            raise HTTPException(400, "该物品只允许现金购买")
        if pay_option == 'points' and paid_amount > 0:
            raise HTTPException(400, "该物品只允许积分兑换")
        
        # 获取当前积分汇率
        rate_config = db.query(SystemConfig).filter(SystemConfig.key == 'exchange_rate').first()
        current_rate = int(rate_config.value) if rate_config else 10
        points_value = points_used / current_rate
        total_paid = paid_amount + points_value
        
        if total_paid > total_amount:
            raise HTTPException(400, f"支付总额超出商品价格 {total_amount} 元")
        
        # 确定支付方式标签
        if points_used > 0 and paid_amount > 0:
            payment_type = 'mix'
        elif points_used > 0:
            payment_type = 'points'
        else:
            payment_type = payment_method
        
        # 4. 扣积分（加锁学员行）
        if points_used > 0:
            if student.total_integral < points_used:
                raise HTTPException(400, f"积分不足，需要 {points_used} 积分")
            student.total_integral -= points_used
            integral_record = IntegralRecord(
                student_id=student.id,
                change_amount=-points_used,
                reason=f"购买【{item.name}】抵扣 {points_value:.2f} 元"
            )
            db.add(integral_record)
        
        # 5. FIFO 成本计算（内部已加锁）
        cost_result = deduct_cost_by_fifo(db, item_id, quantity)
        total_cost = cost_result["total_cost"]
        cost_details = cost_result["details"]
        
        # 6. 扣库存（行锁已持有）
        before = item.stock
        item.stock -= quantity
        after = item.stock
        
        # 7. 记录主销售流水
        first_batch_id = cost_details[0]["batch_id"] if cost_details else None
        txn = InventoryTransaction(
            item_id=item_id,
            batch_id=first_batch_id,
            transaction_type='sale',
            quantity=-quantity,
            before_stock=before,
            after_stock=after,
            unit_price=item.sale_price,
            total_amount=total_amount,
            cost_of_goods_sold=total_cost,
            payment_method=payment_type,
            remark=f"现金 {paid_amount} 元，积分 {points_used} 分，成本 {total_cost} 元"
        )
        db.add(txn)
        
        # 8. 记录每个批次的成本扣除明细
        for detail in cost_details:
            batch = db.query(InventoryBatch).filter(
                InventoryBatch.id == detail["batch_id"]
            ).with_for_update().first()
            if batch:
                batch_cost_txn = InventoryTransaction(
                    item_id=item_id,
                    batch_id=detail["batch_id"],
                    transaction_type='cost_deduct',
                    quantity=-detail["quantity"],
                    before_stock=batch.remaining_quantity + detail["quantity"],
                    after_stock=batch.remaining_quantity,
                    unit_price=detail["unit_cost"],
                    total_amount=-detail["cost"],
                    remark=f"批次 {detail['batch_no']} 扣除成本"
                )
                db.add(batch_cost_txn)
        
        # 9. 杂费记录
        misc = MiscFee(
            student_id=student_id,
            fee_type='item_sale',
            source_id=0,
            description=f"购买 {item.name} x{quantity}",
            amount=total_amount,
            paid_amount=paid_amount,
            points_used=points_used,
            exchange_rate=current_rate,
            status='paid' if total_paid >= total_amount else 'partial',
            payment_method=payment_type,
            paid_at=datetime.now() if paid_amount > 0 or points_used > 0 else None
        )
        db.add(misc)
        
        # 提交事务（释放所有行锁）
        db.commit()
        
        return {"code": 0, "message": "销售成功", "data": {"cost": total_cost, "profit": total_amount - total_cost}}
    
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"销售失败: {e}")
        raise HTTPException(500, f"销售失败: {str(e)}")

@router.get("/items/{item_id}/batches")
def get_item_batches(
    item_id: int,
    db: Session = Depends(get_db)
):
    item = db.query(Item).get(item_id)
    if not item:
        raise HTTPException(404, "物品不存在")
    
    batches = db.query(InventoryBatch).filter(
        InventoryBatch.item_id == item_id
    ).order_by(InventoryBatch.purchase_date.desc()).all()
    
    result = []
    for b in batches:
        result.append({
            "id": b.id,
            "batch_no": b.batch_no,
            "quantity": b.quantity,
            "remaining_quantity": b.remaining_quantity,
            "unit_cost": b.unit_cost,
            "total_cost": b.total_cost,
            "purchase_date": b.purchase_date.strftime('%Y-%m-%d %H:%M:%S'),
            "remark": b.remark
        })
    return {"code": 0, "data": result}


@router.get("/inventory/records")
def inventory_records(
    item_id: Optional[int] = Query(None),
    transaction_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(InventoryTransaction)
    if item_id:
        query = query.filter(InventoryTransaction.item_id == item_id)
    if transaction_type:
        query = query.filter(InventoryTransaction.transaction_type == transaction_type)
    if start_date:
        query = query.filter(InventoryTransaction.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        query = query.filter(InventoryTransaction.created_at <= datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))
    
    total = query.count()
    records = query.order_by(InventoryTransaction.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    result = []
    for r in records:
        item = db.query(Item).get(r.item_id)
        batch = db.query(InventoryBatch).get(r.batch_id) if r.batch_id else None
        
        # 显示数量为正数
        display_quantity = abs(r.quantity) if r.quantity < 0 else r.quantity
        
        result.append({
            "id": r.id,
            "item_name": item.name if item else '',
            "item_image": ImageService.get_url(item.image_url) if item else '',
            "batch_no": batch.batch_no if batch else '',
            "transaction_type": r.transaction_type,
            "quantity": display_quantity,
            "before_stock": r.before_stock,
            "after_stock": r.after_stock,
            "unit_price": r.unit_price,
            "total_amount": r.total_amount,
            "cost_of_goods_sold": r.cost_of_goods_sold,
            "payment_method": getattr(r, 'payment_method', ''),
            "remark": r.remark,
            "created_at": str(r.created_at)
        })
    return {"code": 0, "data": {"items": result, "total": total}}


@router.post("/inventory/sales/{sale_id}/refund")
def refund_item_sale(
    sale_id: int,
    refund_amount: float = Query(0),
    refund_points: int = Query(0),
    payment_method: str = Query('原路返回'),
    db: Session = Depends(get_db)
):
    sale = db.query(MiscFee).get(sale_id)
    if not sale or sale.fee_type != 'item_sale':
        raise HTTPException(404, "销售记录不存在")
    if sale.amount <= 0:
        raise HTTPException(400, "不是正数销售记录，无法退款")

    # 查找对应的销售库存交易
    sale_txn = db.query(InventoryTransaction).filter(
        InventoryTransaction.transaction_type == 'sale',
        InventoryTransaction.total_amount == sale.amount,
        InventoryTransaction.remark.contains(str(sale.id))
    ).first()
    if not sale_txn:
        sale_txn = db.query(InventoryTransaction).filter(
            InventoryTransaction.transaction_type == 'sale',
            InventoryTransaction.remark.like(f'%{sale.description}%')
        ).first()

    max_cash_refund = sale.paid_amount
    if refund_amount > max_cash_refund:
        raise HTTPException(400, f"现金退款不能超过实付金额 {max_cash_refund}")

    max_points_refund = sale.points_used - (sale.points_refunded if hasattr(sale, 'points_refunded') else 0)
    if refund_points > max_points_refund:
        raise HTTPException(400, f"积分退款不能超过已用积分 {max_points_refund}")

    student = db.query(Student).get(sale.student_id)
    if not student:
        raise HTTPException(404, "学员不存在")

    # 现金退款
    if refund_amount > 0:
        refund_misc = MiscFee(
            student_id=sale.student_id,
            fee_type='refund',
            source_id=sale.id,
            description=sale.description + " 退款",
            amount=-refund_amount,
            paid_amount=refund_amount,
            status='paid',
            payment_method=payment_method,
            paid_at=datetime.now()
        )
        db.add(refund_misc)
        sale.paid_amount -= refund_amount
        if sale.paid_amount <= 0:
            sale.status = 'refunded'
        else:
            sale.status = 'partial'

    # 积分退款
    if refund_points > 0:
        student.total_integral += refund_points
        integral_record = IntegralRecord(
            student_id=sale.student_id,
            change_amount=refund_points,
            reason=f"购买商品退款返还积分"
        )
        db.add(integral_record)
        if hasattr(sale, 'points_refunded'):
            sale.points_refunded = (sale.points_refunded or 0) + refund_points

    # 库存回滚
    if sale_txn and sale_txn.batch_id:
        batch = db.query(InventoryBatch).get(sale_txn.batch_id)
        if batch:
            # 恢复批次数量
            batch.remaining_quantity += -sale_txn.quantity
            
            refund_txn = InventoryTransaction(
                item_id=sale_txn.item_id,
                batch_id=batch.id,
                transaction_type='refund',
                quantity=-sale_txn.quantity,
                before_stock=batch.remaining_quantity - (-sale_txn.quantity),
                after_stock=batch.remaining_quantity,
                unit_price=sale_txn.unit_price,
                total_amount=sale_txn.total_amount,
                remark=f"销售退款 {refund_amount} 元"
            )
            db.add(refund_txn)
            
            # 恢复总库存
            item = db.query(Item).get(sale_txn.item_id)
            if item:
                item.stock += -sale_txn.quantity

    db.commit()
    return {"code": 0, "message": f"退款成功，现金 {refund_amount} 元，积分 {refund_points} 分"}


@router.post("/items/{item_id}/exchange")
def exchange_gift(
    item_id: int,
    student_id: int = Query(...),
    quantity: int = Query(..., gt=0),
    db: Session = Depends(get_db)
):
    item = db.query(Item).get(item_id)
    if not item or item.item_type != 'gift':
        raise HTTPException(400, "物品不是兑换礼品")
    if item.stock < quantity:
        raise HTTPException(400, f"库存不足，当前库存 {item.stock}")
    if item.points <= 0:
        raise HTTPException(400, "礼品未设置积分")

    student = db.query(Student).get(student_id)
    if not student:
        raise HTTPException(404, "学员不存在")
    total_points = item.points * quantity
    if student.total_integral < total_points:
        raise HTTPException(400, f"积分不足，需要 {total_points} 积分")

    student.total_integral -= total_points
    integral_record = IntegralRecord(
        student_id=student_id,
        change_amount=-total_points,
        reason=f"兑换 {item.name} x{quantity}"
    )
    db.add(integral_record)

    # 扣库存
    before = item.stock
    item.stock -= quantity
    after = item.stock
    
    # 记录库存流水
    txn = InventoryTransaction(
        item_id=item_id,
        transaction_type='exchange',
        quantity=-quantity,
        before_stock=before,
        after_stock=after,
        unit_price=0,
        total_amount=0,
        remark=f"学员兑换 {item.name}"
    )
    db.add(txn)

    # 记录杂费
    misc = MiscFee(
        student_id=student_id,
        fee_type='item_sale',
        source_id=0,
        description=f"积分兑换 {item.name} x{quantity}",
        amount=0,
        paid_amount=0,
        points_used=total_points,
        status='paid',
        payment_method='积分',
        paid_at=datetime.now()
    )
    db.add(misc)

    db.commit()
    return {"code": 0, "message": "兑换成功"}


def _item_to_dict(item):
    return {
        "id": item.id,
        "name": item.name,
        "category": item.category,
        "item_type": item.item_type,
        "points": item.points,
        "sale_price": item.sale_price,
        "cost_price": item.cost_price,
        "stock": item.stock,
        "unit": item.unit,
        "status": item.status,
        "image_url": ImageService.get_url(item.image_url),  # 返回完整 URL
        "remark": item.remark,
        "pay_option": item.pay_option,
        "created_at": str(item.created_at)
    }
Item.to_dict = _item_to_dict