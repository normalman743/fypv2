from fastapi import HTTPException, status
from app.schemas.common import ErrorResponse


class BaseAPIException(HTTPException):
    """基础 API 异常类，确保统一的错误响应格式"""
    def __init__(self, status_code: int, error_code: str, message: str):
        error_response = ErrorResponse(
            success=False,
            error={
                "code": error_code,
                "message": message
            }
        )
        super().__init__(
            status_code=status_code,
            detail=error_response.model_dump()
        )


class ConflictError(BaseAPIException):
    """Conflict error (409)"""
    def __init__(self, detail: str, error_code: str = "CONFLICT"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code=error_code,
            message=detail
        )


class NotFoundError(BaseAPIException):
    """Not found error (404)"""
    def __init__(self, detail: str, error_code: str = "NOT_FOUND"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=error_code,
            message=detail
        )


class ForbiddenError(BaseAPIException):
    """Forbidden error (403)"""
    def __init__(self, detail: str, error_code: str = "FORBIDDEN"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code,
            message=detail
        )


class BadRequestError(BaseAPIException):
    """Bad request error (400)"""
    def __init__(self, detail: str, error_code: str = "BAD_REQUEST"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code,
            message=detail
        )


class UnauthorizedError(BaseAPIException):
    """Unauthorized error (401)"""
    def __init__(self, detail: str, error_code: str = "UNAUTHORIZED"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code,
            message=detail
        )


class InsufficientPermissionsError(BaseAPIException):
    """Insufficient permissions error (403)"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="INSUFFICIENT_PERMISSIONS",
            message=detail
        )


class InsufficientBalanceError(BaseAPIException):
    """余额不足异常 (402)"""
    def __init__(self, detail: str = "余额不足，请充值后继续使用"):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            error_code="INSUFFICIENT_BALANCE",
            message=detail
        )