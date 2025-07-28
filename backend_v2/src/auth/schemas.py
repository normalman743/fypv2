"""Auth模块的Pydantic模式定义"""
from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
import re
from src.shared.schemas import BaseResponse

# 从现有backend复制验证规则
USERNAME_PATTERN = r'^[a-zA-Z0-9_]{3,20}$'
VERIFICATION_CODE_PATTERN = r'^[A-Z0-9]{6}$'

def _validate_username(username: str) -> str:
    """统一的用户名验证函数"""
    if not re.match(USERNAME_PATTERN, username):
        raise ValueError('用户名必须是3-20个字符，只能包含字母、数字和下划线')
    return username.lower()

def _validate_password(password: str) -> str:
    """统一的密码复杂度验证函数"""
    if len(password) < 8:
        raise ValueError('密码至少8位')
    if len(password) > 128:
        raise ValueError('密码不能超过128位')
    if not re.search(r'[A-Z]', password):
        raise ValueError('密码必须包含至少一个大写字母')
    if not re.search(r'[a-z]', password):
        raise ValueError('密码必须包含至少一个小写字母')
    if not re.search(r'\d', password):
        raise ValueError('密码必须包含至少一个数字')
    if not re.search(r'[@$!%*?&]', password):
        raise ValueError('密码必须包含至少一个特殊字符 (@$!%*?&)')
    return password

def _validate_verification_code(code: str) -> str:
    """统一的验证码验证函数"""
    if not re.match(VERIFICATION_CODE_PATTERN, code):
        raise ValueError('验证码必须是6位大写字母或数字')
    return code.upper()


# ===== 请求模式 =====

class UserRegister(BaseModel):
    """用户注册请求模型"""
    username: str = Field(
        ..., 
        min_length=3,
        max_length=20,
        description="用户名 (3-20位，仅支持字母、数字、下划线)"
    )
    email: EmailStr = Field(
        ..., 
        description="邮箱地址"
    )
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=128, 
        description="密码 (8-128位，必须包含大小写字母、数字和特殊字符)"
    )
    invite_code: str = Field(
        ..., 
        description="邀请码"
    )
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        return _validate_username(v)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        return _validate_password(v)


class UserLogin(BaseModel):
    """用户登录请求模型"""
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50,  # 支持邮箱登录，所以长度放宽
        description="用户名或邮箱"
    )
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=128, 
        description="密码"
    )
    
    @field_validator('username')
    @classmethod
    def normalize_username(cls, v):
        return v.lower()  # 标准化为小写，支持大小写不敏感登录


class UserUpdate(BaseModel):
    """用户信息更新模型"""
    username: Optional[str] = Field(
        None, 
        min_length=3, 
        max_length=20,
        description="新用户名 (可选)"
    )
    preferred_language: Optional[Literal["zh_CN", "en_US"]] = Field(
        None,
        description="首选语言 (可选)"
    )
    preferred_theme: Optional[Literal["light", "dark", "system"]] = Field(
        None,
        description="首选主题 (可选)"
    )
    last_opened_semester_id: Optional[int] = Field(
        None,
        description="最后打开的学期ID (可选)"
    )
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v is not None:
            return _validate_username(v)
        return v


class PasswordChangeRequest(BaseModel):
    """密码修改请求模型"""
    old_password: str = Field(
        ..., 
        min_length=8, 
        max_length=128,
        description="当前密码"
    )
    new_password: str = Field(
        ..., 
        min_length=8, 
        max_length=128,
        description="新密码"
    )
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v, info):
        # Pydantic V2 中使用 info.data 获取其他字段值
        if info.data and 'old_password' in info.data and v == info.data['old_password']:
            raise ValueError('新密码不能与旧密码相同')
        return _validate_password(v)


class ForgotPasswordRequest(BaseModel):
    """忘记密码请求模型"""
    email: EmailStr = Field(
        ...,
        description="注册邮箱地址"
    )


class ResetPasswordRequest(BaseModel):
    """重置密码请求模型"""
    reset_token: str = Field(
        ...,
        description="重置令牌"
    )
    new_password: str = Field(
        ..., 
        min_length=8, 
        max_length=128,
        description="新密码"
    )
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        return _validate_password(v)


class EmailVerificationRequest(BaseModel):
    """邮箱验证请求模型"""
    email: EmailStr = Field(
        ...,
        description="邮箱地址"
    )
    code: str = Field(
        ..., 
        min_length=6, 
        max_length=6,
        description="验证码"
    )
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        return _validate_verification_code(v)


class ResendVerificationRequest(BaseModel):
    """重发验证码请求模型"""
    email: EmailStr = Field(
        ...,
        description="邮箱地址"
    )


# ===== 响应模式 =====

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
    # 新增字段
    email_verified: bool = False
    last_login_at: Optional[datetime] = None


# ===== 响应数据类型定义 =====

class LoginData(BaseModel):
    """登录响应数据"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user: UserResponse = Field(..., description="用户信息")


class RegisterData(BaseModel):
    """注册响应数据"""
    user: UserResponse = Field(..., description="用户信息")


class MessageData(BaseModel):
    """消息响应数据"""
    message: str = Field(..., description="操作消息")



class LoginResponse(BaseResponse[LoginData]):
    """登录响应模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "success": True,
                "data": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 86400,
                    "user": {
                        "id": 1,
                        "username": "john_doe",
                        "email": "john@example.com",
                        "role": "user",
                        "balance": 1.0,
                        "email_verified": True
                    }
                }
            }]
        }
    )


class RegisterResponse(BaseResponse[RegisterData]):
    """注册响应模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "success": True,
                "data": {
                    "user": {
                        "id": 1,
                        "username": "john_doe",
                        "email": "john@584743.xyz",
                        "role": "user",
                        "balance": 1.0,
                        "email_verified": False,
                        "created_at": "2024-01-01T00:00:00Z"
                    }
                },
                "message": "注册成功！验证邮件已发送，如果没有收到，请检查垃圾邮件或稍后再试。"
            }]
        }
    )


class UserProfileResponse(BaseResponse[UserResponse]):
    """用户信息响应模型"""
    pass


class MessageResponse(BaseResponse[MessageData]):
    """通用消息响应模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "success": True,
                "data": {
                    "message": "操作成功"
                }
            }]
        }
    )