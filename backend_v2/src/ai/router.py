"""AI模块路由定义 - 基于FastAPI 2024最佳实践"""
from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from sqlalchemy.orm import Session

from .service import AIService
from .schemas import (
    AIRequest, AIResponse, AIModelResponse,
    AIModelListResponse, AIConversationConfigResponse
)

# 导入依赖
from src.shared.dependencies import DbDep, UserDep
from src.shared.api_decorator import create_service_route_config, service_api_handler
from src.shared.schemas import BaseResponse

# 创建路由器
router = APIRouter(prefix="/ai", include_in_schema=False, tags=["AI智能助手/AI"])


# ===== AI对话接口 =====
"""
@router.post("/chat", **create_service_route_config(
    AIService, 'generate_response', BaseResponse[AIResponse],
    summary="AI对话生成",
    description="与AI进行对话，支持RAG检索和多种上下文模式",
    operation_id="ai_chat"
))
@service_api_handler(AIService, 'generate_response')
async def ai_chat(
    request: AIRequest,
    current_user: UserDep,
    db: DbDep
):
    service = AIService(db)
    result = service.generate_response(request, current_user.id)
    
    return BaseResponse(
        success=True,
        data=result,
        message="对话生成成功"
    )
"""

# ===== AI模型管理 =====

@router.get("/models", **create_service_route_config(
    AIService, 'get_available_models', BaseResponse[List[AIModelResponse]],
    summary="获取可用AI模型",
    description="获取系统中所有可用的AI模型列表",
    operation_id="get_ai_models"
))
@service_api_handler(AIService, 'get_available_models')
async def get_available_models(
    current_user: UserDep,
    db: DbDep
):
    """获取可用AI模型列表"""
    service = AIService(db)
    models = service.get_available_models()
    
    return BaseResponse(
        success=True,
        data=models,
        message=None
    )


# ===== AI配置管理 =====

@router.get("/configs", **create_service_route_config(
    AIService, 'get_conversation_configs', BaseResponse[List[AIConversationConfigResponse]],
    summary="获取对话配置",
    description="获取AI对话的配置选项，包括上下文模式等",
    operation_id="get_ai_configs"
))
@service_api_handler(AIService, 'get_conversation_configs')
async def get_conversation_configs(
    current_user: UserDep,
    db: DbDep
):
    """获取对话配置选项"""
    service = AIService(db)
    configs = service.get_conversation_configs()
    
    return BaseResponse(
        success=True,
        data=configs,
        message=None
    )


# ===== RAG相关接口 =====

@router.post("/rag/search", **create_service_route_config(
    AIService, 'search_knowledge_base', BaseResponse[List[dict]],
    summary="知识库搜索",
    description="在知识库中搜索相关内容，用于RAG功能",
    operation_id="rag_search"
))
@service_api_handler(AIService, 'search_knowledge_base')
async def search_knowledge_base(
    current_user: UserDep,
    db: DbDep,
    query: str = Query(..., description="搜索查询"),
    course_id: Optional[int] = Query(None, description="限制搜索范围的课程ID"),
    limit: int = Query(5, ge=1, le=20, description="返回结果数量限制")
):
    """在知识库中搜索相关内容"""
    service = AIService(db)
    results = service.search_knowledge_base(
        query=query,
        user_id=current_user.id,
        course_id=course_id,
        limit=limit
    )
    
    return BaseResponse(
        success=True,
        data=results,
        message="搜索完成"
    )


# ===== 文件向量化接口 =====

@router.post("/vectorize/file/{file_id}", **create_service_route_config(
    AIService, 'vectorize_file', BaseResponse[dict],
    summary="文件向量化",
    description="将指定文件向量化并存储到知识库中",
    operation_id="vectorize_file"
))
@service_api_handler(AIService, 'vectorize_file')
async def vectorize_file(
    file_id: int,
    current_user: UserDep,
    db: DbDep
):
    """向量化指定文件"""
    service = AIService(db)
    result = service.vectorize_file(file_id, current_user.id)
    
    return BaseResponse(
        success=True,
        data=result,
        message="文件向量化完成"
    )


@router.post("/vectorize/course/{course_id}", **create_service_route_config(
    AIService, 'vectorize_course_files', BaseResponse[dict],
    summary="课程文件批量向量化",
    description="将指定课程的所有文件进行批量向量化",
    operation_id="vectorize_course"
))
@service_api_handler(AIService, 'vectorize_course_files')
async def vectorize_course_files(
    course_id: int,
    current_user: UserDep,
    db: DbDep
):
    """批量向量化课程文件"""
    service = AIService(db)
    result = service.vectorize_course_files(course_id, current_user.id)
    
    return BaseResponse(
        success=True,
        data=result,
        message="课程文件向量化完成"
    )


# ===== 向量化状态查询 =====

@router.get("/vectorize/status/{file_id}", **create_service_route_config(
    AIService, 'get_vectorization_status', BaseResponse[dict],
    summary="查询文件向量化状态",
    description="查询指定文件的向量化处理状态",
    operation_id="get_vectorization_status"
))
@service_api_handler(AIService, 'get_vectorization_status')
async def get_vectorization_status(
    file_id: int,
    current_user: UserDep,
    db: DbDep
):
    """查询文件向量化状态"""
    service = AIService(db)
    status = service.get_vectorization_status(file_id, current_user.id)
    
    return BaseResponse(
        success=True,
        data=status,
        message=None
    )