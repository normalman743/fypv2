from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.invite_code import InviteCode
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.file import File
from app.models.chat import Chat
from app.schemas.invite_code import CreateInviteCodeRequest, UpdateInviteCodeRequest
from app.core.exceptions import NotFoundError, BadRequestError
import secrets
import string
from typing import List, Optional, Dict, Any


class AdminService:
    # 声明每个方法可能抛出的异常
    METHOD_EXCEPTIONS = {
        'create_invite_code': {BadRequestError},
        'get_invite_codes': set(),
        'update_invite_code': {NotFoundError, BadRequestError},
        'delete_invite_code': {NotFoundError},
        'get_system_config': set(),  # 只读，无异常
        'get_audit_logs': {BadRequestError}
    }
    
    def __init__(self, db: Session):
        self.db = db

    def generate_invite_code(self) -> str:
        """生成邀请码"""
        # 生成8位随机字符串，包含字母和数字
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(secrets.choice(alphabet) for _ in range(8))
            # 检查是否已存在
            if not self.db.query(InviteCode).filter(InviteCode.code == code).first():
                return code

    def create_invite_code(self, request: CreateInviteCodeRequest, created_by: int) -> InviteCode:
        """创建邀请码"""
        code = self.generate_invite_code()
        
        invite_code = InviteCode(
            code=code,
            description=request.description,
            expires_at=request.expires_at,
            is_used=False,
            created_by=created_by
        )
        
        self.db.add(invite_code)
        self.db.commit()
        self.db.refresh(invite_code)
        return invite_code

    def get_invite_codes(self, skip: int = 0, limit: int = 100) -> List[InviteCode]:
        """获取邀请码列表"""
        return self.db.query(InviteCode).offset(skip).limit(limit).all()

    def get_invite_code_by_id(self, invite_code_id: int) -> InviteCode:
        """根据ID获取邀请码"""
        invite_code = self.db.query(InviteCode).filter(InviteCode.id == invite_code_id).first()
        if not invite_code:
            raise NotFoundError("邀请码不存在", "INVITE_CODE_NOT_FOUND")
        return invite_code

    def update_invite_code(self, invite_code_id: int, request: UpdateInviteCodeRequest) -> InviteCode:
        """更新邀请码"""
        invite_code = self.get_invite_code_by_id(invite_code_id)
        
        if request.description is not None:
            invite_code.description = request.description
        if request.expires_at is not None:
            invite_code.expires_at = request.expires_at
        
        self.db.commit()
        self.db.refresh(invite_code)
        return invite_code

    def delete_invite_code(self, invite_code_id: int) -> bool:
        """删除邀请码"""
        invite_code = self.get_invite_code_by_id(invite_code_id)
        self.db.delete(invite_code)
        self.db.commit()
        return True

    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置 - 只读，过滤敏感信息"""
        from app.core.config import settings
        
        # 只返回对管理员有用且安全的配置
        safe_config = {
            # 应用信息
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "environment": settings.environment,
            
            # 功能开关（只读显示）
            "registration_enabled": settings.registration_enabled,
            "email_verification_enabled": settings.email_verification_enabled,
            "registration_invite_code_verification": settings.registration_invite_code_verification,
            
            # 文件配置
            "max_file_size": settings.max_file_size,
            "max_file_size_mb": settings.max_file_size // (1024 * 1024),  # 方便显示
            "temporary_file_expiry_hours": settings.temporary_file_expiry_hours,
            
            # RAG 配置
            "rag_chunk_size": settings.rag_chunk_size,
            "rag_chunk_overlap": settings.rag_chunk_overlap,
            
            # 其他业务配置
            "access_token_expire_minutes": settings.access_token_expire_minutes,
            "allowed_email_domains": settings.allowed_email_domains_list,
            
            # 统计信息（只读）
            "total_users": self.db.query(User).count(),
        }
        
        # 安全地添加统计信息（避免导入问题）
        try:
            safe_config["total_files"] = self.db.query(File).count()
        except Exception:
            safe_config["total_files"] = 0
            
        try:
            safe_config["total_chats"] = self.db.query(Chat).count()
        except Exception:
            safe_config["total_chats"] = 0
        
        return safe_config


    def get_audit_logs(self, 
                      user_id: Optional[int] = None,
                      action: Optional[str] = None,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      skip: int = 0,
                      limit: int = 100) -> Dict[str, Any]:
        """获取审计日志"""
        from datetime import datetime
        
        query = self.db.query(AuditLog)
        
        # 应用过滤器
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if start_date:
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(AuditLog.created_at >= start)
            except ValueError:
                raise BadRequestError("开始日期格式错误", "INVALID_START_DATE")
        
        if end_date:
            try:
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(AuditLog.created_at <= end)
            except ValueError:
                raise BadRequestError("结束日期格式错误", "INVALID_END_DATE")
        
        # 分页和排序
        total = query.count()
        logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "logs": [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "username": log.user.username if log.user else "已删除用户",
                    "action": log.action,
                    "entity_type": log.entity_type,
                    "entity_id": log.entity_id,
                    "details": log.details,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat() + "Z"
                } for log in logs
            ],
            "total": total,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "has_more": skip + limit < total
            }
        } 