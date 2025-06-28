from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    invite_code: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    email: str
    role: str
    balance: float
    total_spent: float
    preferred_language: str
    preferred_theme: str
    last_opened_semester_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    is_active: bool

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    preferred_language: Optional[str] = None
    preferred_theme: Optional[str] = None
