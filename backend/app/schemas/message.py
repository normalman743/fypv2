from pydantic import BaseModel
from typing import Optional, List
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

class MessageListResponse(SuccessResponse):
    data: dict  # {"messages": List[MessageResponse]}

class SendMessageRequest(BaseModel):
    content: str
    file_ids: Optional[List[int]] = []
    folder_ids: Optional[List[int]] = []
    temporary_file_tokens: Optional[List[str]] = []  # 临时文件通过token引用

class EditMessageRequest(BaseModel):
    content: str

class MessageSendResponse(SuccessResponse):
    data: dict  # {"user_message": MessageResponse, "ai_message": MessageResponse, "chat_title_updated": bool, "new_chat_title": str}

class MessageUpdateResponse(SuccessResponse):
    data: dict  # {"message": {"id": int, "content": str, "updated_at": datetime}} 