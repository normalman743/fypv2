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

class FileListData(BaseModel):
    files: List[FileResponse]

class FileListResponse(SuccessResponse):
    data: FileListData

class FilePreviewResponse(SuccessResponse):
    data: dict

class UploadFileRequest(BaseModel):
    course_id: int
    folder_id: int

class UploadFileData(BaseModel):
    file: dict

class UploadFileResponse(SuccessResponse):
    data: UploadFileData

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

class UploadTemporaryFileData(BaseModel):
    file: dict

class UploadTemporaryFileResponse(SuccessResponse):
    data: UploadTemporaryFileData