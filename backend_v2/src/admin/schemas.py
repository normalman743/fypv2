"""Admin模块的Pydantic模式定义"""
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

# ===== 请求模式 =====

class CreateInviteCodeRequest(BaseModel):
    """创建邀请码请求模型"""
    description: Optional[str] = Field(
        None, 
        max_length=200, 
        description="邀请码描述（可选，最多200字符）"
    )
    expires_at: Optional[datetime] = Field(
        None, 
        description="过期时间（可选，不设置则永不过期）"
    )
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError('描述不能为空字符串')
        return v.strip() if v else None


class UpdateInviteCodeRequest(BaseModel):
    """更新邀请码请求模型"""
    description: Optional[str] = Field(
        None, 
        max_length=200, 
        description="邀请码描述（可选）"
    )
    expires_at: Optional[datetime] = Field(
        None, 
        description="过期时间（可选）"
    )
    is_active: Optional[bool] = Field(
        None,
        description="是否启用（可选）"
    )
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError('描述不能为空字符串')
        return v.strip() if v else None


class AuditLogQuery(BaseModel):
    """审计日志查询参数模型"""
    user_id: Optional[int] = Field(
        None, 
        ge=1, 
        description="用户ID过滤（可选）"
    )
    action: Optional[str] = Field(
        None, 
        max_length=100,
        description="操作类型过滤（可选）"
    )
    entity_type: Optional[str] = Field(
        None, 
        max_length=50,
        description="实体类型过滤（可选）"
    )
    start_date: Optional[datetime] = Field(
        None, 
        description="开始时间（可选）"
    )
    end_date: Optional[datetime] = Field(
        None, 
        description="结束时间（可选）"
    )
    skip: int = Field(
        default=0, 
        ge=0, 
        description="跳过记录数"
    )
    limit: int = Field(
        default=100, 
        ge=1, 
        le=1000, 
        description="每页记录数（1-1000）"
    )
    
    @field_validator('action', 'entity_type')
    @classmethod
    def validate_string_fields(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError('字段不能为空字符串')
        return v.strip() if v else None


# ===== 响应数据模式 =====

class InviteCodeData(BaseModel):
    """邀请码数据模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="邀请码ID")
    code: str = Field(..., description="邀请码")
    description: Optional[str] = Field(None, description="邀请码描述")
    is_used: bool = Field(..., description="是否已使用")
    used_by: Optional[int] = Field(None, description="使用者用户ID")
    used_by_username: Optional[str] = Field(None, description="使用者用户名")
    used_at: Optional[datetime] = Field(None, description="使用时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    is_active: bool = Field(..., description="是否启用")
    created_by: int = Field(..., description="创建者用户ID")
    created_by_username: Optional[str] = Field(None, description="创建者用户名")
    created_at: datetime = Field(..., description="创建时间")
    
    @classmethod
    def from_orm_with_relations(cls, invite_code):
        """从ORM对象创建，包含关联用户信息"""
        return cls(
            id=invite_code.id,
            code=invite_code.code,
            description=invite_code.description,
            is_used=invite_code.is_used,
            used_by=invite_code.used_by,
            used_by_username=invite_code.user.username if invite_code.user else None,
            used_at=invite_code.used_at,
            expires_at=invite_code.expires_at,
            is_active=invite_code.is_active,
            created_by=invite_code.created_by,
            created_by_username=invite_code.creator.username if invite_code.creator else None,
            created_at=invite_code.created_at
        )


class PaginationInfo(BaseModel):
    """分页信息模型"""
    skip: int = Field(..., description="跳过记录数")
    limit: int = Field(..., description="每页记录数")
    total: int = Field(..., description="总记录数")
    has_more: bool = Field(..., description="是否有更多记录")


class CreateInviteCodeData(BaseModel):
    """创建邀请码响应数据"""
    invite_code: InviteCodeData = Field(..., description="创建的邀请码信息")


class GetInviteCodeData(BaseModel):
    """获取邀请码详情响应数据"""
    invite_code: InviteCodeData = Field(..., description="邀请码详情信息")


class InviteCodeListData(BaseModel):
    """邀请码列表响应数据"""
    invite_codes: List[InviteCodeData] = Field(..., description="邀请码列表")
    total: int = Field(..., description="总记录数")
    pagination: PaginationInfo = Field(..., description="分页信息")


class UpdateInviteCodeData(BaseModel):
    """更新邀请码响应数据"""
    invite_code: InviteCodeData = Field(..., description="更新后的邀请码信息")


class SystemConfigData(BaseModel):
    """系统配置数据模型"""
    # 应用信息
    app_name: str = Field(..., description="应用名称")
    app_version: str = Field(..., description="应用版本")
    environment: str = Field(..., description="运行环境")
    
    # 功能开关
    registration_enabled: bool = Field(..., description="是否启用注册")
    email_verification_enabled: bool = Field(..., description="是否启用邮箱验证")
    
    # 系统统计
    total_users: int = Field(..., description="总用户数")
    total_files: int = Field(..., description="总文件数")
    storage_used_mb: float = Field(..., description="已使用存储空间(MB)")
    
    # 限制配置
    max_file_size_mb: int = Field(..., description="最大文件大小(MB)")
    max_upload_files_per_user: int = Field(..., description="每用户最大上传文件数")


class AuditLogData(BaseModel):
    """审计日志数据模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="日志ID")
    user_id: Optional[int] = Field(None, description="操作用户ID")
    username: Optional[str] = Field(None, description="操作用户名")
    action: str = Field(..., description="操作类型")
    entity_type: str = Field(..., description="实体类型")
    entity_id: Optional[int] = Field(None, description="实体ID")
    details: Optional[Dict[str, Any]] = Field(None, description="操作详情")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    created_at: datetime = Field(..., description="创建时间")
    
    @classmethod
    def from_orm_with_relations(cls, audit_log):
        """从ORM对象创建，包含关联用户信息"""
        return cls(
            id=audit_log.id,
            user_id=audit_log.user_id,
            username=audit_log.user.username if audit_log.user else None,
            action=audit_log.action,
            entity_type=audit_log.entity_type,
            entity_id=audit_log.entity_id,
            details=audit_log.details,
            ip_address=audit_log.ip_address,
            user_agent=audit_log.user_agent,
            created_at=audit_log.created_at
        )


