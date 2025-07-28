"""Course模块Pydantic模型 - 严格遵循FastAPI最佳实践"""
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Optional, Dict, Any
from datetime import datetime

from src.shared.schemas import BaseResponse


# ===== 请求模型 =====

class CreateSemesterRequest(BaseModel):
    """创建学期请求模型"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra={
            "examples": [
                {
                    "name": "2025第三学期",
                    "code": "2025S3", 
                    "start_date": "2025-09-01T00:00:00Z",
                    "end_date": "2025-12-31T23:59:59Z"
                }
            ]
        }
    )
    
    name: str = Field(..., min_length=1, max_length=100, description="学期名称")
    code: str = Field(..., min_length=1, max_length=20, description="学期代码")
    start_date: datetime = Field(..., description="开始时间")
    end_date: datetime = Field(..., description="结束时间")
    
    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        """验证结束时间必须晚于开始时间"""
        if info.data.get('start_date') and v <= info.data['start_date']:
            raise ValueError('结束时间必须晚于开始时间')
        return v
    
    @field_validator('code')
    @classmethod
    def validate_code_format(cls, v):
        """验证学期代码格式"""
        if not v.strip():
            raise ValueError('学期代码不能为空')
        return v.strip().upper()


class UpdateSemesterRequest(BaseModel):
    """更新学期请求模型"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra={
            "examples": [
                {
                    "name": "2025第三学期-更新",
                    "start_date": "2025-09-01T00:00:00Z",
                    "end_date": "2025-12-31T23:59:59Z",
                    "is_active": True
                }
            ]
        }
    )
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="学期名称")
    code: Optional[str] = Field(None, min_length=1, max_length=20, description="学期代码")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")
    is_active: Optional[bool] = Field(None, description="激活状态")
    
    @field_validator('code')
    @classmethod
    def validate_code_format(cls, v):
        """验证学期代码格式"""
        if v is not None and not v.strip():
            raise ValueError('学期代码不能为空')
        return v.strip().upper() if v else None
    
    @model_validator(mode='after')
    def validate_date_range(self):
        """验证日期范围"""
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValueError('结束时间必须晚于开始时间')
        return self


class CreateCourseRequest(BaseModel):
    """创建课程请求模型"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra={
            "examples": [
                {
                    "name": "数据结构与算法",
                    "code": "计算机科学1101A",
                    "description": "学习各种数据结构和算法",
                    "semester_id": 3
                }
            ]
        }
    )
    
    name: str = Field(..., min_length=1, max_length=100, description="课程名称")
    code: str = Field(..., min_length=1, max_length=20, description="课程代码")
    description: Optional[str] = Field(None, description="课程描述")
    semester_id: int = Field(..., gt=0, description="学期ID")
    
    @field_validator('name', 'code')
    @classmethod
    def validate_not_empty(cls, v):
        """验证字段不能为空"""
        if not v.strip():
            raise ValueError('该字段不能为空')
        return v.strip()


class UpdateCourseRequest(BaseModel):
    """更新课程请求模型"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra={
            "examples": [
                {
                    "name": "新课程名称",
                    "description": "新描述"
                }
            ]
        }
    )
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="课程名称")
    code: Optional[str] = Field(None, min_length=1, max_length=20, description="课程代码")
    description: Optional[str] = Field(None, description="课程描述")
    
    @field_validator('name', 'code')
    @classmethod
    def validate_not_empty(cls, v):
        """验证字段不能为空"""
        if v is not None and not v.strip():
            raise ValueError('该字段不能为空')
        return v.strip() if v else None


# ===== 数据模型 =====

class SemesterBasicData(BaseModel):
    """学期基础数据模型（用于关联显示）"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    code: str


class SemesterData(BaseModel):
    """学期完整数据模型"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 3,
                    "name": "2025第三学期",
                    "code": "2025S3",
                    "start_date": "2025-09-01T00:00:00Z",
                    "end_date": "2025-12-31T23:59:59Z",
                    "is_active": True,
                    "created_at": "2025-06-10T10:30:00Z",
                    "updated_at": "2025-06-11T10:30:00Z"
                }
            ]
        }
    )
    
    id: int
    name: str
    code: str
    start_date: datetime
    end_date: datetime
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class CourseStatsData(BaseModel):
    """课程统计数据模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "file_count": 5,
                    "chat_count": 2
                }
            ]
        }
    )
    
    file_count: int = Field(0, ge=0, description="文件数量")
    chat_count: int = Field(0, ge=0, description="聊天数量")


class CourseData(BaseModel):
    """课程完整数据模型"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "name": "数据结构与算法",
                    "code": "计算机科学1101A",
                    "description": "学习各种数据结构和算法",
                    "semester_id": 3,
                    "user_id": 2,
                    "created_at": "2025-06-10T09:00:00Z",
                    "semester": {
                        "id": 3,
                        "name": "2025第三学期",
                        "code": "2025S3"
                    },
                    "stats": {
                        "file_count": 5,
                        "chat_count": 2
                    }
                }
            ]
        }
    )
    
    id: int
    name: str
    code: str
    description: Optional[str] = None
    semester_id: int
    user_id: int
    created_at: datetime
    semester: Optional[SemesterBasicData] = None
    stats: Optional[CourseStatsData] = None
    
    @classmethod
    def from_orm_with_relations(cls, course):
        """从ORM对象创建实例，包含关联数据"""
        data = {
            "id": course.id,
            "name": course.name,
            "code": course.code,
            "description": course.description,
            "semester_id": course.semester_id,
            "user_id": course.user_id,
            "created_at": course.created_at,
        }
        
        # 添加学期信息
        if hasattr(course, 'semester') and course.semester:
            data["semester"] = SemesterBasicData.model_validate(course.semester)
        
        # 添加统计信息（暂时返回默认值）
        data["stats"] = CourseStatsData(file_count=0, chat_count=0)
        
        return cls.model_validate(data)


