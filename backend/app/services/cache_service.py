import os
"""
缓存服务 - 基于 Redis
"""
import json
import hashlib
from functools import wraps
from typing import Optional, Any, Callable
from datetime import timedelta
import redis
from loguru import logger
from app.config import REDIS_URL

# Redis 连接配置（需要在 config.py 中添加）
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

class CacheService:
    """缓存服务"""
    
    def __init__(self):
        self._client = None
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
            # 测试连接
            self._client.ping()
            logger.info("Redis 连接成功")
        except Exception as e:
            logger.warning(f"Redis 连接失败，将使用内存缓存: {e}")
            self._client = None
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self._client:
            return None
        try:
            value = self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"获取缓存失败: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """设置缓存（默认5分钟）"""
        if not self._client:
            return False
        try:
            self._client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
            return True
        except Exception as e:
            logger.error(f"设置缓存失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._client:
            return False
        try:
            self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"删除缓存失败: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """批量删除匹配模式的缓存"""
        if not self._client:
            return 0
        try:
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"批量删除缓存失败: {e}")
            return 0
    
    def invalidate_student_cache(self, student_id: int):
        """清除学员相关缓存"""
        self.clear_pattern(f"student:*:{student_id}:*")
        self.clear_pattern(f"student_list:*")
    
    def invalidate_item_cache(self, item_id: int):
        """清除商品相关缓存"""
        self.clear_pattern(f"item:*")
        self.clear_pattern(f"items:*")
        self.clear_pattern(f"inventory:*")

# 全局缓存实例
cache = CacheService()


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存时间（秒），默认5分钟
        key_prefix: 缓存 key 前缀
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存 key
            key_parts = [key_prefix or func.__name__]
            for arg in args:
                if isinstance(arg, (int, str, float, bool)):
                    key_parts.append(str(arg))
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (int, str, float, bool)):
                    key_parts.append(f"{k}:{v}")
            
            cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行原函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            cache.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 生成缓存 key
            key_parts = [key_prefix or func.__name__]
            for arg in args:
                if isinstance(arg, (int, str, float, bool)):
                    key_parts.append(str(arg))
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (int, str, float, bool)):
                    key_parts.append(f"{k}:{v}")
            
            cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            cache.set(cache_key, result, ttl)
            
            return result
        
        # 判断是异步函数还是同步函数
        if hasattr(func, '__call__') and func.__name__ != '<lambda>':
            import inspect
            if inspect.iscoroutinefunction(func):
                return async_wrapper
        return sync_wrapper
    
    return decorator