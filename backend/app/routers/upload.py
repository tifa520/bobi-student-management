from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils import get_current_user
from app.services.bg_config import save_bg_url, get_bg_url
from app.services.image_service import ImageService
import os

router = APIRouter()


# ========== 登录背景图接口 ==========
@router.get("/login-bg")
async def get_login_bg():
    url = get_bg_url()
    return {"code": 0, "data": {"url": url}}


@router.post("/login-bg")
async def upload_login_bg(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        get_current_user(request, db)
    except:
        raise HTTPException(401, "未授权")

    relative_path = await ImageService.save(file, "login_bg")
    full_url = ImageService.get_url(relative_path)
    save_bg_url(full_url, db)
    return {"code": 0, "data": {"url": full_url}}


# ========== 商品图片接口 ==========
@router.post("/item-image")
async def upload_item_image(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        get_current_user(request, db)
    except:
        raise HTTPException(401, "未授权")

    relative_path = await ImageService.save(file, "item_image")
    full_url = ImageService.get_url(relative_path)
    return {"code": 0, "data": {"url": full_url}}


# ========== 通用图片上传（兼容旧接口） ==========
@router.post("/image")
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    category: str = "item_image",
    db: Session = Depends(get_db)
):
    """通用图片上传接口，支持指定 category"""
    try:
        get_current_user(request, db)
    except:
        raise HTTPException(401, "未授权")

    relative_path = await ImageService.save(file, category)
    full_url = ImageService.get_url(relative_path)
    return {"code": 0, "data": {"url": full_url}}