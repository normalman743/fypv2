"""Admin模块业务逻辑服务"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, func
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import secrets
import string

# 导入日志
from src.shared.logging import get_logger

# 导入模型
from .models import AuditLog
from src.auth.models import InviteCode, User

# 导入请求/响应模型
from .schemas import (
    CreateInviteCodeRequest, UpdateInviteCodeRequest, AuditLogQuery
)

# 导入异常
from src.shared.exceptions import (
    BadRequestError, NotFoundError, ConflictError, ForbiddenError
)

# 导入配置
from src.shared.config import settings


class AdminService:
    """管理员服务类 - 基于Auth模块模式实现"""
    
    # 声明每个方法可能抛出的异常
    METHOD_EXCEPTIONS = {
        # 邀请码管理
        'create_invite_code': {BadRequestError, ConflictError},
        'get_invite_codes': set(),  # 无特定异常
        'get_invite_code': {NotFoundError},
        'update_invite_code': {NotFoundError, BadRequestError},
        'delete_invite_code': {NotFoundError, ConflictError},  # 已使用的不能删除
        
        # 系统配置
        'get_system_config': set(),  # 只读，无异常
        
        # 审计日志
        'get_audit_logs': {BadRequestError},  # 日期格式错误等
        'create_audit_log': set(),  # 内部使用，无异常
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger(__name__)

    # ===== 邀请码管理 =====
    
    def create_invite_code(self, request: CreateInviteCodeRequest, created_by: int) -> Dict[str, Any]:
        """创建邀请码"""
        # 1. 验证过期时间
        if request.expires_at and request.expires_at <= datetime.utcnow():
            raise BadRequestError("过期时间不能早于当前时间", error_code="INVALID_EXPIRE_TIME")
        
        # 2. 生成唯一邀请码
        code = self._generate_unique_invite_code()
        
        try:
            # 3. 创建邀请码
            invite_code = InviteCode(
                code=code,
                description=request.description,
                expires_at=request.expires_at,
                created_by=created_by
            )
            
            self.db.add(invite_code)
            self.db.commit()
            self.db.refresh(invite_code)
            
            # 4. 记录审计日志
            self.create_audit_log(
                user_id=created_by,
                action="CREATE_INVITE_CODE",
                entity_type="invite_code",
                entity_id=invite_code.id,
                details={
                    "code": code,
                    "description": request.description,
                    "expires_at": request.expires_at.isoformat() if request.expires_at else None
                }
            )
            
            # 5. 重新查询获取关联信息
            created_invite_code = self._get_invite_code_with_user_info(invite_code.id)
            
            return {
                "invite_code": created_invite_code,
                "message": "邀请码创建成功"
            }
            
        except IntegrityError:
            self.db.rollback()
            # 理论上不会发生，因为我们生成唯一码
            raise ConflictError("邀请码生成冲突，请重试", error_code="INVITE_CODE_CONFLICT")

    def get_invite_codes(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """获取邀请码列表"""
        # 查询总数
        total = self.db.query(InviteCode).count()
        
        # 分页查询，关联用户信息
        invite_codes = (
            self.db.query(InviteCode)
            .options(
                joinedload(InviteCode.creator),
                joinedload(InviteCode.user)
            )
            .order_by(InviteCode.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        # 直接返回ORM对象，让Pydantic处理序列化
        return {
            "invite_codes": invite_codes,
            "total": total,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total,
                "has_more": skip + limit < total
            }
        }

    def get_invite_code(self, invite_code_id: int) -> Dict[str, Any]:
        """获取单个邀请码详情"""
        invite_code = self._get_invite_code_with_user_info(invite_code_id)
        if not invite_code:
            raise NotFoundError(f"邀请码 {invite_code_id} 不存在", error_code="INVITE_CODE_NOT_FOUND")
        
        return {
            "invite_code": invite_code,
            "message": None
        }

    def update_invite_code(self, invite_code_id: int, request: UpdateInviteCodeRequest, updated_by: int) -> Dict[str, Any]:
        """更新邀请码"""        
        # 1. 查找邀请码
        invite_code = self.db.query(InviteCode).filter(InviteCode.id == invite_code_id).first()
        if not invite_code:
            raise NotFoundError(f"邀请码 {invite_code_id} 不存在", error_code="INVITE_CODE_NOT_FOUND")
        
        # 2. 验证更新权限（已使用的邀请码某些字段不能修改）
        if invite_code.is_used and request.expires_at is not None:
            raise BadRequestError("已使用的邀请码不能修改过期时间", error_code="USED_INVITE_CODE_READONLY")
        
        # 3. 验证过期时间
        if request.expires_at and request.expires_at <= datetime.utcnow():
            raise BadRequestError("过期时间不能早于当前时间", error_code="INVALID_EXPIRE_TIME")
        
        # 4. 记录更新前的状态用于审计
        old_data = {
            "description": invite_code.description,
            "expires_at": invite_code.expires_at.isoformat() if invite_code.expires_at else None,
            "is_active": invite_code.is_active
        }
        
        # 5. 更新字段
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(invite_code, field, value)
        
        self.db.commit()
        self.db.refresh(invite_code)
        
        # 6. 记录审计日志
        try:
            # 为审计日志准备JSON兼容的数据
            json_safe_update_data = {}
            for field, value in update_data.items():
                if isinstance(value, datetime):
                    json_safe_update_data[field] = value.isoformat()
                else:
                    json_safe_update_data[field] = value
            
            self.create_audit_log(
                user_id=updated_by,
                action="UPDATE_INVITE_CODE",
                entity_type="invite_code",
                entity_id=invite_code.id,
                details={
                    "old_data": old_data,
                    "new_data": json_safe_update_data
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to create audit log: {e}")
            # 审计日志失败不应该影响业务操作
        
        # 7. 重新查询获取关联信息
        updated_invite_code = self._get_invite_code_with_user_info(invite_code.id)
        
        return {
            "invite_code": updated_invite_code,
            "message": "邀请码更新成功"
        }

    def delete_invite_code(self, invite_code_id: int, deleted_by: int) -> Dict[str, Any]:
        """删除邀请码"""
        # 1. 查找邀请码
        invite_code = self.db.query(InviteCode).filter(InviteCode.id == invite_code_id).first()
        if not invite_code:
            raise NotFoundError(f"邀请码 {invite_code_id} 不存在", error_code="INVITE_CODE_NOT_FOUND")
        
        # 2. 检查是否已使用（已使用的不能删除）
        if invite_code.is_used:
            raise ConflictError(
                f"邀请码 {invite_code.code} 已被使用，无法删除",
                error_code="INVITE_CODE_ALREADY_USED"
            )
        
        # 3. 记录删除前的信息用于审计
        delete_data = {
            "code": invite_code.code,
            "description": invite_code.description,
            "expires_at": invite_code.expires_at.isoformat() if invite_code.expires_at else None,
            "created_at": invite_code.created_at.isoformat()
        }
        
        # 4. 删除邀请码
        self.db.delete(invite_code)
        self.db.commit()
        
        # 5. 记录审计日志
        self.create_audit_log(
            user_id=deleted_by,
            action="DELETE_INVITE_CODE",
            entity_type="invite_code",
            entity_id=invite_code_id,
            details=delete_data
        )
        
        return {
            "message": f"邀请码 {invite_code.code} 删除成功"
        }

    # ===== 系统配置 =====
    
    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置 - 过滤敏感信息"""
        # 获取系统统计
        total_users = self.db.query(User).count()
        # TODO: 等Storage模块实现后添加文件统计
        # total_files = self.db.query(File).count()
        total_files = 0
        storage_used_mb = 0.0
        
        config_data = {
            # 应用信息
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "environment": settings.environment,
            
            # 功能开关
            "registration_enabled": settings.enable_registration,
            "email_verification_enabled": settings.enable_email_verification,
            
            # 系统统计
            "total_users": total_users,
            "total_files": total_files,
            "storage_used_mb": storage_used_mb,
            
            # 限制配置（从配置中获取，如果没有则使用默认值）
            "max_file_size_mb": 100,  # TODO: 从设置中获取
            "max_upload_files_per_user": 1000,  # TODO: 从设置中获取
        }
        
        return {
            "data": config_data,
            "message": None
        }

    # ===== 审计日志 =====
    
    def get_audit_logs(
        self, 
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """获取审计日志"""
        # 1. 验证日期范围
        if start_date and end_date and start_date > end_date:
            raise BadRequestError("开始时间不能晚于结束时间", error_code="INVALID_DATE_RANGE")
        
        # 2. 验证时间范围不能过大（防止查询超时）
        if start_date and end_date:
            date_diff = end_date - start_date
            if date_diff.days > 365:  # 限制一年内
                raise BadRequestError("查询时间范围不能超过365天", error_code="DATE_RANGE_TOO_LARGE")
        
        # 3. 构建查询（优化：使用joinedload避免N+1查询）
        query = (
            self.db.query(AuditLog)
            .options(joinedload(AuditLog.user))
        )
        
        # 应用过滤条件
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if action:
            query = query.filter(AuditLog.action == action)
            
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        
        # 4. 获取总数和分页数据
        total = query.count()
        logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
        
        # 直接返回ORM对象，让Pydantic处理序列化
        return {
            "logs": logs,
            "total": total,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total,
                "has_more": skip + limit < total
            }
        }

    def create_audit_log(
        self,
        user_id: Optional[int],
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """创建审计日志 - 内部使用"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        return audit_log

    # ===== 私有辅助方法 =====
    
    def _generate_unique_invite_code(self) -> str:
        """生成唯一的邀请码"""
        max_attempts = 10
        
        for _ in range(max_attempts):
            # 生成8位随机邀请码：2位字母 + 6位数字
            letters = ''.join(secrets.choice(string.ascii_uppercase) for _ in range(2))
            numbers = ''.join(secrets.choice(string.digits) for _ in range(6))
            code = letters + numbers
            
            # 检查是否已存在
            existing = self.db.query(InviteCode).filter(InviteCode.code == code).first()
            if not existing:
                return code
        
        # 如果多次尝试都失败，使用UUID确保唯一性
        import uuid
        return f"INV{uuid.uuid4().hex[:8].upper()}"
    
    def _get_invite_code_with_user_info(self, invite_code_id: int) -> Optional[InviteCode]:
        """获取包含用户信息的邀请码"""
        invite_code = (
            self.db.query(InviteCode)
            .options(
                joinedload(InviteCode.creator),
                joinedload(InviteCode.user)
            )
            .filter(InviteCode.id == invite_code_id)
            .first()
        )
        
        return invite_code