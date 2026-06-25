from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

# 获取客户端 IP
def get_client_ip(request: Request) -> str:
    """获取客户端真实 IP（支持代理）"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)

# 创建限流器实例
limiter = Limiter(key_func=get_client_ip)

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """限流超限处理"""
    return JSONResponse(
        status_code=429,
        content={
            "code": 429,
            "message": "请求过于频繁，请稍后再试",
            "detail": str(exc.detail)
        }
    )