class CreateResultData(BaseModel):
    """创建结果数据模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 3,
                    "created_at": "2025-06-10T10:30:00Z"
                }
            ]
        }
    )
    
    id: int
    created_at: datetime


class UpdateResultData(BaseModel):
    """更新结果数据模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 3,
                    "updated_at": "2025-06-11T10:30:00Z"
                }
            ]
        }
    )
    
    id: int
    updated_at: datetime


class PaginationData(BaseModel):
    """分页数据模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "skip": 0,
                    "limit": 100,
                    "total": 150
                }
            ]
        }
    )
    
    skip: int = Field(ge=0)
    limit: int = Field(ge=1)
    total: int = Field(ge=0)


# ===== 响应模型 =====

class SemesterListResponse(BaseResponse[Dict[str, Any]]):
    """学期列表响应"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "data": {
                        "semesters": [
                            {
                                "id": 3,
                                "name": "2025第三学期",
                                "code": "2025S3",
                                "start_date": "2025-09-01T00:00:00Z",
                                "end_date": "2025-12-31T23:59:59Z",
                                "is_active": True,
                                "created_at": "2025-06-10T10:30:00Z"
                            }
                        ]
                    }
                }
            ]
        }
    )


class CreateSemesterResponse(BaseResponse[Dict[str, Any]]):
    """创建学期响应"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "data": {
                        "semester": {
                            "id": 3,
                            "created_at": "2025-06-10T10:30:00Z"
                        }
                    },
                    "message": "学期创建成功"
                }
            ]
        }
    )


class GetSemesterResponse(BaseResponse[Dict[str, Any]]):
    """获取学期详情响应"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "data": {
                        "semester": {
                            "id": 3,
                            "name": "2025第三学期",
                            "code": "2025S3",
                            "start_date": "2025-09-01T00:00:00Z",
                            "end_date": "2025-12-31T23:59:59Z",
                            "is_active": True,
                            "created_at": "2025-06-10T10:30:00Z"
                        }
                    }
                }
            ]
        }
    )


class UpdateSemesterResponse(BaseResponse[Dict[str, Any]]):
    """更新学期响应"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "data": {
                        "semester": {
                            "id": 3,
                            "updated_at": "2025-06-11T10:30:00Z"
                        }
                    },
                    "message": "学期更新成功"
                }
            ]
        }
    )


class SemesterCoursesResponse(BaseResponse[Dict[str, Any]]):
    """学期课程列表响应"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "data": {
                        "courses": [
                            {
                                "id": 1,
                                "name": "数据结构与算法",
                                "code": "计算机科学1101A",
                                "description": "学习各种数据结构和算法",
                                "semester_id": 3,
                                "user_id": 2,
                                "created_at": "2025-06-10T09:00:00Z",
                                "semester": {
                                    "id": 3,
                                    "name": "2025第三学期",
                                    "code": "2025S3"
                                },
                                "stats": {
                                    "file_count": 5,
                                    "chat_count": 2
                                }
                            }
                        ]
                    }
                }
            ]
        }
    )


class CourseListResponse(BaseResponse[Dict[str, Any]]):
    """课程列表响应"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "data": {
                        "courses": [
                            {
                                "id": 1,
                                "name": "数据结构与算法",
                                "code": "计算机科学1101A",
                                "description": "学习各种数据结构和算法",
                                "semester_id": 3,
                                "user_id": 2,
                                "created_at": "2025-06-10T09:00:00Z",
                                "semester": {
                                    "id": 3,
                                    "name": "2025第三学期",
                                    "code": "2025S3"
                                },
                                "stats": {
                                    "file_count": 5,
                                    "chat_count": 2
                                }
                            }
                        ]
                    }
                }
            ]
        }
    )


class CreateCourseResponse(BaseResponse[Dict[str, Any]]):
    """创建课程响应"""
    model_config = ConfigDict(
        json_schema_extra={  
            "examples": [
                {
                    "success": True,
                    "data": {
                        "course": {
                            "id": 3,
                            "created_at": "2025-06-10T10:30:00Z"
                        }
                    },
                    "message": "课程创建成功"
                }
            ]
        }
    )


class GetCourseResponse(BaseResponse[Dict[str, Any]]):
    """获取课程详情响应"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "data": {
                        "course": {
                            "id": 1,
                            "name": "数据结构与算法",
                            "code": "计算机科学1101A",
                            "description": "学习各种数据结构和算法",
                            "semester_id": 3,
                            "user_id": 2,
                            "created_at": "2025-06-10T09:00:00Z",
                            "semester": {
                                "id": 3,
                                "name": "2025第三学期",
                                "code": "2025S3"
                            },
                            "stats": {
                                "file_count": 5,
                                "chat_count": 2
                            }
                        }
                    }
                }
            ]
        }
    )


class UpdateCourseResponse(BaseResponse[Dict[str, Any]]):
    """更新课程响应"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "data": {
                        "course": {
                            "id": 3,
                            "updated_at": "2025-06-11T10:30:00Z"
                        }
                    },
                    "message": "课程更新成功"
                }
            ]
        }
    )


# ===== 删除响应使用共享的MessageResponse =====
# from src.shared.schemas import MessageResponse  # 在router中导入