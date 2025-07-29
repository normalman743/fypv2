"""Chat模块Pydantic Schema定义"""
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime
from decimal import Decimal
from src.shared.schemas import BaseResponse


# ===== 聊天相关Schema =====

class ChatBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="聊天标题")
    chat_type: Literal["general", "course"] = Field("general", description="聊天类型")
    course_id: Optional[int] = Field(None, description="关联课程ID")
    custom_prompt: Optional[str] = Field(None, description="自定义提示词")
    ai_model: Literal["Star", "StarPlus", "StarCode"] = Field("Star", description="AI模型")
    search_enabled: bool = Field(False, description="是否启用搜索")
    context_mode: Literal["Economy", "Standard", "Premium", "Max"] = Field(
        "Standard", description="上下文模式"
    )
    rag_enabled: bool = Field(True, description="是否启用RAG")

    @field_validator('course_id')
    @classmethod
    def validate_course_chat(cls, v, info):
        """验证课程聊天必须有course_id"""
        if info.data.get('chat_type') == 'course' and v is None:
            raise ValueError('课程聊天必须指定course_id')
        return v


class CreateChatRequest(ChatBase):
    """创建聊天请求"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra={
            "examples": [
                {
                    "title": "关于Python的问题",
                    "chat_type": "general",
                    "course_id": None,
                    "custom_prompt": None,
                    "ai_model": "Star",
                    "search_enabled": False,
                    "context_mode": "Standard",
                    "rag_enabled": True,
                    "first_message": "请介绍一下Python的基本语法",
                    "file_ids": [],
                    "folder_ids": [],
                    "temporary_file_tokens": [],
                    "stream": False
                },
                {
                    "title": "数据结构课程讨论",
                    "chat_type": "course",
                    "course_id": 1,
                    "custom_prompt": "你是一个数据结构专家",
                    "ai_model": "StarPlus",
                    "search_enabled": True,
                    "context_mode": "Premium",
                    "rag_enabled": True,
                    "first_message": "请解释一下二叉林的时间复杂度",
                    "file_ids": [1, 2],
                    "folder_ids": [1],
                    "temporary_file_tokens": [],
                    "stream": True
                }
            ]
        }
    )
    
    first_message: str = Field(..., min_length=1, description="首条消息内容")
    file_ids: Optional[List[int]] = Field([], description="关联文件ID列表")
    folder_ids: Optional[List[int]] = Field([], description="关联文件夹ID列表")
    temporary_file_tokens: Optional[List[str]] = Field([], description="临时文件token列表")
    stream: bool = Field(False, description="是否启用流式响应")


class UpdateChatRequest(BaseModel):
    """更新聊天请求"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra={
            "examples": [
                {
                    "title": "更新后的聊天标题",
                    "ai_model": "StarPlus",
                    "rag_enabled": False
                }
            ]
        }
    )
    
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="聊天标题")
    ai_model: Optional[Literal["Star", "StarPlus", "StarCode"]] = Field(None, description="AI模型")
    rag_enabled: Optional[bool] = Field(None, description="是否启用RAG")


class ChatStats(BaseModel):
    """聊天统计信息"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"message_count": 12}
            ]
        }
    )
    
    message_count: int = Field(0, description="消息数量")


class CourseInfo(BaseModel):
    """课程信息"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "name": "Python程序设计",
                    "code": "CS101"
                }
            ]
        }
    )
    
    id: int
    name: str
    code: str


