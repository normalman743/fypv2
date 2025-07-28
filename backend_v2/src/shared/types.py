"""
共享类型定义 - 避免循环导入

使用 Protocol 定义接口，避免在 shared 模块中直接导入业务模块的具体类
"""
from typing import Protocol, runtime_checkable, Optional
from datetime import datetime


@runtime_checkable
class UserProtocol(Protocol):
    """用户对象协议 - 定义用户对象的基本接口"""
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    email_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    failed_login_attempts: int
    locked_until: Optional[datetime]


@runtime_checkable
class InviteCodeProtocol(Protocol):
    """邀请码对象协议"""
    id: int
    code: str
    description: Optional[str]
    is_used: bool
    used_by: Optional[int]
    used_at: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool
    created_by: int
    created_at: datetime


@runtime_checkable
class AuditLogProtocol(Protocol):
    """审计日志对象协议"""
    id: int
    user_id: Optional[int]
    action: str
    entity_type: str
    entity_id: Optional[int]
    details: Optional[dict]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime