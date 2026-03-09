from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from app.schemas.common import SuccessResponse

class FolderStats(BaseModel):
    file_count: int

class FolderResponse(BaseModel):
    id: int
    name: str
    folder_type: str
    course_id: int
    is_default: bool
    created_at: datetime
    stats: FolderStats

class FolderListData(BaseModel):
    folders: List[FolderResponse]

class FolderListResponse(SuccessResponse):
    data: FolderListData

class CreateFolderRequest(BaseModel):
    name: str
    folder_type: str

class CreateFolderInner(BaseModel):
    id: int
    created_at: Any

class CreateFolderData(BaseModel):
    folder: CreateFolderInner

class CreateFolderResponse(SuccessResponse):
    data: CreateFolderData

class UpdateFolderRequest(BaseModel):
    name: Optional[str] = None
    folder_type: Optional[str] = None 