class ChatResponse(BaseModel):
    """聊天响应"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "title": "关于Python的问题",
                    "chat_type": "course",
                    "course_id": 1,
                    "user_id": 1,
                    "custom_prompt": "你是一个Python专家",
                    "ai_model": "StarPlus",
                    "search_enabled": True,
                    "context_mode": "Premium",
                    "rag_enabled": True,
                    "created_at": "2025-01-15T10:30:00Z",
                    "updated_at": "2025-01-15T11:45:00Z",
                    "last_message_at": "2025-01-15T11:45:00Z",
                    "course": {
                        "id": 1,
                        "name": "Python程序设计",
                        "code": "CS101"
                    },
                    "stats": {"message_count": 12}
                }
            ]
        }
    )
    
    id: int
    title: str
    chat_type: str
    course_id: Optional[int] = None
    user_id: int
    custom_prompt: Optional[str] = None
    ai_model: str = "Star"
    search_enabled: bool = False
    context_mode: str = "Standard"
    rag_enabled: bool = True
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None
    
    # 关联信息
    course: Optional[CourseInfo] = None
    stats: ChatStats


class ChatListData(BaseModel):
    """聊天列表数据"""
    chats: List[ChatResponse]
    total: int


class ChatListResponse(BaseResponse[ChatListData]):
    """聊天列表响应"""
    pass


class CreateChatData(BaseModel):
    """创建聊天响应数据"""
    chat: dict  # ChatResponse的简化版本
    user_message: dict  # MessageResponse的简化版本
    ai_message: dict  # MessageResponse的简化版本


class CreateChatResponse(BaseResponse[CreateChatData]):
    """创建聊天响应"""
    pass


class UpdateChatData(BaseModel):
    """更新聊天响应数据"""
    chat: dict  # {"id": int, "title": str, "updated_at": datetime}


class UpdateChatResponse(BaseResponse[UpdateChatData]):
    """更新聊天响应"""
    pass


# ===== 消息相关Schema =====

class MessageBase(BaseModel):
    content: str = Field(..., min_length=1, description="消息内容")


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra={
            "examples": [
                {
                    "content": "请解释一下这个Python代码的作用",
                    "file_ids": [],
                    "stream": False
                },
                {
                    "content": "根据上传的文档内容，总结一下主要知识点",
                    "file_ids": [1, 2],
                    "stream": True
                }
            ]
        }
    )
    
    content: str = Field(..., min_length=1, description="消息内容")
    file_ids: Optional[List[int]] = Field([], description="关联文件ID列表")
    stream: bool = Field(False, description="是否启用流式响应")


class EditMessageRequest(BaseModel):
    """编辑消息请求"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra={
            "examples": [
                {
                    "content": "修改后的消息内容"
                }
            ]
        }
    )
    
    content: str = Field(..., min_length=1, description="新的消息内容")


class RAGSourceInfo(BaseModel):
    """RAG来源信息"""
    file_id: int
    file_name: str
    chunk_content: str
    relevance_score: Optional[Decimal] = None


class MessageResponse(BaseModel):
    """消息响应"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "chat_id": 1,
                    "content": "请解释一下Python的列表推导式",
                    "role": "user",
                    "model_name": None,
                    "tokens_used": None,
                    "input_tokens": None,
                    "output_tokens": None,
                    "cost": None,
                    "response_time_ms": None,
                    "rag_sources": None,
                    "context_size": None,
                    "direct_file_count": 0,
                    "rag_source_count": 0,
                    "is_edited": False,
                    "edited_at": None,
                    "created_at": "2025-01-15T10:30:00Z"
                },
                {
                    "id": 2,
                    "chat_id": 1,
                    "content": "Python中的列表推导式是一种简洁的创建列表的方法...",
                    "role": "assistant",
                    "model_name": "Star",
                    "tokens_used": 150,
                    "input_tokens": 25,
                    "output_tokens": 125,
                    "cost": "0.003",
                    "response_time_ms": 1500,
                    "rag_sources": [
                        {
                            "file_id": 1,
                            "file_name": "Python教程.pdf",
                            "chunk_content": "列表推导式..."
                        }
                    ],
                    "context_size": 2048,
                    "direct_file_count": 1,
                    "rag_source_count": 1,
                    "is_edited": False,
                    "edited_at": None,
                    "created_at": "2025-01-15T10:30:30Z"
                }
            ]
        }
    )
    
    id: int
    chat_id: int
    content: str
    role: str  # 'user', 'assistant', 'system'
    
    # AI相关字段
    model_name: Optional[str] = None
    tokens_used: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cost: Optional[Decimal] = None
    response_time_ms: Optional[int] = None
    
    # RAG相关
    rag_sources: Optional[List[dict]] = None
    
    # 上下文统计
    context_size: Optional[int] = None
    direct_file_count: int = 0
    rag_source_count: int = 0
    
    # 编辑相关
    is_edited: bool = False
    edited_at: Optional[datetime] = None
    
    created_at: datetime


class MessageListData(BaseModel):
    """消息列表数据"""
    messages: List[MessageResponse]
    total: int


class MessageListResponse(BaseResponse[MessageListData]):
    """消息列表响应"""
    pass


class SendMessageData(BaseModel):
    """发送消息响应数据"""
    user_message: MessageResponse
    ai_message: MessageResponse


class SendMessageResponse(BaseResponse[SendMessageData]):
    """发送消息响应"""
    pass


class UpdateMessageData(BaseModel):
    """更新消息响应数据"""
    message: dict  # {"id": int, "content": str, "is_edited": bool, "updated_at": datetime}


class UpdateMessageResponse(BaseResponse[UpdateMessageData]):
    """更新消息响应"""
    pass


# ===== 消息文件引用Schema =====

class MessageFileReferenceResponse(BaseModel):
    """消息文件引用响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    message_id: int
    file_id: int
    created_at: datetime


# ===== 消息RAG来源Schema =====

class MessageRAGSourceResponse(BaseModel):
    """消息RAG来源响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    message_id: int
    document_chunk_id: int
    relevance_score: Optional[Decimal] = None
    created_at: datetime