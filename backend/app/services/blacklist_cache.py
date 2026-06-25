from datetime import datetime
from loguru import logger
from app.services.cache_service import cache
from app.database import SessionLocal
from app.models import TokenBlacklist

BLACKLIST_CACHE_PREFIX = "blacklist:"
# 7天缓存，与 Refresh Token 有效期对齐
BLACKLIST_CACHE_TTL = 7 * 24 * 3600  

def _check_db(token: str) -> bool:
    """查数据库（内部方法）"""
    db = SessionLocal()
    try:
        result = db.query(TokenBlacklist).filter(
            TokenBlacklist.token == token,
            TokenBlacklist.expires_at > datetime.now()
        ).first()
        return result is not None
    except Exception as e:
        logger.error(f"数据库黑名单查询失败: {e}")
        return False  # 降级放行需谨慎，这里为了高可用
    finally:
        db.close()

def is_in_blacklist_cache(token: str) -> bool:
    # 1. 查缓存
    try:
        cached = cache.get(f"{BLACKLIST_CACHE_PREFIX}{token}")
        if cached is True:
            return True
        if cached is False:
            return False
    except Exception as e:
        logger.error(f"黑名单缓存查询异常: {e}")
    
    # 2. 缓存未命中或异常，回源数据库（缓存穿透保护）
    db_result = _check_db(token)
    if db_result:
        # 重新塞入缓存，延长TTL
        cache.set(f"{BLACKLIST_CACHE_PREFIX}{token}", True, ttl=BLACKLIST_CACHE_TTL)
    else:
        # 为了防止缓存穿透，将不存在的结果也缓存短时间（阴性缓存）
        cache.set(f"{BLACKLIST_CACHE_PREFIX}{token}", False, ttl=60)
    return db_result

def add_to_blacklist_cache(token: str, ttl: int = BLACKLIST_CACHE_TTL):
    try:
        cache.set(f"{BLACKLIST_CACHE_PREFIX}{token}", True, ttl=ttl)
    except Exception as e:
        logger.error(f"加入黑名单缓存失败: {e}")