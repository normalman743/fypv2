"""Admin模块路由定义"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime

from .service import AdminService
from .schemas import (
    # 请求模型
    CreateInviteCodeRequest, UpdateInviteCodeRequest,
    # 响应模型
    CreateInviteCodeResponse, GetInviteCodeResponse, InviteCodeListResponse, UpdateInviteCodeResponse,
    SystemConfigResponse, AuditLogsResponse, MessageResponse,
    # 数据模型
    InviteCodeData, AuditLogData
)

# 导入依赖
from src.shared.dependencies import DbDep
from .dependencies import AdminDep

# 导入装饰器
from src.shared.api_decorator import create_service_route_config, service_api_handler

# 创建路由器
router = APIRouter(prefix="/admin")


# ===== 邀请码管理 =====

@router.post("/invite-codes", **create_service_route_config(
    AdminService, 'create_invite_code', CreateInviteCodeResponse,
    success_status=201,
    summary="创建邀请码",
    description="管理员创建新的邀请码，可设置描述和过期时间",
    operation_id="create_invite_code"
))
@service_api_handler(AdminService, 'create_invite_code')
async def create_invite_code(
    request: CreateInviteCodeRequest,
    admin_user: AdminDep,
    db: DbDep
):
    """创建邀请码 (管理员专用)"""
    service = AdminService(db)
    result = service.create_invite_code(request, admin_user.id)
    
    return CreateInviteCodeResponse(
        success=True,
        data={"invite_code": InviteCodeData.from_orm_with_relations(result["invite_code"])},
        message=result["message"]
    )


@router.get("/invite-codes", **create_service_route_config(
    AdminService, 'get_invite_codes', InviteCodeListResponse,
    summary="获取邀请码列表",
    description="分页获取邀请码列表，包含使用状态和用户信息",
    operation_id="get_invite_codes"
))
@service_api_handler(AdminService, 'get_invite_codes')
async def get_invite_codes(
    admin_user: AdminDep,
    db: DbDep,
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="每页记录数")
):
    """获取邀请码列表 (管理员专用)"""
    service = AdminService(db)
    result = service.get_invite_codes(skip=skip, limit=limit)
    
    return InviteCodeListResponse(
        success=True,
        data={
            "invite_codes": [InviteCodeData.from_orm_with_relations(code) for code in result["invite_codes"]],
            "total": result["total"],
            "pagination": result["pagination"]
        }
    )


@router.get("/invite-codes/{invite_code_id}", **create_service_route_config(
    AdminService, 'get_invite_code', GetInviteCodeResponse,
    summary="获取邀请码详情",
    description="获取指定邀请码的详细信息",
    operation_id="get_invite_code",
    include_in_schema=False  # 如果不希望在API文档中显示，可以设置为False
))
@service_api_handler(AdminService, 'get_invite_code')
async def get_invite_code(
    invite_code_id: int,
    admin_user: AdminDep,
    db: DbDep
):
    """获取邀请码详情 (管理员专用)"""
    service = AdminService(db)
    result = service.get_invite_code(invite_code_id)
    
    return GetInviteCodeResponse(
        success=True,
        data={"invite_code": InviteCodeData.from_orm_with_relations(result["invite_code"])},
        message=result["message"]
    )


@router.put("/invite-codes/{invite_code_id}", **create_service_route_config(
    AdminService, 'update_invite_code', UpdateInviteCodeResponse,
    summary="更新邀请码",
    description="更新邀请码的描述、过期时间或启用状态",
    operation_id="update_invite_code",
    include_in_schema=False  # 如果不希望在API文档中显示，可以设置为False
))
@service_api_handler(AdminService, 'update_invite_code')
async def update_invite_code(
    invite_code_id: int,
    request: UpdateInviteCodeRequest,
    admin_user: AdminDep,
    db: DbDep
):
    """更新邀请码 (管理员专用)"""
    service = AdminService(db)
    result = service.update_invite_code(invite_code_id, request, admin_user.id)
    
    return UpdateInviteCodeResponse(
        success=True,
        data={"invite_code": InviteCodeData.from_orm_with_relations(result["invite_code"])},
        message=result["message"]
    )


@router.delete("/invite-codes/{invite_code_id}", **create_service_route_config(
    AdminService, 'delete_invite_code', MessageResponse,
    summary="删除邀请码",
    description="删除未使用的邀请码（已使用的邀请码无法删除）",
    operation_id="delete_invite_code"
))
@service_api_handler(AdminService, 'delete_invite_code')
async def delete_invite_code(
    invite_code_id: int,
    admin_user: AdminDep,
    db: DbDep
):
    """删除邀请码 (管理员专用)"""
    service = AdminService(db)
    result = service.delete_invite_code(invite_code_id, admin_user.id)
    
    return MessageResponse(
        success=True,
        data={"message": result["message"]},
        message=result["message"]
    )


# ===== 系统配置 =====

@router.get("/system/config", **create_service_route_config(
    AdminService, 'get_system_config', SystemConfigResponse,
    summary="获取系统配置",
    description="获取系统配置信息，包含应用信息、功能开关和系统统计",
    operation_id="get_system_config",
    include_in_schema=False  # 如果不希望在API文档中显示，可以设置为False
))
@service_api_handler(AdminService, 'get_system_config')
async def get_system_config(
    admin_user: AdminDep,
    db: DbDep
):
    """获取系统配置 (管理员专用)"""
    service = AdminService(db)
    result = service.get_system_config()
    
    return SystemConfigResponse(
        success=True,
        data=result["data"],
        message=result["message"]
    )


# ===== 审计日志 =====

@router.get("/audit-logs", **create_service_route_config(
    AdminService, 'get_audit_logs', AuditLogsResponse,
    summary="获取审计日志",
    description="分页查询审计日志，支持按用户、操作类型、实体类型和时间范围过滤",
    operation_id="get_audit_logs",
    include_in_schema=False  # 如果不希望在API文档中显示，可以设置为False
))
@service_api_handler(AdminService, 'get_audit_logs')
async def get_audit_logs(
    admin_user: AdminDep,
    db: DbDep,
    user_id: Optional[int] = Query(None, ge=1, description="用户ID过滤"),
    action: Optional[str] = Query(None, description="操作类型过滤"),
    entity_type: Optional[str] = Query(None, description="实体类型过滤"),
    start_date: Optional[datetime] = Query(None, description="开始时间过滤"),
    end_date: Optional[datetime] = Query(None, description="结束时间过滤"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="每页记录数")
):
    """获取审计日志 (管理员专用)"""
    service = AdminService(db)
    result = service.get_audit_logs(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    
    return AuditLogsResponse(
        success=True,
        data={
            "logs": [AuditLogData.from_orm_with_relations(log) for log in result["logs"]],
            "total": result["total"],
            "pagination": result["pagination"]
        },
        message=result.get("message")
    )