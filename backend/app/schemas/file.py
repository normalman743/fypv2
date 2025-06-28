from pydantic import BaseModel
from typing import Optional, List
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
    id: int
    original_name: str
    file_type: str
    file_size: int
    mime_type: str
    course_id: int
    folder_id: int
    user_id: int
    is_processed: bool
    processing_status: str
    created_at: datetime
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