from pydantic import BaseModel, EmailStr, ConfigDict, Field, validator
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
import re

# Constants
USERNAME_PATTERN = r'^[a-zA-Z0-9_]{3,20}$'
PASSWORD_PATTERN = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,128}$'
VERIFICATION_CODE_PATTERN = r'^[A-Z0-9]{6}$'


class UserRegister(BaseModel):
    """用户注册请求模型"""
    username: str = Field(
        ..., 
        min_length=3,
        max_length=20,
        title="Username",  
        description="Username for registration (3-20 chars, alphanumeric and underscore only)",
        examples=["john_doe", "jane_doe"]
    )
    email: EmailStr = Field(
        ..., 
        title="Email", 
        description="Email address for registration", 
        examples=["john@link.cuhk.edu.hk", "jane@link.cuhk.edu.hk"]
    )
    password: str = Field(
        ..., 
        title="Password", 
        description="Password (8-128 chars, must contain uppercase, lowercase, number and special char)", 
        min_length=8, 
        max_length=128, 
        examples=["StrongPassword123!"]
    )
    invite_code: str = Field(
        ..., 
        title="Invite Code", 
        description="Invite code for registration", 
        examples=["INVITE1234"]
    )
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(USERNAME_PATTERN, v):
            raise ValueError('Username must be 3-20 characters, containing only letters, numbers and underscore')
        return v.lower()  # Normalize to lowercase
    
    @validator('password')
    def validate_password(cls, v):
        if not re.match(PASSWORD_PATTERN, v):
            raise ValueError(
                'Password must contain at least one uppercase letter, '
                'one lowercase letter, one number and one special character'
            )
        return v


class UserLogin(BaseModel):
    """用户登录请求模型"""
    username: str = Field(..., min_length=3, max_length=20, description="Username or email for login", examples=["john_doe", "john@link.cuhk.edu.hk"])
    password: str = Field(..., min_length=8, max_length=128, description="Password for login", examples=["StrongPassword123!"])
    
    @validator('username')
    def normalize_username(cls, v):
        return v.lower()  # Normalize for case-insensitive login


class UserResponse(BaseModel):
    """用户信息响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    email: str
    role: Literal["admin", "user"] = "user"
    balance: float = Field(default=0.0, ge=0)
    total_spent: float = Field(default=0.0, ge=0)
    preferred_language: Literal["zh_CN", "en_US"] = "zh_CN"
    preferred_theme: Literal["light", "dark", "system"] = "light"
    last_opened_semester_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


class UserUpdate(BaseModel):
    """用户信息更新模型"""
    username: Optional[str] = Field(None, min_length=3, max_length=20)
    email: Optional[EmailStr] = None
    preferred_language: Optional[Literal["zh_CN", "en_US"]] = None
    preferred_theme: Optional[Literal["light", "dark", "system"]] = None
    last_opened_semester_id: Optional[int] = None
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if not re.match(USERNAME_PATTERN, v):
                raise ValueError('Username must be 3-20 characters, containing only letters, numbers and underscore')
            return v.lower()
        return v


class PasswordChangeRequest(BaseModel):
    """密码修改请求模型"""
    old_password: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v, values):
        if 'old_password' in values and v == values['old_password']:
            raise ValueError('New password must be different from old password')
        if not re.match(PASSWORD_PATTERN, v):
            raise ValueError(
                'Password must contain at least one uppercase letter, '
                'one lowercase letter, one number and one special character'
            )
        return v


class PasswordResetRequest(BaseModel):
    """密码重置请求模型"""
    email: EmailStr
    
    
class PasswordResetConfirm(BaseModel):
    """密码重置确认模型"""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('code')
    def validate_code(cls, v):
        if not re.match(VERIFICATION_CODE_PATTERN, v):
            raise ValueError('Verification code must be 6 uppercase letters or numbers')
        return v.upper()
    
    @validator('new_password')
    def validate_password(cls, v):
        if not re.match(PASSWORD_PATTERN, v):
            raise ValueError(
                'Password must contain at least one uppercase letter, '
                'one lowercase letter, one number and one special character'
            )
        return v


class EmailChangeRequest(BaseModel):
    """邮箱更改请求模型"""
    new_email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class EmailVerificationRequest(BaseModel):
    """邮箱验证请求模型"""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    
    @validator('code')
    def validate_code(cls, v):
        if not re.match(VERIFICATION_CODE_PATTERN, v):
            raise ValueError('Verification code must be 6 uppercase letters or numbers')
        return v.upper()


class ResendVerificationRequest(BaseModel):
    """重发验证码请求模型"""
    email: EmailStr


# 响应模型
class LoginResponse(BaseModel):
    """登录响应模型"""
    success: bool = True
    data: dict = Field(..., examples=[{
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "user": {
            "id": 1,
            "username": "john_doe",
            "email": "john@link.cuhk.edu.hk",
            "role": "user"
        }
    }])


class RegisterResponse(BaseModel):
    """注册响应模型"""
    success: bool = True
    data: dict = Field(..., examples=[{
        "user": {
            "id": 1,
            "username": "john_doe",
            "email": "john@link.cuhk.edu.hk",
            "role": "user"
        },
        "message": "注册成功！验证邮件已发送，如果没有收到，请检查垃圾邮件或稍后再试。"
    }])


class UserProfileResponse(BaseModel):
    """用户信息响应模型"""
    success: bool = True
    data: UserResponse = Field(..., examples=[{
        "id": 1,
        "username": "john_doe",
        "email": "john@link.cuhk.edu.hk",
        "role": "user",
        "balance": 100.0,
        "total_spent": 50.0,
        "preferred_language": "zh_CN",
        "is_active": True,
        "email_verified": True,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }])


class MessageResponse(BaseModel):
    """通用消息响应模型"""
    success: bool = True
    data: dict = Field(..., examples=[{
        "message": "操作成功"
    }])


class UserStatusUpdate(BaseModel):
    """用户状态更新模型（管理员用）"""
    is_active: Optional[bool] = None
    role: Optional[Literal["admin", "user"]] = None
    balance: Optional[float] = Field(None, ge=0)
    
    @validator('balance')
    def validate_balance(cls, v):
        if v is not None and v < 0:
            raise ValueError('Balance cannot be negative')
        return v


class UserBriefResponse(BaseModel):
    """用户简要信息响应（用于列表等场景）"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    email: str
    role: Literal["admin", "user"]
    is_active: bool


class UserStatsResponse(BaseModel):
    """用户统计信息响应"""
    total_courses: int = 0
    total_files: int = 0
    storage_used: int = 0  # in bytes
    last_active: Optional[datetime] = None
