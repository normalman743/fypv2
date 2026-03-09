from pydantic import BaseModel
from typing import Optional, List, Literal, Any
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
    chat_type: Literal["general", "course"] = "general"
    course_id: Optional[int] = None
    user_id: int
    custom_prompt: Optional[str] = None
    ai_model: Literal["Star", "StarPlus", "StarCode"] = "Star"
    search_enabled: bool = False
    context_mode: Literal["Economy", "Standard", "Premium", "Max"] = "Standard"
    created_at: datetime
    updated_at: datetime
    course: Optional[CourseInfo] = None
    stats: ChatStats

class ChatListData(BaseModel):
    chats: List[ChatResponse]

class ChatListResponse(SuccessResponse):
    data: ChatListData

class CreateChatRequest(BaseModel):
    chat_type: Literal["general", "course"] = "general"
    first_message: str
    course_id: Optional[int] = None
    custom_prompt: Optional[str] = None
    ai_model: Literal["Star", "StarPlus", "StarCode"] = "Star"
    search_enabled: bool = False
    context_mode: Literal["Economy", "Standard", "Premium", "Max"] = "Standard"
    file_ids: Optional[List[int]] = []
    folder_ids: Optional[List[int]] = []
    temporary_file_tokens: Optional[List[str]] = []
    stream: bool = False

class UpdateChatRequest(BaseModel):
    title: str

class ChatCreateMessageData(BaseModel):
    id: int
    chat_id: int
    content: str
    role: str
    tokens_used: Optional[int] = None
    cost: Optional[Any] = None
    created_at: Any
    file_attachments: List[dict] = []
    temporary_file_attachments: Optional[List[dict]] = None
    rag_sources: Optional[List[dict]] = None

class ChatCreateChatData(BaseModel):
    id: int
    title: str
    chat_type: str
    course_id: Optional[int] = None
    user_id: int
    custom_prompt: Optional[str] = None
    ai_model: str
    search_enabled: bool
    context_mode: str
    created_at: Any
    updated_at: Any

class ChatCreateData(BaseModel):
    chat: ChatCreateChatData
    user_message: ChatCreateMessageData
    ai_message: ChatCreateMessageData
    chat_title_updated: bool = False
    new_chat_title: Optional[str] = None

class ChatCreateResponse(SuccessResponse):
    data: ChatCreateData

class ChatUpdateInner(BaseModel):
    id: int
    title: str
    updated_at: Any

class ChatUpdateData(BaseModel):
    chat: ChatUpdateInner

class ChatUpdateResponse(SuccessResponse):
    data: ChatUpdateData