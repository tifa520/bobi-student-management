import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data')
DATABASE_URL = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(DATA_DIR, "app.db")}')

APP_NAME = "Bobi艺术·学员管理系统"
APP_VERSION = "v8.0.0"

ORDER_NO_DATE_FORMAT = "%Y%m%d"
ENROLL_SESSION_EXPIRE_DAYS = 7

SECRET_KEY = os.environ.get("SECRET_KEY", "your-very-secret-key-change-in-production")
if not SECRET_KEY or SECRET_KEY == "your-very-secret-key-change-in-production":
    print("❌ FATAL: SECRET_KEY must be set in production environment.")
    print("   Generate one with: openssl rand -hex 32")
    sys.exit(1)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

ENABLE_AUTH_MIDDLEWARE = os.environ.get("ENABLE_AUTH_MIDDLEWARE", "false").lower() == "true"

# Redis 配置
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# 是否启用监控
ENABLE_MONITORING = os.environ.get('ENABLE_MONITORING', 'true').lower() == 'true'

# 慢请求阈值（秒）
SLOW_REQUEST_THRESHOLD = float(os.environ.get('SLOW_REQUEST_THRESHOLD', '1.0'))

# 分页默认值
DEFAULT_PAGE_SIZE = int(os.environ.get('DEFAULT_PAGE_SIZE', '20'))
MAX_PAGE_SIZE = int(os.environ.get('MAX_PAGE_SIZE', '100'))

# 日志级别
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# 认证白名单路径
WHITELIST_PATHS = [
    '/api/health',
    '/api/auth/login',
    '/api/auth/refresh',
    '/api/auth/logout',
    '/api/auth/has-admin', 
    '/api/auth/create-admin',
    '/api/upload/login-bg',
    '/api/exchange-rate',
    '/api/payment-methods',
    '/api/item-categories',
    '/api/students/birthdays',
    '/docs',
    '/openapi.json',
    '/redoc',
    '/media',          # 新增
    '/uploads'        # 新增（兼容旧路径）
]

POINTS_TO_CASH_RATE = 10