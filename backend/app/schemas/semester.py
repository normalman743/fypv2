from pydantic import BaseModel
from typing import Optional, List, Any
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


class SemesterListData(BaseModel):
    semesters: List[SemesterResponse]

class SemesterListResponse(BaseResponse):
    data: SemesterListData

class SemesterCreateInner(BaseModel):
    id: int
    created_at: Any

class SemesterCreateData(BaseModel):
    semester: SemesterCreateInner

class SemesterCreateResponse(BaseResponse):
    data: SemesterCreateData

class SemesterUpdateInner(BaseModel):
    id: int
    updated_at: Any

class SemesterUpdateData(BaseModel):
    semester: SemesterUpdateInner

class SemesterUpdateResponse(BaseResponse):
    data: SemesterUpdateData