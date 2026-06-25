from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.utils import decode_token
from app.config import ENABLE_AUTH_MIDDLEWARE, WHITELIST_PATHS
import traceback
from loguru import logger
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import TokenBlacklist
from datetime import datetime
from app.services.blacklist_cache import is_in_blacklist_cache, add_to_blacklist_cache


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not ENABLE_AUTH_MIDDLEWARE:
            return await call_next(request)

        if any(request.url.path == path or request.url.path.startswith(path) for path in WHITELIST_PATHS):
            return await call_next(request)

        if request.url.path.startswith('/uploads/') or request.url.path.startswith('/static/'):
            return await call_next(request)

        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            logger.warning(f"未提供认证令牌: {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"code": 401, "message": "未提供认证令牌"}
            )

        token = token[7:]
        
        # 先检查缓存
        if is_in_blacklist_cache(token):
            logger.warning(f"缓存黑名单中的令牌: {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"code": 401, "message": "令牌已失效，请重新登录"}
            )

        # 再检查数据库（可能缓存未命中）
        if await self._is_token_blacklisted(token):
            logger.warning(f"数据库黑名单中的令牌: {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"code": 401, "message": "令牌已失效，请重新登录"}
            )

        try:
            payload = decode_token(token)
            if not payload:
                logger.warning(f"无效令牌: {request.url.path}")
                return JSONResponse(
                    status_code=401,
                    content={"code": 401, "message": "无效令牌或已过期"}
                )

            request.state.user_id = int(payload.get("sub"))
            request.state.username = payload.get("username", "")
            request.state.user_role = payload.get("role", "admin")
        except Exception as e:
            logger.error(f"认证中间件异常: {e}\n{traceback.format_exc()}")
            return JSONResponse(
                status_code=401,
                content={"code": 401, "message": "认证失败"}
            )

        return await call_next(request)
    
    async def _is_token_blacklisted(self, token: str) -> bool:
        """检查 token 是否在黑名单中（数据库）"""
        db = SessionLocal()
        try:
            result = db.query(TokenBlacklist).filter(
                TokenBlacklist.token == token,
                TokenBlacklist.expires_at > datetime.now()
            ).first()
            if result:
                # 查到后也加入缓存，避免重复查库
                add_to_blacklist_cache(token)
            return result is not None
        except Exception as e:
            logger.error(f"检查黑名单失败: {e}")
            return False
        finally:
            db.close()


def add_to_blacklist(token: str, expires_at: datetime, db: Session, 
                     token_type: str = 'access', reason: str = ''):
    """将 token 加入黑名单（持久化 + 缓存）"""
    try:
        existing = db.query(TokenBlacklist).filter(
            TokenBlacklist.token == token
        ).first()
        if existing:
            return
        
        blacklisted = TokenBlacklist(
            token=token,
            token_type=token_type,
            expires_at=expires_at,
            revoked_at=datetime.now(),
            reason=reason
        )
        db.add(blacklisted)
        db.commit()
        # 加入缓存
        add_to_blacklist_cache(token)
        logger.info(f"Token 已加入黑名单: {token[:20]}..., 原因: {reason}")
    except Exception as e:
        logger.error(f"添加 token 到黑名单失败: {e}")
        db.rollback()


def clean_expired_blacklist(db: Session):
    """清理过期的黑名单记录（可定时执行）"""
    try:
        deleted = db.query(TokenBlacklist).filter(
            TokenBlacklist.expires_at < datetime.now()
        ).delete()
        db.commit()
        if deleted > 0:
            logger.info(f"清理了 {deleted} 条过期的黑名单记录")
    except Exception as e:
        logger.error(f"清理黑名单失败: {e}")
        db.rollback()