from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from app.schemas.common import SuccessResponse

class FileAttachment(BaseModel):
    id: int
    filename: str
    original_name: str
    file_size: int

class FolderInfo(BaseModel):
    id: int
    name: str
    folder_type: str

class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    physical_file_id: int
    original_name: str
    file_type: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    course_id: Optional[int] = None
    folder_id: Optional[int] = None
    user_id: int
    is_processed: Optional[bool] = False
    processing_status: Optional[str] = "pending"
    processing_error: Optional[str] = None
    processed_at: Optional[datetime] = None
    chunk_count: Optional[int] = 0
    content_preview: Optional[str] = None
    created_at: datetime
    scope: Optional[str] = "course"
    visibility: Optional[str] = "private"
    is_shareable: Optional[bool] = True
    share_settings: Optional[Any] = None  # JSON field
    tags: Optional[List[str]] = None  # JSON field
    description: Optional[str] = None
    file_hash: Optional[str] = None
    updated_at: Optional[datetime] = None
    folder: Optional[FolderInfo] = None

class FileListResponse(SuccessResponse):
    data: dict  # {"files": List[FileResponse]}

class FilePreviewResponse(SuccessResponse):
    data: dict  # FileResponse fields

class UploadFileRequest(BaseModel):
    course_id: int
    folder_id: int

class UploadFileResponse(SuccessResponse):
    data: dict  # {"file": FileResponse}

class TemporaryFileResponse(BaseModel):
    id: int
    token: str
    original_name: str
    file_type: str
    file_size: int
    mime_type: str
    expires_at: datetime
    purpose: Optional[str] = None
    created_at: datetime

class UploadTemporaryFileResponse(SuccessResponse):
    data: dict  # {"file": TemporaryFileResponse} 