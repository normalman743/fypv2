from fastapi import APIRouter
from app.schemas.common import SuccessResponse
from app.core.config import settings

router = APIRouter(tags=["系统健康检查/System Health Check"])

@router.get(
    "/health",
    response_model=SuccessResponse,
    responses={
        200: {
            "description": "Success - 系统运行正常",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "status": "healthy",
                            "message": "校园LLM系统运行正常"
                        }
                    }
                }
            }
        }
    },
    summary="健康检查",
    description="检查系统运行状态，用于负载均衡器和监控系统"
)
async def health_check():
    """系统健康检查
    
    返回系统运行状态，主要用于：
    - 负载均衡器检查服务可用性
    - 监控系统检测服务状态
    - 容器编排判断服务是否正常
    """
    return SuccessResponse(
        success=True,
        data={
            "status": "healthy", 
            "message": "校园LLM系统运行正常"
        }
    )

@router.get(
    "/",
    response_model=SuccessResponse,
    responses={
        200: {
            "description": "Success - 系统信息获取成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "message": "欢迎使用校园LLM系统",
                            "version": "1.0.0",
                            "docs": "/docs",
                            "api_prefix": "/api/v1"
                        }
                    }
                }
            }
        }
    },
    summary="系统信息",
    description="获取系统基本信息和API文档入口"
)
async def root():
    """系统根端点
    
    返回系统基本信息，包括：
    - 欢迎信息
    - 系统版本
    - API文档地址
    """
    return SuccessResponse(
        success=True,
        data={
            "message": "欢迎使用校园LLM系统",
            "version": settings.app_version,
            "docs": "/docs",
            "api_prefix": "/api/v1"
        }
    )