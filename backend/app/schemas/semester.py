from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.schemas.common import BaseResponse


class SemesterBase(BaseModel):
    name: str
    code: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SemesterCreate(SemesterBase):
    pass


class SemesterUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class SemesterResponse(SemesterBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SemesterListResponse(BaseResponse):
    data: dict  # {"semesters": List[SemesterResponse]}


class SemesterCreateResponse(BaseResponse):
    data: dict  # {"semester": {"id": int, "created_at": datetime}}


class SemesterUpdateResponse(BaseResponse):
    data: dict  # {"semester": {"id": int, "updated_at": datetime}}