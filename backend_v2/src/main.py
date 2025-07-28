from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.shared.config import settings
from src.shared.middleware import setup_middleware
from src.shared.exceptions import setup_exception_handlers
from src.shared.logging import setup_logging
from src.shared.database import setup_database


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    
    # 设置日志
    setup_logging()
    
    # 创建应用
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        debug=settings.debug
    )
    
    # 设置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["Authorization", "Content-Type"],
    )
    
    # 设置其他中间件
    setup_middleware(app)
    
    # 设置异常处理
    setup_exception_handlers(app)
    
    # 设置数据库
    setup_database()
    
    # 注册路由
    register_routers(app)
    
    return app


def register_routers(app: FastAPI) -> None:
    """注册所有路由"""
    # Auth 模块路由
    from src.auth.router import router as auth_router
    app.include_router(auth_router, prefix="/api/v1", tags=["认证"])
    
    # TODO: 随着模块开发逐步添加路由
    # from src.admin.router import router as admin_router
    # from src.course.router import router as course_router
    # from src.chat.router import router as chat_router
    # from src.storage.router import router as storage_router
    # from src.ai.router import router as ai_router
    
    # app.include_router(admin_router, prefix="/api/v1", tags=["管理"])
    # app.include_router(course_router, prefix="/api/v1", tags=["课程"])
    # app.include_router(chat_router, prefix="/api/v1", tags=["聊天"])
    # app.include_router(storage_router, prefix="/api/v1", tags=["存储"])
    # app.include_router(ai_router, prefix="/api/v1", tags=["AI"])


# 创建应用实例
app = create_app()


# 健康检查（简单的系统级端点）
@app.get("/health", tags=["系统"])
async def health_check():
    return {
        "status": "healthy", 
        "version": app.version,
        "environment": settings.environment
    }


@app.get("/", tags=["系统"])
async def root():
    return {
        "message": f"{app.title}",
        "version": app.version,
        "environment": settings.environment,
        "docs": "/docs" if app.debug else "disabled"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.workers
    )