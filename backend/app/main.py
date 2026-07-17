from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import init_db
from app.routers import (
    student, enroll, attendance, class_, course, teacher, classroom,
    score, gift, purchase, activity, order, course_record, refund, change_log, 
    auth, dashboard, item, misc_fee, upload, settings, birthday, stats,
    student_portal
)
from app.config import APP_NAME, APP_VERSION, ENABLE_AUTH_MIDDLEWARE
from app.middleware.auth import AuthMiddleware
from app.middleware import log_requests
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from loguru import logger
from app.routers import sales
from app.routers import salary
import sys
import os

# 创建日志目录
os.makedirs("logs", exist_ok=True)

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
logger.add("logs/app_{time:YYYY-MM-DD}.log", rotation="1 day", retention="30 days",
           compression="zip", level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
logger.add("logs/error_{time:YYYY-MM-DD}.log", rotation="1 day", retention="30 days",
           compression="zip", level="ERROR", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

# 初始化数据库（创建表等）
init_db()

app = FastAPI(title=APP_NAME, version=APP_VERSION)

# 添加限流器到 app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# 请求日志中间件
app.middleware("http")(log_requests)

# CORS 配置（生产环境限制为已知域名）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://www.bobiart.cn:5050", "http://bobiart.cn:5050"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 认证中间件（可选）
if ENABLE_AUTH_MIDDLEWARE:
    app.add_middleware(AuthMiddleware)

# 挂载静态文件目录（用于统一图片存储）
os.makedirs("media", exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")

# 路由注册 - 全部统一挂载到 /api 前缀
app.include_router(student.router, prefix="/api", tags=["学员管理"])
app.include_router(enroll.router, prefix="/api", tags=["报名流程"])
app.include_router(attendance.router, prefix="/api", tags=["考勤管理"])
app.include_router(class_.router, prefix="/api", tags=["班级管理"])
app.include_router(course.router, prefix="/api", tags=["课程管理"])
app.include_router(teacher.router, prefix="/api", tags=["教师管理"])
app.include_router(classroom.router, prefix="/api", tags=["教室管理"])
app.include_router(score.router, prefix="/api/score", tags=["积分管理"])
app.include_router(gift.router, prefix="/api/gift", tags=["礼物兑换"])
app.include_router(purchase.router, prefix="/api/purchase", tags=["物品购买"])
app.include_router(activity.router, prefix="/api/activity", tags=["活动管理"])
app.include_router(order.router, prefix="/api/order", tags=["订单管理"])
app.include_router(course_record.router, prefix="/api/course-record", tags=["课消记录"])
app.include_router(refund.router, prefix="/api/refund", tags=["退费管理"])
app.include_router(change_log.router, prefix="/api/change-log", tags=["变更记录"])
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(dashboard.router, prefix="/api", tags=["工作台"])
app.include_router(item.router, prefix="/api", tags=["物品管理"])
app.include_router(misc_fee.router, prefix="/api", tags=["杂费记录"])
app.include_router(upload.router, prefix="/api/upload", tags=["上传"])
app.include_router(settings.router, prefix="/api", tags=["系统设置"])
app.include_router(birthday.router, prefix="/api", tags=["生日提醒"])
app.include_router(sales.router, prefix="/api", tags=["销售订单"])
app.include_router(salary.router, prefix="/api", tags=["课酬提成"])
app.include_router(stats.router, prefix="/api", tags=["统计"])
app.include_router(student_portal.router, prefix="/api", tags=["学员门户"])

# 健康检查接口
@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": APP_NAME, "version": APP_VERSION}

@app.on_event("startup")
def startup_event():
    logger.info(f"应用启动: {APP_NAME} v{APP_VERSION}")
