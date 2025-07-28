"""Admin模块 - 系统管理功能"""

from .models import AuditLog
from .schemas import (
    # 请求模型
    CreateInviteCodeRequest, UpdateInviteCodeRequest, AuditLogQuery,
    # 响应数据模型
    InviteCodeData, CreateInviteCodeData, InviteCodeListData, UpdateInviteCodeData,
    SystemConfigData, AuditLogData, AuditLogsData, MessageData, PaginationInfo,
    # 响应模型
    CreateInviteCodeResponse, InviteCodeListResponse, UpdateInviteCodeResponse,
    SystemConfigResponse, AuditLogsResponse, MessageResponse
)
from .service import AdminService
from .router import router
from .dependencies import AdminDep, get_admin_user

__all__ = [
    # Models
    "AuditLog",
    # 请求模型
    "CreateInviteCodeRequest", "UpdateInviteCodeRequest", "AuditLogQuery",
    # 响应数据模型
    "InviteCodeData", "CreateInviteCodeData", "InviteCodeListData", "UpdateInviteCodeData",
    "SystemConfigData", "AuditLogData", "AuditLogsData", "MessageData", "PaginationInfo",
    # 响应模型
    "CreateInviteCodeResponse", "InviteCodeListResponse", "UpdateInviteCodeResponse",
    "SystemConfigResponse", "AuditLogsResponse", "MessageResponse",
    # Service
    "AdminService",
    # Router
    "router",
    # Dependencies
    "AdminDep", "get_admin_user"
]