"""
监控中间件 - 请求追踪和性能监控
"""
import time
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from collections import defaultdict
import threading

# 请求计数器（简单的内存统计，生产环境建议使用 Prometheus）
_request_stats = defaultdict(lambda: {"count": 0, "total_time": 0, "slow_count": 0})
_stats_lock = threading.Lock()


class MonitoringMiddleware(BaseHTTPMiddleware):
    """监控中间件"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # 生成请求 ID（用于链路追踪）
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            import uuid
            request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # 记录请求开始
        logger.info(f"[{request_id}] 请求开始: {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # 记录请求完成
            logger.info(f"[{request_id}] 请求完成: {response.status_code} - {duration:.3f}s")
            
            # 添加自定义响应头
            response.headers["X-Process-Time"] = str(duration)
            response.headers["X-Request-ID"] = request_id
            
            # 更新统计（慢请求 > 1秒）
            self._update_stats(request.url.path, duration, duration > 1.0)
            
            # 慢请求告警
            if duration > 1.0:
                logger.warning(f"[{request_id}] 慢请求: {request.method} {request.url.path} - {duration:.3f}s")
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[{request_id}] 请求异常: {str(e)} - {duration:.3f}s")
            raise
    
    def _update_stats(self, path: str, duration: float, is_slow: bool):
        """更新统计信息"""
        with _stats_lock:
            _request_stats[path]["count"] += 1
            _request_stats[path]["total_time"] += duration
            if is_slow:
                _request_stats[path]["slow_count"] += 1
    
    @staticmethod
    def get_stats():
        """获取统计信息"""
        with _stats_lock:
            stats = {}
            for path, data in _request_stats.items():
                avg_time = data["total_time"] / data["count"] if data["count"] > 0 else 0
                stats[path] = {
                    "count": data["count"],
                    "avg_time": round(avg_time, 3),
                    "slow_count": data["slow_count"],
                    "slow_rate": round(data["slow_count"] / data["count"] * 100, 2) if data["count"] > 0 else 0
                }
            return stats
    
    @staticmethod
    def reset_stats():
        """重置统计"""
        with _stats_lock:
            _request_stats.clear()


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件（自动记录数据库查询）"""
    
    async def dispatch(self, request: Request, call_next):
        # 记录数据库查询次数（需要 SQLAlchemy 事件钩子）
        from sqlalchemy import event
        from app.database import engine
        
        query_count = 0
        
        def before_cursor_execute(conn, cursor, statement, params, context, executemany):
            nonlocal query_count
            query_count += 1
        
        event.listen(engine, 'before_cursor_execute', before_cursor_execute)
        
        try:
            response = await call_next(request)
            return response
        finally:
            event.remove(engine, 'before_cursor_execute', before_cursor_execute)
            # 记录查询次数到响应头
            response.headers["X-DB-Queries"] = str(query_count)