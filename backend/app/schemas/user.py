from typing import Optional
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    role: Optional[str] = "user"
    preferred_language: Optional[str] = "zh_CN"
    preferred_theme: Optional[str] = "light"

class UserCreate(UserBase):
    password: str
    invite_code: Optional[str] = None

class UserUpdate(UserBase):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
    preferred_language: Optional[str] = None
    preferred_theme: Optional[str] = None

class UserInDBBase(UserBase):
    id: int
    is_active: bool
    balance: float
    total_spent: float
    last_opened_semester_id: Optional[int] = None
    created_at: str # Will be datetime, but Pydantic handles str conversion
    updated_at: str # Will be datetime, but Pydantic handles str conversion

    class Config:
        from_attributes = True # For Pydantic v2, use from_attributes=True instead of orm_mode=True

class User(UserInDBBase):
    pass

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None

class UserPublic(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    balance: float
    preferred_language: str
    preferred_theme: str
    last_opened_semester_id: Optional[int] = None
    created_at: str

    class Config:
        from_attributes = True
