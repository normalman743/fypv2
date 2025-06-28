from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel
from datetime import datetime

T = TypeVar('T')

class BaseResponse(BaseModel):
    """Base response model"""
    success: bool

class SuccessResponse(BaseResponse):
    """Success response model"""
    success: bool = True
    data: Optional[Any] = None

class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    error: dict

class ResponseModel(BaseModel, Generic[T]):
    """通用响应模型"""
    success: bool
    data: Optional[T] = None
    error: Optional[dict] = None

class PaginationParams(BaseModel):
    """分页参数"""
    page: int = 1
    size: int = 20

class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    items: list[T]
    total: int
    page: int
    size: int
    pages: int
