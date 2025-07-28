"""Auth模块 - 用户认证和授权功能"""

from .models import User, EmailVerification, PasswordReset, InviteCode
from .schemas import (
    UserRegister, UserLogin, UserUpdate, UserResponse,
    PasswordChangeRequest, ForgotPasswordRequest, ResetPasswordRequest,
    EmailVerificationRequest, ResendVerificationRequest,
    LoginResponse, RegisterResponse, UserProfileResponse, MessageResponse
)
from .service import AuthService
from .router import router

__all__ = [
    # Models
    "User",
    "EmailVerification", 
    "PasswordReset",
    "InviteCode",
    
    # Schemas
    "UserRegister",
    "UserLogin", 
    "UserUpdate",
    "UserResponse",
    "PasswordChangeRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "EmailVerificationRequest",
    "ResendVerificationRequest",
    "LoginResponse",
    "RegisterResponse", 
    "UserProfileResponse",
    "MessageResponse",
    
    # Service
    "AuthService",
    
    # Router
    "router",
]