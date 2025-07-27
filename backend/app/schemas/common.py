from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar('T')

class BaseResponse(BaseModel):
    """Base response model"""
    success: bool

class SuccessResponse(BaseResponse):
    """Success response model"""
    success: bool = True
    data: Optional[Any] = Field(None, examples=[
        {"message": "操作成功"},
        {"user": {"id": 1, "username": "john_doe", "email": "john@example.com"}},
        {"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "token_type": "bearer"}
    ])
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "data": {
                        "message": "操作成功"
                    }
                },
                {
                    "success": True,
                    "data": {
                        "user": {
                            "id": 1,
                            "username": "john_doe",
                            "email": "john@link.cuhk.edu.hk",
                            "role": "user",
                            "is_active": True
                        }
                    }
                },
                {
                    "success": True,
                    "data": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "user": {
                            "id": 1,
                            "username": "john_doe",
                            "email": "john@link.cuhk.edu.hk"
                        }
                    }
                }
            ]
        }
    }

class ErrorDetail(BaseModel):
    """错误详情模型"""
    code: str = Field(..., examples=["INVALID_INPUT", "USER_NOT_FOUND"])
    message: str = Field(..., examples=["输入参数无效", "用户未找到"])
    details: Optional[dict] = Field(None, examples=[{"field": "error description"}])

class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    error: ErrorDetail
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": False,
                    "error": {
                        "code": "USER_NOT_FOUND",
                        "message": "用户未找到"
                    }
                },
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_INPUT",
                        "message": "输入参数无效",
                        "details": {"username": "用户名格式错误"}
                    }
                }
            ]
        }
    }

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
