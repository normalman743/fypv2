from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class CourseBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    semester_id: int

class CourseCreate(CourseBase):
    pass

class CourseUpdate(CourseBase):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    semester_id: Optional[int] = None

class CourseInDBBase(CourseBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Course(CourseInDBBase):
    pass
