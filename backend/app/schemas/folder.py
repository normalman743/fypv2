from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

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

class FolderListResponse(BaseModel):
    folders: List[FolderResponse]

class CreateFolderRequest(BaseModel):
    name: str
    folder_type: str

class CreateFolderResponse(BaseModel):
    folder: dict  # 包含id和created_at

class UpdateFolderRequest(BaseModel):
    name: Optional[str] = None
    folder_type: Optional[str] = None 