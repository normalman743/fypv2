from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func, Text, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.database import Base


class FileShare(Base):
    """文件共享记录表"""
    __tablename__ = "file_shares"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False, index=True)
    
    # 共享对象 (灵活设计)
    shared_with_type = Column(String(20), nullable=False)  
    # 取值: 'user', 'course', 'group', 'role', 'public'
    shared_with_id = Column(Integer, nullable=True)  # 根据type决定是否需要
    
    # 权限级别
    permission_level = Column(String(20), default='read')
    # 取值: 'read', 'comment', 'edit', 'manage'
    
    # 共享配置
    can_reshare = Column(Boolean, default=False)
    download_allowed = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    
    # 追踪信息
    shared_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    last_accessed = Column(DateTime, nullable=True)
    access_count = Column(Integer, default=0)
    
    # 复合索引优化
    __table_args__ = (
        Index('idx_share_target', shared_with_type, shared_with_id),
        Index('idx_file_permissions', file_id, permission_level),
        Index('idx_shared_by_date', shared_by, created_at),
    )
    
    # 关系
    file = relationship("File", back_populates="shares")
    sharer = relationship("User", foreign_keys=[shared_by])


class FileAccessLog(Base):
    """文件访问日志表"""
    __tablename__ = "file_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    action = Column(String(20), nullable=False)  # 'view', 'download', 'share', 'edit'
    access_via = Column(String(20), default='direct')  # 'direct', 'share', 'course'
    
    # 元数据
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    accessed_at = Column(DateTime, server_default=func.now())
    
    # 索引优化
    __table_args__ = (
        Index('idx_file_access', file_id, accessed_at),
        Index('idx_user_access', user_id, accessed_at),
        Index('idx_action_date', action, accessed_at),
    )
    
    # 关系
    file = relationship("File", back_populates="access_logs")
    user = relationship("User")


class FileGroup(Base):
    """文件组 - 用于批量共享和权限管理"""
    __tablename__ = "file_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    group_type = Column(String(20), default='custom')  # 'custom', 'course_based', 'role_based'
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)  # 课程级组
    
    is_active = Column(Boolean, default=True)
    auto_manage = Column(Boolean, default=False)  # 自动管理成员
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    course = relationship("Course", foreign_keys=[course_id])
    members = relationship("FileGroupMember", back_populates="group", cascade="all, delete-orphan")


class FileGroupMember(Base):
    """文件组成员表"""
    __tablename__ = "file_group_members"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("file_groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default='member')  # 'admin', 'member', 'viewer'
    
    added_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime, server_default=func.now())
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('group_id', 'user_id', name='uq_group_member'),
        Index('idx_group_member', group_id, user_id),
    )
    
    # 关系
    group = relationship("FileGroup", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    adder = relationship("User", foreign_keys=[added_by])