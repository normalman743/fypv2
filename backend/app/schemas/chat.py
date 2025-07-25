from pydantic import BaseModel, validator
from typing import Optional, List, Literal
from datetime import datetime
from app.schemas.common import SuccessResponse

class ChatStats(BaseModel):
    message_count: int

class CourseInfo(BaseModel):
    id: int
    name: str
    code: str

class ChatResponse(BaseModel):
    id: int
    title: str
    chat_type: str
    course_id: Optional[int]
    user_id: int
    custom_prompt: Optional[str]
    ai_model: str
    search_enabled: bool
    context_mode: str
    created_at: datetime
    updated_at: datetime
    course: Optional[CourseInfo] = None
    stats: ChatStats

class ChatListResponse(SuccessResponse):
    data: dict  # {"chats": List[ChatResponse]}

class CreateChatRequest(BaseModel):
    chat_type: Literal["general", "course"] = "general"  # 限制只能是 "general" 或 "course"
    first_message: str
    course_id: Optional[int] = None
    custom_prompt: Optional[str] = None
    ai_model: Literal["Star", "StarPlus", "StarCode"] = "Star"  # 限制AI模型选项
    search_enabled: bool = False
    context_mode: Literal["Economy", "Standard", "Premium", "Max"] = "Standard"  # 限制上下文模式选项
    file_ids: Optional[List[int]] = []
    folder_ids: Optional[List[int]] = []
    temporary_file_tokens: Optional[List[str]] = []
    stream: bool = False  # 是否启用streaming模式

class UpdateChatRequest(BaseModel):
    title: str

class ChatCreateResponse(SuccessResponse):
    data: dict  # Complex structure with chat, user_message, ai_message

class ChatUpdateResponse(SuccessResponse):
    data: dict  # {"chat": {"id": int, "title": str, "updated_at": datetime}} 