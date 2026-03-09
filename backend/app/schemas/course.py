from pydantic import BaseModel
from typing import Optional, List, Any
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
    id: int
    user_id: int
    created_at: datetime
    semester: SemesterInfo
    stats: CourseStats

    class Config:
        from_attributes = True


class CourseListData(BaseModel):
    courses: List[CourseResponse]

class CourseListResponse(BaseResponse):
    data: CourseListData

class CourseCreateInner(BaseModel):
    id: int
    created_at: Any

class CourseCreateData(BaseModel):
    course: CourseCreateInner

class CourseCreateResponse(BaseResponse):
    data: CourseCreateData

class CourseUpdateInner(BaseModel):
    id: int
    updated_at: Any

class CourseUpdateData(BaseModel):
    course: CourseUpdateInner

class CourseUpdateResponse(BaseResponse):
    data: CourseUpdateData