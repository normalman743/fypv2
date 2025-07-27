from pydantic import BaseModel, ConfigDict, Field, validator
from typing import Optional, List, Dict, Union
from datetime import datetime

from app.schemas.common import BaseResponse


class SemesterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="学期名称")
    code: str = Field(..., min_length=1, max_length=20, description="学期代码")
    start_date: datetime = Field(..., description="学期开始日期")
    end_date: datetime = Field(..., description="学期结束日期")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    @validator('code')
    def validate_code_format(cls, v):
        if not v.strip():
            raise ValueError('Semester code cannot be empty')
        return v.strip().upper()
    
    @validator('name')
    def validate_name_format(cls, v):
        if not v.strip():
            raise ValueError('Semester name cannot be empty')
        return v.strip()


class SemesterCreate(SemesterBase):
    """创建学期的请求模型"""
    pass


class SemesterUpdate(BaseModel):
    """更新学期的请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and values['start_date'] and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    @validator('code')
    def validate_code_format(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Semester code cannot be empty')
        return v.strip().upper() if v else v
    
    @validator('name')
    def validate_name_format(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Semester name cannot be empty')
        return v.strip() if v else v


class SemesterResponse(BaseModel):
    """学期响应模型 - 根据用户角色动态显示字段"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    code: str
    start_date: datetime
    end_date: datetime
    is_active: bool
    
    # 管理员才显示的元数据
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# 类型安全的数据容器
class SemesterListData(BaseModel):
    semesters: List[SemesterResponse]

class SemesterDetailData(BaseModel):
    semester: SemesterResponse

class SemesterOperationData(BaseModel):
    semester: Dict[str, Union[int, datetime]]


# 响应模型
class SemesterListResponse(BaseResponse):
    """学期列表响应"""
    data: SemesterListData


class SemesterDetailResponse(BaseResponse):
    """单个学期详情响应"""
    data: SemesterDetailData


class SemesterOperationResponse(BaseResponse):
    """学期操作响应（创建/更新）"""
    data: SemesterOperationData