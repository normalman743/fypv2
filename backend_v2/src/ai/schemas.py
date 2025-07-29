"""AI模块Schema定义"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal

# 导入共享响应格式
from src.shared.schemas import BaseResponse


class RAGSource(BaseModel):
    """RAG检索源"""
    source_file: str
    chunk_id: int
    content: str
    score: float
    file_id: Optional[int] = None
    course_id: Optional[int] = None


class AIRequest(BaseModel):
    """AI请求"""
    message: str = Field(..., min_length=1, max_length=10000)
    ai_model: str = Field(default="Star")
    context_mode: str = Field(default="Standard")
    rag_enabled: bool = Field(default=True)
    search_enabled: bool = Field(default=False)
    chat_type: str = Field(default="general")  # general, course
    course_id: Optional[int] = None
    file_ids: Optional[List[int]] = None
    custom_prompt: Optional[str] = None


class AIResponse(BaseModel):
    """AI响应"""
    content: str
    model_name: str
    tokens_used: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cost: Optional[Decimal] = None
    response_time_ms: Optional[int] = None
    rag_sources: Optional[List[RAGSource]] = None
    context_size: Optional[int] = None
    error: Optional[str] = None


class AIModelResponse(BaseModel):
    """AI模型信息响应"""
    id: int
    name: str
    display_name: str
    description: Optional[str]
    provider: str
    model_id: str
    max_tokens: int
    temperature: str
    is_active: bool
    is_default: bool
    supports_function_calling: bool
    supports_vision: bool
    supports_code_execution: bool

    model_config = ConfigDict(from_attributes=True)


class AIConversationConfigResponse(BaseModel):
    """对话配置响应"""
    id: int
    name: str
    display_name: str
    description: Optional[str]
    max_context_messages: int
    max_context_tokens: int
    rag_chunk_limit: int
    rag_similarity_threshold: str
    max_file_attachments: int
    max_file_size_mb: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AIStatsResponse(BaseModel):
    """AI统计信息响应"""
    total_conversations: int
    total_messages: int
    total_tokens_used: int
    total_cost: Decimal
    popular_models: List[Dict[str, Any]]
    rag_usage_stats: Dict[str, int]


# ===== 具体响应模型 =====

class AIModelListResponse(BaseResponse[List[AIModelResponse]]):
    """AI模型列表响应"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "success": True,
                "data": [
                    {
                        "id": 1,
                        "name": "Star",
                        "display_name": "Star助手",
                        "description": "智能校园助手，专注于学术支持",
                        "provider": "openai",
                        "model_id": "gpt-4",
                        "max_tokens": 4096,
                        "temperature": "0.7",
                        "is_active": True,
                        "is_default": True,
                        "supports_function_calling": True,
                        "supports_vision": False,
                        "supports_code_execution": False
                    }
                ],
                "message": None
            }]
        }
    )


class AIResponseModel(BaseResponse[AIResponse]):
    """AI对话响应模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "success": True,
                "data": {
                    "content": "您好！我是ICU智能学习助手Star。有什么可以帮助您的吗？",
                    "model_name": "Star",
                    "tokens_used": 120,
                    "input_tokens": 50,
                    "output_tokens": 70,
                    "cost": "0.002",
                    "response_time_ms": 1500,
                    "rag_sources": [
                        {
                            "source_file": "course_materials.pdf",
                            "chunk_id": 123,
                            "content": "相关课程内容...",
                            "score": 0.85,
                            "file_id": 456,
                            "course_id": 789
                        }
                    ],
                    "context_size": 2048,
                    "error": None
                },
                "message": "对话生成成功"
            }]
        }
    )