from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.models.database import engine, Base
from app.schemas.common import ErrorResponse
import os
import asyncio
import time
import logging
from collections import defaultdict
from datetime import datetime, timedelta
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log", encoding='utf-8')
    ]
)

# 减少SQLAlchemy日志级别（避免太多SQL日志）
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 简单的速率限制器
class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.max_requests = 100  # 每分钟最多100个请求
        self.window = timedelta(minutes=1)
    
    def is_allowed(self, client_ip: str) -> bool:
        now = datetime.now()
        # 清理过期的请求记录
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < self.window
        ]
        # 检查是否超过限制
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        # 记录新请求
        self.requests[client_ip].append(now)
        return True

rate_limiter = RateLimiter()

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 速率限制中间件
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """添加速率限制"""
    client_ip = request.client.host if request.client else "unknown"
    
    # 跳过 OPTIONS 请求
    if request.method == "OPTIONS":
        return await call_next(request)
    
    # 检查速率限制
    if not rate_limiter.is_allowed(client_ip):
        logging.warning(f"Rate limit exceeded for {client_ip}")
        return JSONResponse(
            status_code=429,
            content=ErrorResponse(
                success=False,
                error={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "请求过于频繁，请稍后再试"
                }
            ).model_dump()
        )
    
    return await call_next(request)

# 请求超时中间件
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    """添加请求超时控制"""
    try:
        start_time = time.time()
        # 设置30秒超时
        response = await asyncio.wait_for(call_next(request), timeout=30.0)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except asyncio.TimeoutError:
        logging.error(f"Request timeout: {request.method} {request.url.path}")
        return JSONResponse(
            status_code=504,
            content=ErrorResponse(
                success=False,
                error={
                    "code": "REQUEST_TIMEOUT",
                    "message": "请求处理超时，请稍后重试"
                }
            ).model_dump()
        )

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    start_time = time.time()
    
    # 记录请求信息
    logging.info(f"Request: {request.method} {request.url.path} from {request.client.host}")
    
    response = await call_next(request)
    
    # 记录响应信息
    process_time = time.time() - start_time
    logging.info(f"Response: {response.status_code} in {process_time:.2f}s")
    
    return response

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
