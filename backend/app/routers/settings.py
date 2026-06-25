from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import SystemConfig
from pydantic import BaseModel
from typing import Any, List
import json

router = APIRouter()

# ========== 响应模型 ==========
class ConfigUpdate(BaseModel):
    value: Any

# ========== 支付方式 ==========
@router.get("/payment-methods")
def get_payment_methods(db: Session = Depends(get_db)):
    """获取支付方式列表"""
    config = db.query(SystemConfig).filter(SystemConfig.key == 'payment_methods').first()
    methods = json.loads(config.value) if config else ["微信支付", "支付宝", "现金", "银行转账"]
    return {"code": 0, "data": methods}

@router.put("/config/payment_methods")
def update_payment_methods(data: ConfigUpdate, db: Session = Depends(get_db)):
    """更新支付方式列表"""
    config = db.query(SystemConfig).filter(SystemConfig.key == 'payment_methods').first()
    if not config:
        config = SystemConfig(key='payment_methods', value=json.dumps(data.value), description='支付方式列表')
        db.add(config)
    else:
        config.value = json.dumps(data.value, ensure_ascii=False)
    db.commit()
    return {"code": 0, "message": "更新成功"}

# ========== 商品类别 ==========
@router.get("/item-categories")
def get_item_categories(db: Session = Depends(get_db)):
    """获取商品类别列表"""
    config = db.query(SystemConfig).filter(SystemConfig.key == 'item_categories').first()
    categories = json.loads(config.value) if config else ["教材", "教具", "礼品", "办公用品", "其他"]
    return {"code": 0, "data": categories}

@router.put("/config/item_categories")
def update_item_categories(data: ConfigUpdate, db: Session = Depends(get_db)):
    """更新商品类别列表"""
    config = db.query(SystemConfig).filter(SystemConfig.key == 'item_categories').first()
    if not config:
        config = SystemConfig(key='item_categories', value=json.dumps(data.value), description='商品类别列表')
        db.add(config)
    else:
        config.value = json.dumps(data.value, ensure_ascii=False)
    db.commit()
    return {"code": 0, "message": "更新成功"}

# ========== 积分汇率 ==========
@router.get("/exchange-rate")
def get_exchange_rate(db: Session = Depends(get_db)):
    config = db.query(SystemConfig).filter(SystemConfig.key == 'exchange_rate').first()
    rate = int(config.value) if config else 10
    return {"code": 0, "data": rate}

# 兼容旧版前端可能使用的路径
@router.get("/settings/exchange-rate")
def get_exchange_rate_legacy(db: Session = Depends(get_db)):
    return get_exchange_rate(db)

@router.put("/config/exchange_rate")
def update_exchange_rate(data: ConfigUpdate, db: Session = Depends(get_db)):
    """更新积分汇率"""
    config = db.query(SystemConfig).filter(SystemConfig.key == 'exchange_rate').first()
    if not config:
        config = SystemConfig(key='exchange_rate', value=str(data.value), description='积分兑换汇率')
        db.add(config)
    else:
        config.value = str(data.value)
    db.commit()
    return {"code": 0, "message": "保存成功"}