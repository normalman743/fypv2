from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import Any, Dict, Optional, Callable
import logging
import functools

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
    def __init__(self, message: str = "请求参数错误", error_code: str = "BAD_REQUEST", details: Optional[Dict[str, Any]] = None):
        super().__init__(error_code, message, 400, details)
        self.error_code = error_code


class UnauthorizedError(BaseAPIException):
    """401 未认证"""
    def __init__(self, message: str = "未认证或认证已过期", error_code: str = "UNAUTHORIZED", details: Optional[Dict[str, Any]] = None):
        super().__init__(error_code, message, 401, details)
        self.error_code = error_code


class ForbiddenError(BaseAPIException):
    """403 禁止访问"""
    def __init__(self, message: str = "权限不足", error_code: str = "FORBIDDEN", details: Optional[Dict[str, Any]] = None):
        super().__init__(error_code, message, 403, details)
        self.error_code = error_code


class NotFoundError(BaseAPIException):
    """404 资源不存在"""
    def __init__(self, message: str = "资源不存在", error_code: str = "NOT_FOUND", details: Optional[Dict[str, Any]] = None):
        super().__init__(error_code, message, 404, details)
        self.error_code = error_code


class ConflictError(BaseAPIException):
    """409 冲突"""
    def __init__(self, message: str = "资源冲突", error_code: str = "CONFLICT", details: Optional[Dict[str, Any]] = None):
        super().__init__(error_code, message, 409, details)
        self.error_code = error_code


class InternalServerError(BaseAPIException):
    """500 服务器内部错误"""
    def __init__(self, message: str = "服务器内部错误", error_code: str = "INTERNAL_SERVER_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(error_code, message, 500, details)
        self.error_code = error_code


# Service层异常基类
class BaseServiceException(Exception):
    """Service层基础异常类"""
    status_code: int = 500
    error_code: str = "SERVICE_ERROR"
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code or self.__class__.error_code
        self.details = details
        super().__init__(message)


# 具体的Service异常类（基于类型注解自动映射状态码）
class NotFoundServiceException(BaseServiceException):
    """Service层资源不存在异常"""
    status_code: int = 404
    error_code: str = "NOT_FOUND"


class AccessDeniedServiceException(BaseServiceException):
    """Service层访问被拒绝异常"""
    status_code: int = 403
    error_code: str = "ACCESS_DENIED"


class UnauthorizedServiceException(BaseServiceException):
    """Service层未认证异常"""
    status_code: int = 401
    error_code: str = "UNAUTHORIZED"


class ConflictServiceException(BaseServiceException):
    """Service层资源冲突异常"""
    status_code: int = 409
    error_code: str = "CONFLICT"


class ValidationServiceException(BaseServiceException):
    """Service层验证错误异常"""
    status_code: int = 422
    error_code: str = "VALIDATION_ERROR"


class BadRequestServiceException(BaseServiceException):
    """Service层请求错误异常"""
    status_code: int = 400
    error_code: str = "BAD_REQUEST"


# Service异常处理装饰器
def handle_service_exceptions(func: Callable) -> Callable:
    """处理Service层异常的装饰器（自动检测同步/异步）"""
    import asyncio
    import inspect
    
    if inspect.iscoroutinefunction(func):
        # 异步版本
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except BaseServiceException as e:
                # 基于类型注解自动映射状态码（遵循开闭原则）
                status_code = getattr(e, 'status_code', 500)
                
                raise BaseAPIException(
                    code=e.error_code,
                    message=e.message,
                    status_code=status_code,
                    details=e.details
                )
            except Exception as e:
                logger.exception(f"Unexpected error in {func.__name__}: {e}")
                raise InternalServerError(
                    message="服务器内部错误",
                    error_code="INTERNAL_SERVER_ERROR"
                )
        
        return async_wrapper
    else:
        # 同步版本
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BaseServiceException as e:
                # 基于类型注解自动映射状态码（遵循开闭原则）
                status_code = getattr(e, 'status_code', 500)
                
                raise BaseAPIException(
                    code=e.error_code,
                    message=e.message,
                    status_code=status_code,
                    details=e.details
                )
            except Exception as e:
                logger.exception(f"Unexpected error in {func.__name__}: {e}")
                raise InternalServerError(
                    message="服务器内部错误",
                    error_code="INTERNAL_SERVER_ERROR"
                )
        
        return sync_wrapper


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