from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ErrorDetail(BaseModel):
    """错误详情模型"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """统一错误响应模型"""
    success: bool = False
    error: ErrorDetail


# 基础异常类
class BaseAPIException(HTTPException):
    """API 基础异常类"""
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details
        
        # 构造 FastAPI HTTPException 的 detail
        detail = ErrorResponse(
            error=ErrorDetail(
                code=code,
                message=message,
                details=details
            )
        ).model_dump()
        
        super().__init__(status_code=status_code, detail=detail)


# 常用异常类
class BadRequestError(BaseAPIException):
    """400 错误请求"""
    def __init__(self, message: str = "请求参数错误", details: Optional[Dict[str, Any]] = None):
        super().__init__("BAD_REQUEST", message, 400, details)


class UnauthorizedError(BaseAPIException):
    """401 未认证"""
    def __init__(self, message: str = "未认证或认证已过期", details: Optional[Dict[str, Any]] = None):
        super().__init__("UNAUTHORIZED", message, 401, details)


class ForbiddenError(BaseAPIException):
    """403 禁止访问"""
    def __init__(self, message: str = "权限不足", details: Optional[Dict[str, Any]] = None):
        super().__init__("FORBIDDEN", message, 403, details)


class NotFoundError(BaseAPIException):
    """404 资源不存在"""
    def __init__(self, message: str = "资源不存在", details: Optional[Dict[str, Any]] = None):
        super().__init__("NOT_FOUND", message, 404, details)


class ConflictError(BaseAPIException):
    """409 冲突"""
    def __init__(self, message: str = "资源冲突", details: Optional[Dict[str, Any]] = None):
        super().__init__("CONFLICT", message, 409, details)


class InternalServerError(BaseAPIException):
    """500 服务器内部错误"""
    def __init__(self, message: str = "服务器内部错误", details: Optional[Dict[str, Any]] = None):
        super().__init__("INTERNAL_SERVER_ERROR", message, 500, details)


def setup_exception_handlers(app) -> None:
    """设置异常处理器"""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """统一 HTTP 异常响应格式"""
        # 检查 detail 是否已经是我们的错误格式
        if isinstance(exc.detail, dict) and "success" in exc.detail:
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail
            )
        
        # 否则使用默认格式
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=f"HTTP_{exc.status_code}",
                    message=str(exc.detail)
                )
            ).model_dump()
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """422 验证错误处理"""
        errors = []
        for error in exc.errors():
            field = " -> ".join(str(x) for x in error["loc"])
            errors.append(f"{field}: {error['msg']}")
        
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="VALIDATION_ERROR",
                    message="请求数据验证失败",
                    details={"errors": errors}
                )
            ).model_dump()
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """全局异常处理"""
        logger.exception(f"Unhandled exception: {exc}")
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="INTERNAL_SERVER_ERROR",
                    message="服务器内部错误，请稍后重试"
                )
            ).model_dump()
        )