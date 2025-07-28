"""Admin模块数据模型"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, JSON, Text, Boolean
from sqlalchemy.orm import relationship
from src.shared.database import Base


class Permission(Base):
    """权限模型 - RBAC系统的权限定义"""
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}')>"


class Role(Base):
    """角色模型 - RBAC系统的角色定义"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"


class RolePermission(Base):
    """角色权限关联模型 - RBAC系统的角色权限映射"""
    __tablename__ = "role_permissions"
    
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), primary_key=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    role = relationship("Role")
    permission = relationship("Permission")
    
    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"


class SubjectRole(Base):
    """主题角色模型 - 为用户在特定课程/主题中分配角色"""
    __tablename__ = "subject_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True, index=True)  # 可空，支持全局角色
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    granted_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    role = relationship("Role")
    course = relationship("Course")  # 这个关系在Course模块中定义
    grantor = relationship("User", foreign_keys=[granted_by])
    
    def __repr__(self):
        return f"<SubjectRole(id={self.id}, user_id={self.user_id}, role_id={self.role_id}, course_id={self.course_id})>"


class AuditLog(Base):
    """审计日志模型 - 记录所有重要操作"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    # 兼容v1版本：使用entity_type而不是resource_type
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(Integer, nullable=True, index=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    # 兼容v1版本：使用created_at而不是timestamp
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    # 关系
    user = relationship("User")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action='{self.action}', entity_type='{self.entity_type}')>"


# 索引优化建议（在Alembic迁移中实现）
# CREATE INDEX idx_audit_logs_user_time ON audit_logs(user_id, created_at);
# CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
# CREATE INDEX idx_audit_logs_action_time ON audit_logs(action, created_at);