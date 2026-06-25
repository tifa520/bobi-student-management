from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
import os
import base64
from io import BytesIO
from PIL import Image

from app.database import get_db
from app.models import User, UserSession, Role
from app.utils import verify_password, create_access_token, hash_password, get_current_user, create_refresh_token, decode_refresh_token
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.middleware.auth import add_to_blacklist
from app.services.image_service import ImageService
from app.middleware.rate_limit import limiter

router = APIRouter(tags=["认证"])


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    role_id: int
    email: str = None
    phone: str = None


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None


# ============================================================
# ★ 新增：创建管理员账号相关请求模型
# ============================================================
class AdminCreateRequest(BaseModel):
    username: str
    password: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


# ============================================================
# ★ 新增：管理员检查与创建接口
# ============================================================

@router.get("/has-admin")
def has_admin(db: Session = Depends(get_db)):
    """检查系统中是否已存在管理员账号"""
    admin_count = db.query(User).filter(User.role_id == 1).count()
    return {"code": 0, "data": {"has_admin": admin_count > 0}}


@router.post("/create-admin")
def create_admin(data: AdminCreateRequest, db: Session = Depends(get_db)):
    """创建管理员账号（仅当系统中无管理员时可用）"""
    # 1. 检查是否已有管理员
    admin_count = db.query(User).filter(User.role_id == 1).count()
    if admin_count > 0:
        raise HTTPException(400, "系统中已存在管理员账号，无法创建")
    
    # 2. 检查用户名是否已存在
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(400, "用户名已存在")
    
    # 3. 确保 role_id=1 的角色存在（超级管理员）
    admin_role = db.query(Role).filter(Role.id == 1).first()
    if not admin_role:
        # 创建默认超级管理员角色
        admin_role = Role(
            id=1,
            name="超级管理员",
            permissions=["*"]
        )
        db.add(admin_role)
        db.flush()
    
    # 4. 创建管理员用户
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        name=data.name or data.username,
        email=data.email,
        phone=data.phone,
        role_id=1,
        is_enabled=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "code": 0,
        "data": {
            "id": user.id,
            "username": user.username,
            "name": user.name
        },
        "message": "管理员账号创建成功"
    }


# ============================================================
# 原有接口（保持不变）
# ============================================================

@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "用户名或密码错误")
    if not user.is_enabled:
        raise HTTPException(403, "用户已被禁用")

    user.last_login = datetime.now()

    access_token = create_access_token({"sub": str(user.id), "username": user.username, "role": user.role.name if user.role else "admin"})
    refresh_token = create_refresh_token({"sub": str(user.id), "username": user.username})

    session = UserSession(
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(session)
    db.commit()

    # ★ 修改：返回完整头像 URL
    user_avatar = ImageService.get_url(user.avatar) if user.avatar else ""

    return {
        "code": 0,
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "name": user.name,
                "role": user.role.name if user.role else "admin",
                "username": user.username,
                "phone": user.phone or "",
                "avatar": user_avatar
            }
        }
    }


@router.post("/refresh")
def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = decode_refresh_token(data.refresh_token)
    if not payload:
        raise HTTPException(401, "无效的刷新令牌")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(401, "令牌格式错误")

    session = db.query(UserSession).filter(
        UserSession.token == data.refresh_token,
        UserSession.expires_at > datetime.now()
    ).first()

    if not session:
        raise HTTPException(401, "刷新令牌已失效")

    user = db.query(User).get(int(user_id))
    if not user or not user.is_enabled:
        raise HTTPException(401, "用户不存在或已禁用")

    new_access_token = create_access_token({"sub": str(user.id), "username": user.username, "role": user.role.name if user.role else "admin"})

    return {
        "code": 0,
        "data": {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    }


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        token = token[7:]
        add_to_blacklist(token, datetime.now() + timedelta(days=7), db, reason="用户主动登出")
        db.query(UserSession).filter(UserSession.token == token).delete()
        db.commit()
    return {"code": 0, "message": "已登出"}


@router.post("/change-password")
def change_password(data: ChangePasswordRequest, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(400, "原密码错误")
    user.password_hash = hash_password(data.new_password)
    db.commit()

    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        token = token[7:]
        add_to_blacklist(token, datetime.now() + timedelta(days=7), db, reason="修改密码后强制登出")

    return {"code": 0, "message": "密码已更新，请重新登录"}


@router.post("/users")
def create_user(data: UserCreate, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if current_user.role_id != 1:
        raise HTTPException(403, "无权限创建用户")

    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(400, "用户名已存在")

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        name=data.name,
        email=data.email,
        phone=data.phone,
        role_id=data.role_id,
        is_enabled=True
    )
    db.add(user)
    db.commit()
    return {"code": 0, "message": "用户创建成功"}


@router.get("/me")
def get_current_user_info(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return {
        "code": 0,
        "data": {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "email": user.email,
            "phone": user.phone or "",
            "avatar": ImageService.get_url(user.avatar),
            "role": user.role.name if user.role else "",
            "role_id": user.role_id,
            "is_enabled": user.is_enabled
        }
    }


@router.put("/me")
def update_current_user(data: UserUpdateRequest, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if data.name is not None:
        user.name = data.name
    if data.phone is not None:
        user.phone = data.phone
    db.commit()
    return {"code": 0, "message": "更新成功"}


@router.post("/avatar")
async def upload_user_avatar(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    
    # 删除旧头像文件
    if user.avatar:
        ImageService.delete(user.avatar)
    
    # 保存新头像
    relative_path = await ImageService.save(file, "user_avatar")
    user.avatar = relative_path
    db.commit()
    
    full_url = ImageService.get_url(relative_path)
    return {"code": 0, "data": {"avatar_url": full_url}, "message": "上传成功"}