from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.database import Base


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    
    # 资源标识
    resource_type = Column(String(50), nullable=False, index=True)  # 'file', 'course', 'folder', 'chat'
    resource_id = Column(String(100), nullable=False, index=True)
    
    # 主体标识  
    subject_type = Column(String(50), nullable=False, index=True)  # 'user', 'role', 'group', 'course_member'
    subject_id = Column(String(100), nullable=False, index=True)
    
    # 权限定义
    action = Column(String(50), nullable=False, index=True)  # 'read', 'write', 'delete', 'share'
    effect = Column(Enum('allow', 'deny', name='permission_effect'), default='allow')
    
    # 条件和元数据
    conditions = Column(JSON, nullable=True)  # 复杂条件: 时间、IP、设备等
    extra_data = Column(JSON, nullable=True)  # 扩展字段
    
    # 管理字段
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    granted_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)  # 过期时间
    is_active = Column(Boolean, default=True, index=True)
    
    # 关系
    granted_by_user = relationship("User", foreign_keys=[granted_by])


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    scope_type = Column(String(50), default='global')  # 'global', 'course', 'organization'
    scope_id = Column(String(100), nullable=True)  # 作用域ID
    is_system = Column(Boolean, default=False)  # 系统内置角色
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    subject_roles = relationship("SubjectRole", back_populates="role")


class SubjectRole(Base):
    __tablename__ = "subject_roles"

    id = Column(Integer, primary_key=True, index=True)
    subject_type = Column(String(50), nullable=False, index=True)
    subject_id = Column(String(100), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    scope_type = Column(String(50), nullable=True)  # 角色生效范围
    scope_id = Column(String(100), nullable=True)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # 关系
    role = relationship("Role", back_populates="subject_roles")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])