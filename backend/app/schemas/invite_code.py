from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.schemas.common import BaseResponse

class InviteCodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    code: str
    description: Optional[str] = None
    is_used: bool = False
    used_by: Optional[int] = None
    used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True
    created_by: int
    created_at: datetime

class CreateInviteCodeRequest(BaseModel):
    description: Optional[str] = None
    expires_at: Optional[datetime] = None

class UpdateInviteCodeRequest(BaseModel):
    description: Optional[str] = None
    expires_at: Optional[datetime] = None

# 具体的响应数据模型
class CreateInviteCodeData(BaseModel):
    invite_code: dict  # 包含id, code, created_at

class UpdateInviteCodeData(BaseModel):
    invite_code: dict  # 包含id, updated_at

class InviteCodeListData(BaseModel):
    invite_codes: List[InviteCodeResponse]

# 具体的API响应模型
class CreateInviteCodeResponse(BaseResponse):
    success: bool = True
    data: CreateInviteCodeData

class UpdateInviteCodeResponse(BaseResponse):
    success: bool = True
    data: UpdateInviteCodeData

class InviteCodeListResponse(BaseResponse):
    success: bool = True
    data: InviteCodeListData 