"""
幂等性服务 - 基于 Redis 实现请求去重
防止重复提交、退款等操作的幂等性保证
"""
import hashlib
import json
import uuid
from datetime import timedelta
from functools import wraps
from typing import Optional, Callable, Any

import redis
from loguru import logger

from app.config import REDIS_URL


class IdempotencyService:
    """幂等性服务"""

    # 默认幂等性 key 过期时间（10分钟）
    DEFAULT_TTL = 600

    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._connect()

    def _connect(self):
        """建立 Redis 连接"""
        try:
            self._client = redis.Redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            self._client.ping()
            logger.info("幂等性服务 Redis 连接成功")
        except Exception as e:
            logger.warning(f"幂等性服务 Redis 连接失败: {e}")
            self._client = None

    def _generate_key(self, idempotency_key: str, user_id: Optional[int] = None) -> str:
        """生成幂等性缓存 key"""
        parts = ["idempotency", idempotency_key]
        if user_id:
            parts.append(str(user_id))
        return ":".join(parts)

    def check_and_set(
        self,
        idempotency_key: str,
        user_id: Optional[int] = None,
        ttl: int = DEFAULT_TTL,
        metadata: Optional[dict] = None
    ) -> tuple[bool, Optional[Any]]:
        """
        检查并设置幂等性标记

        Returns:
            (is_new_request, cached_result)
            - is_new_request: True 表示是新请求，False 表示重复请求
            - cached_result: 如果是重复请求，返回之前缓存的结果
        """
        if not self._client:
            # Redis 不可用时，允许继续执行（降级策略）
            return True, None

        try:
            key = self._generate_key(idempotency_key, user_id)

            # 使用 SETNX 保证原子性
            is_new = self._client.set(
                key,
                json.dumps({"status": "processing", "metadata": metadata or {}}),
                nx=True,
                ex=ttl
            )

            if is_new:
                return True, None
            else:
                # 获取已存在的记录
                data = self._client.get(key)
                if data:
                    parsed = json.loads(data)
                    if parsed.get("status") == "completed":
                        return False, parsed.get("result")
                    elif parsed.get("status") == "processing":
                        # 请求正在处理中
                        return False, {"error": "request_is_being_processed"}
                return False, None

        except Exception as e:
            logger.error(f"幂等性检查失败: {e}")
            # 出错时允许继续执行（降级策略）
            return True, None

    def complete(
        self,
        idempotency_key: str,
        user_id: Optional[int] = None,
        result: Any = None,
        ttl: int = DEFAULT_TTL
    ) -> bool:
        """
        标记请求已完成（设置结果）

        Args:
            idempotency_key: 幂等性 key
            user_id: 用户 ID（可选）
            result: 要缓存的结果
            ttl: 结果缓存时间
        """
        if not self._client:
            return False

        try:
            key = self._generate_key(idempotency_key, user_id)
            data = {
                "status": "completed",
                "result": result
            }
            self._client.set(key, json.dumps(data, ensure_ascii=False, default=str), ex=ttl)
            return True
        except Exception as e:
            logger.error(f"设置幂等性结果失败: {e}")
            return False

    def remove(self, idempotency_key: str, user_id: Optional[int] = None) -> bool:
        """移除幂等性标记"""
        if not self._client:
            return False

        try:
            key = self._generate_key(idempotency_key, user_id)
            self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"移除幂等性标记失败: {e}")
            return False


# 全局幂等性服务实例
idempotency_service = IdempotencyService()


def idempotent(key_prefix: str = "", ttl: int = 600):
    """
    幂等性装饰器

    Args:
        key_prefix: 幂等性 key 前缀
        ttl: 缓存时间（秒），默认10分钟
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 从 kwargs 中提取幂等性 key（通常由调用方传入）
            idempotency_key = kwargs.pop("idempotency_key", None)

            if not idempotency_key:
                # 如果没有提供幂等性 key，生成一个基于参数的 hash
                key_parts = [key_prefix or func.__name__]
                for arg in args:
                    if isinstance(arg, (int, str, float, bool)):
                        key_parts.append(str(arg))
                for k, v in sorted(kwargs.items()):
                    if isinstance(v, (int, str, float, bool)):
                        key_parts.append(f"{k}:{v}")
                idempotency_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

            # 获取用户 ID（如果存在）
            user_id = kwargs.get("current_user_id")

            # 检查是否是重复请求
            is_new, cached_result = idempotency_service.check_and_set(
                idempotency_key,
                user_id=user_id,
                ttl=ttl,
                metadata={"function": func.__name__}
            )

            if not is_new:
                if cached_result and isinstance(cached_result, dict) and cached_result.get("error") == "request_is_being_processed":
                    from fastapi import HTTPException
                    raise HTTPException(status_code=409, detail="请求正在处理中，请勿重复提交")
                if cached_result is not None:
                    return cached_result
                from fastapi import HTTPException
                raise HTTPException(status_code=409, detail="检测到重复请求")

            try:
                # 执行原函数
                result = func(*args, **kwargs)

                # 缓存结果
                idempotency_service.complete(idempotency_key, user_id, result, ttl)

                return result
            except Exception as e:
                # 失败时移除幂等性标记，允许重试
                idempotency_service.remove(idempotency_key, user_id)
                raise

        return wrapper
    return decorator
