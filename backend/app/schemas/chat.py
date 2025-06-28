from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

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
    created_at: datetime
    updated_at: datetime
    course: Optional[CourseInfo]
    stats: ChatStats

class ChatListResponse(BaseModel):
    chats: List[ChatResponse]

class CreateChatRequest(BaseModel):
    chat_type: str
    first_message: str
    course_id: Optional[int] = None
    custom_prompt: Optional[str] = None
    file_ids: Optional[List[int]] = None

class UpdateChatRequest(BaseModel):
    title: str

class CreateChatResponse(BaseModel):
    chat: ChatResponse
    user_message: dict
    ai_message: dict
    chat_title_updated: bool
    new_chat_title: Optional[str] = None 