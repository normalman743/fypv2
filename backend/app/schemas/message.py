from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from app.schemas.common import SuccessResponse

class FileAttachment(BaseModel):
    id: int
    filename: str
    original_name: str
    file_size: int

class RAGSource(BaseModel):
    source_file: str
    chunk_id: int

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    content: str
    role: str  # "user" or "assistant"
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    created_at: datetime
    file_attachments: List[FileAttachment] = []
    rag_sources: Optional[List[RAGSource]] = []

class MessageListData(BaseModel):
    messages: List[dict]

class MessageListResponse(SuccessResponse):
    data: MessageListData

class SendMessageRequest(BaseModel):
    content: str
    file_ids: Optional[List[int]] = []
    folder_ids: Optional[List[int]] = []
    temporary_file_tokens: Optional[List[str]] = []
    stream: bool = False

class EditMessageRequest(BaseModel):
    content: str

class MessageSendData(BaseModel):
    user_message: dict
    ai_message: dict
    chat_title_updated: bool = False
    new_chat_title: Optional[str] = None

class MessageSendResponse(SuccessResponse):
    data: MessageSendData

class MessageUpdateInner(BaseModel):
    id: int
    content: str
    created_at: Any

class MessageUpdateData(BaseModel):
    message: MessageUpdateInner

class MessageUpdateResponse(SuccessResponse):
    data: MessageUpdateData