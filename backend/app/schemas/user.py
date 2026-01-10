from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import Optional, List, Literal
from datetime import datetime
import re
from app.core.config import settings

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    invite_code: str
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError('用户名必须至少3个字符')
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email_domain(cls, v: EmailStr) -> EmailStr:
        # 暂时硬编码允许的邮箱域名
        email_str = str(v).lower()
        if not (email_str.endswith('@link.cuhk.edu.hk') or email_str.endswith('@icu.584743.xyz')):
            raise ValueError('邮箱必须以 @link.cuhk.edu.hk 结尾')
        
        # 原配置方式（保留备用）：
        # # 如果启用了邮箱验证且设置了允许的域名列表
        # if settings.registration_email_verification and settings.allowed_email_domains_list:
        #     email_str = str(v).lower()
        #     email_domain = email_str.split('@')[-1] if '@' in email_str else ""
        #     
        #     # 检查是否匹配允许的域名
        #     email_domain_valid = any(
        #         email_domain == domain or email_domain.endswith(f".{domain}")
        #         for domain in settings.allowed_email_domains_list
        #     )
        #     
        #     if not email_domain_valid:
        #         raise ValueError(f"邮箱域名必须是: {', '.join(settings.allowed_email_domains_list)}")
        
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('密码必须至少8个字符')
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('密码必须包含字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含数字')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    email: str
    role: Literal["admin", "user"] = "user"
    balance: float
    total_spent: float
    preferred_language: Literal["zh_CN", "en_US"] = "zh_CN"
    preferred_theme: Literal["light", "dark", "system"] = "light"
    last_opened_semester_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    is_active: bool

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    preferred_language: Literal["zh_CN", "en_US"] = "zh_CN"
    preferred_theme: Literal["light", "dark", "system"] = "light"
    last_opened_semester_id: Optional[int] = None

class EmailVerificationRequest(BaseModel):
    email: EmailStr
    code: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr
