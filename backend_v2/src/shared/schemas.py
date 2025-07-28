from pydantic import BaseModel
from typing import TypeVar, Generic, Optional, Any

# 泛型类型变量
T = TypeVar('T')


class SuccessResponse(BaseModel, Generic[T]):
    """统一成功响应模型"""
    success: bool = True
    data: T


class MessageResponse(BaseModel):
    """简单消息响应"""
    success: bool = True
    message: str


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
    "SuccessResponse",
    "MessageResponse", 
    "PaginatedResponse",
    "PaginationMeta",
    "ErrorResponse",
    "ErrorDetail"
]