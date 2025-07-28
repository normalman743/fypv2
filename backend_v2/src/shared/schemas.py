from pydantic import BaseModel, Field, ConfigDict
from typing import TypeVar, Generic, Optional, Any

# 泛型类型变量
T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """统一响应格式基类"""
    success: bool = Field(default=True, description="操作是否成功")
    data: T = Field(..., description="响应数据")
    message: Optional[str] = Field(None, description="操作消息")


class SuccessResponse(BaseModel, Generic[T]):
    """统一成功响应模型"""
    success: bool = True
    data: T


class EmptyData(BaseModel):
    """空数据模型 - 用于只返回消息的响应"""
    pass


class MessageResponse(BaseResponse[EmptyData]):
    """标准消息响应 - message在根级别，data为空对象"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "success": True,
                "data": {},
                "message": "操作成功"
            }]
        }
    )


class PaginationMeta(BaseModel):
    """分页元数据"""
    page: int
    size: int
    total: int
    pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    success: bool = True
    data: list[T]
    meta: PaginationMeta


# 重新导出异常相关的 schemas
from .exceptions import ErrorResponse, ErrorDetail

__all__ = [
    "BaseResponse",
    "SuccessResponse",
    "MessageResponse", 
    "PaginatedResponse",
    "PaginationMeta",
    "ErrorResponse",
    "ErrorDetail"
]