class AuditLogsData(BaseModel):
    """审计日志列表响应数据"""
    logs: List[AuditLogData] = Field(..., description="审计日志列表")
    total: int = Field(..., description="总记录数")
    pagination: PaginationInfo = Field(..., description="分页信息")


class MessageData(BaseModel):
    """消息响应数据"""
    message: str = Field(..., description="操作消息")


# ===== 导入共享响应格式 =====
from src.shared.schemas import BaseResponse


# ===== 具体响应模型 =====

class CreateInviteCodeResponse(BaseResponse[CreateInviteCodeData]):
    """创建邀请码响应模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "success": True,
                "data": {
                    "invite_code": {
                        "id": 1,
                        "code": "ABC12345",
                        "description": "测试邀请码",
                        "is_used": False,
                        "used_by": None,
                        "used_by_username": None,
                        "used_at": None,
                        "expires_at": "2025-12-31T23:59:59Z",
                        "is_active": True,
                        "created_by": 1,
                        "created_by_username": "admin",
                        "created_at": "2025-01-27T10:00:00Z"
                    }
                },
                "message": "邀请码创建成功"
            }]
        }
    )


class InviteCodeListResponse(BaseResponse[InviteCodeListData]):
    """邀请码列表响应模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "success": True,
                "data": {
                    "invite_codes": [
                        {
                            "id": 1,
                            "code": "ABC12345",
                            "description": "测试邀请码",
                            "is_used": False,
                            "used_by": None,
                            "used_by_username": None,
                            "used_at": None,
                            "expires_at": "2025-12-31T23:59:59Z",
                            "is_active": True,
                            "created_by": 1,
                            "created_by_username": "admin",
                            "created_at": "2025-01-27T10:00:00Z"
                        }
                    ],
                    "total": 1,
                    "pagination": {
                        "skip": 0,
                        "limit": 100,
                        "total": 1,
                        "has_more": False
                    }
                },
                "message": None
            }]
        }
    )


class GetInviteCodeResponse(BaseResponse[GetInviteCodeData]):
    """获取邀请码详情响应模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "success": True,
                "data": {
                    "invite_code": {
                        "id": 1,
                        "code": "ABC12345",
                        "description": "测试邀请码",
                        "is_used": False,
                        "used_by": None,
                        "used_by_username": None,
                        "used_at": None,
                        "expires_at": "2025-12-31T23:59:59Z",
                        "is_active": True,
                        "created_by": 1,
                        "created_by_username": "admin",
                        "created_at": "2025-01-27T10:00:00Z"
                    }
                },
                "message": None
            }]
        }
    )


class UpdateInviteCodeResponse(BaseResponse[UpdateInviteCodeData]):
    """更新邀请码响应模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "success": True,
                "data": {
                    "invite_code": {
                        "id": 1,
                        "code": "ABC12345",
                        "description": "更新后的描述",
                        "is_used": False,
                        "used_by": None,
                        "used_by_username": None,
                        "used_at": None,
                        "expires_at": "2026-01-01T00:00:00Z",
                        "is_active": True,
                        "created_by": 1,
                        "created_by_username": "admin",
                        "created_at": "2025-01-27T10:00:00Z"
                    }
                },
                "message": "邀请码更新成功"
            }]
        }
    )


class SystemConfigResponse(BaseResponse[SystemConfigData]):
    """系统配置响应模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "success": True,
                "data": {
                    "app_name": "Campus LLM System",
                    "app_version": "2.0.0",
                    "environment": "development",
                    "registration_enabled": True,
                    "email_verification_enabled": True,
                    "total_users": 156,
                    "total_files": 2347,
                    "storage_used_mb": 1234.56,
                    "max_file_size_mb": 100,
                    "max_upload_files_per_user": 1000
                },
                "message": None
            }]
        }
    )


class AuditLogsResponse(BaseResponse[AuditLogsData]):
    """审计日志响应模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "success": True,
                "data": {
                    "logs": [
                        {
                            "id": 1,
                            "user_id": 1,
                            "username": "admin",
                            "action": "CREATE_INVITE_CODE",
                            "entity_type": "invite_code",
                            "entity_id": 1,
                            "details": {
                                "code": "ABC12345",
                                "description": "测试邀请码"
                            },
                            "ip_address": "192.168.1.1",
                            "user_agent": "Mozilla/5.0...",
                            "created_at": "2025-01-27T10:00:00Z"
                        }
                    ],
                    "total": 1,
                    "pagination": {
                        "skip": 0,
                        "limit": 100,
                        "total": 1,
                        "has_more": False
                    }
                },
                "message": None
            }]
        }
    )


class MessageResponse(BaseResponse[MessageData]):
    """通用消息响应模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "success": True,
                "data": {
                    "message": "操作成功"
                },
                "message": "操作成功"
            }]
        }
    )