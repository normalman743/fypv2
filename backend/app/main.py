from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.models.database import engine, Base
from app.schemas.common import ErrorResponse
from app.middleware.rate_limiter import RateLimitMiddleware
import os

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# 验证CORS配置安全性
if settings.environment == "production" and "*" in settings.cors_origins_list:
    import logging
    logging.critical("生产环境CORS配置不安全: 允许所有来源 (*). 请设置 CORS_ORIGINS 环境变量.")
    # 在生产环境强制使用安全默认值
    safe_origins = ["https://your-domain.com"]  # 生产环境应该设置具体域名
else:
    safe_origins = settings.cors_origins_list

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=safe_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 限制允许的方法
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],  # 限制允许的头部
)

# 添加速率限制中间件（防止资源耗尽攻击）
app.add_middleware(
    RateLimitMiddleware,
    calls_per_minute=120,  # 每分钟最多120次请求
    calls_per_hour=1000    # 每小时最多1000次请求
)

# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """统一HTTP异常响应格式"""
    # 检查detail是否已经是字典格式（ErrorResponse）
    if isinstance(exc.detail, dict) and "success" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    
    # 否则使用默认格式
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error={
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail
            }
        ).model_dump()
    )

# 健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "校园LLM系统运行正常"}

# 根端点
@app.get("/")
async def root():
    return {
        "message": "欢迎使用校园LLM系统",
        "version": settings.app_version,
        "docs": "/docs"
    }

# 导入路由
from app.api.v1 import auth, semesters, courses, folders, files, chats, messages, admin, unified_files

# 注册路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(semesters.router, prefix="/api/v1")
app.include_router(courses.router, prefix="/api/v1")
app.include_router(folders.router, prefix="/api/v1")
app.include_router(unified_files.router, prefix="/api/v1")  # 统一文件管理 (优先级高)
app.include_router(files.router, prefix="/api/v1")
app.include_router(chats.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
