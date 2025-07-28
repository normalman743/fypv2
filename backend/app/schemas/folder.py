from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.schemas.common import SuccessResponse

class FolderStats(BaseModel):
    file_count: int

class FolderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    folder_type: str
    course_id: int
    is_default: bool = False
    created_at: datetime
    stats: FolderStats

class FolderListResponse(SuccessResponse):
    data: dict  # {"folders": List[FolderResponse]}

class CreateFolderRequest(BaseModel):
    name: str
    folder_type: str

class CreateFolderResponse(SuccessResponse):
    data: dict  # {"folder": {"id": int, "created_at": datetime}}

class UpdateFolderRequest(BaseModel):
    name: Optional[str] = None
    folder_type: Optional[str] = None 