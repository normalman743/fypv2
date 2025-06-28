from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class SemesterBase(BaseModel):
    name: str
    code: str
    start_date: datetime
    end_date: datetime
    is_active: Optional[bool] = True

class SemesterCreate(SemesterBase):
    pass

class SemesterUpdate(SemesterBase):
    name: Optional[str] = None
    code: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class SemesterInDBBase(SemesterBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Semester(SemesterInDBBase):
    pass
