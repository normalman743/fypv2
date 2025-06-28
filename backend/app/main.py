from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.models.database import engine, Base
from app.schemas.common import ErrorResponse

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
from app.api.v1 import auth, semesters, courses

# 注册路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(semesters.router, prefix="/api/v1")
app.include_router(courses.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
