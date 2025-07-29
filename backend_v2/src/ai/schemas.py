"""AI模块Schema定义"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from decimal import Decimal


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

    model_config = {"from_attributes": True}


class ConversationConfigResponse(BaseModel):
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

    model_config = {"from_attributes": True}


class AIStatsResponse(BaseModel):
    """AI统计信息响应"""
    total_conversations: int
    total_messages: int
    total_tokens_used: int
    total_cost: Decimal
    popular_models: List[Dict[str, Any]]
    rag_usage_stats: Dict[str, int]