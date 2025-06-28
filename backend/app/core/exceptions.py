from fastapi import HTTPException, status


class ConflictError(HTTPException):
    """Conflict error (409)"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "error": {
                    "code": "CONFLICT",
                    "message": detail
                }
            }
        )


class NotFoundError(HTTPException):
    """Not found error (404)"""
    def __init__(self, detail: str, error_code: str = "NOT_FOUND"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": error_code,
                    "message": detail
                }
            }
        )


class ForbiddenError(HTTPException):
    """Forbidden error (403)"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "FORBIDDEN",
                    "message": detail
                }
            }
        )


class BadRequestError(HTTPException):
    """Bad request error (400)"""
    def __init__(self, detail: str, error_code: str = "BAD_REQUEST"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": error_code,
                    "message": detail
                }
            }
        )


class UnauthorizedError(HTTPException):
    """Unauthorized error (401)"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": detail
                }
            }
        )