from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.schemas.common import BaseResponse


class CourseBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    semester_id: int


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None


class SemesterInfo(BaseModel):
    id: int
    name: str
    code: str


class CourseStats(BaseModel):
    file_count: int
    chat_count: int


class CourseResponse(CourseBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime
    semester: SemesterInfo
    stats: CourseStats


class CourseListResponse(BaseResponse):
    data: dict  # {"courses": List[CourseResponse]}


class CourseCreateResponse(BaseResponse):
    data: dict  # {"course": {"id": int, "created_at": datetime}}

class CourseUpdateResponse(BaseResponse):
    data: dict  # {"course": {"id": int, "updated_at": datetime}}