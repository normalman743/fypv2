from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class RagSource(BaseModel):
    source_file: str
    chunk_id: int

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    content: str
    role: str
    tokens_used: Optional[int]
    cost: Optional[float]
    created_at: datetime
    file_attachments: List[dict] = []
    rag_sources: Optional[List[RagSource]] = None

class MessageListResponse(BaseModel):
    messages: List[MessageResponse]

class SendMessageRequest(BaseModel):
    content: str
    file_ids: Optional[List[int]] = None

class SendMessageResponse(BaseModel):
    user_message: MessageResponse
    ai_message: MessageResponse
    chat_title_updated: bool
    new_chat_title: Optional[str] = None

class UpdateMessageRequest(BaseModel):
    content: str

class UpdateMessageResponse(BaseModel):
    message: dict  # 包含id, content, updated_at 