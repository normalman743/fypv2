from pydantic import BaseModel, ConfigDict
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
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    chat_id: int
    content: str
    role: str  # "user" or "assistant"
    model_name: Optional[str] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    response_time_ms: Optional[int] = None
    rag_sources: Optional[Any] = None  # JSON field
    created_at: datetime
    context_size: Optional[int] = None
    direct_file_count: Optional[int] = 0
    rag_source_count: Optional[int] = 0
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    file_attachments: List[FileAttachment] = []

class MessageListResponse(SuccessResponse):
    data: dict  # {"messages": List[MessageResponse]}

class SendMessageRequest(BaseModel):
    content: str
    file_ids: Optional[List[int]] = []
    folder_ids: Optional[List[int]] = []
    temporary_file_tokens: Optional[List[str]] = []  # 临时文件通过token引用
    stream: bool = False  # 是否启用streaming模式

class EditMessageRequest(BaseModel):
    content: str

class MessageSendResponse(SuccessResponse):
    data: dict  # {"user_message": MessageResponse, "ai_message": MessageResponse, "chat_title_updated": bool, "new_chat_title": str}

class MessageUpdateResponse(SuccessResponse):
    data: dict  # {"message": {"id": int, "content": str, "updated_at": datetime}} 