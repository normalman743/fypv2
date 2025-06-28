from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class FileAttachment(BaseModel):
    id: int
    filename: str
    original_name: str
    file_size: int

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
    folder: Optional[dict] = None

class FileListResponse(BaseModel):
    files: List[FileResponse]

class FilePreviewResponse(BaseModel):
    id: int
    original_name: str
    file_type: str
    file_size: int
    mime_type: str
    created_at: datetime

class UploadFileRequest(BaseModel):
    course_id: int
    folder_id: int

class UploadFileResponse(BaseModel):
    file: FileResponse 