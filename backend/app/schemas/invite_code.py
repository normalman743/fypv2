from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class InviteCodeResponse(BaseModel):
    id: int
    code: str
    description: str
    is_used: bool
    expires_at: datetime
    created_at: datetime

class InviteCodeListResponse(BaseModel):
    invite_codes: List[InviteCodeResponse]

class CreateInviteCodeRequest(BaseModel):
    description: str
    expires_at: datetime

class CreateInviteCodeResponse(BaseModel):
    invite_code: dict  # 包含id, code, created_at

class UpdateInviteCodeRequest(BaseModel):
    description: Optional[str] = None
    expires_at: Optional[datetime] = None

class UpdateInviteCodeResponse(BaseModel):
    invite_code: dict  # 包含id, updated_at 