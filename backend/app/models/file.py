from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func, Text, JSON, Index
from sqlalchemy.orm import relationship
from app.models.database import Base

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    physical_file_id = Column(Integer, ForeignKey("physical_files.id"), nullable=False, index=True)
    
    # 基本文件信息
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    
    # 作用域和归属 (统一管理核心)
    scope = Column(String(20), nullable=False, default='course', index=True)
    # scope 取值: 'course', 'global', 'personal', 'shared'
    
    visibility = Column(String(20), default='private', index=True)
    # visibility 取值: 'private', 'course', 'public', 'shared'
    
    # 关联字段
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # 改名为owner_id更清晰
    
    # 文件元数据 (从 global_files 迁移)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_hash = Column(String(64), nullable=True, index=True)
    
    # 共享和权限
    is_shareable = Column(Boolean, default=True)
    share_settings = Column(JSON, nullable=True)  # 存储复杂共享配置
    
    # RAG处理相关
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(20), default="pending")
    processing_error = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    chunk_count = Column(Integer, default=0)
    content_preview = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 复合索引优化
    __table_args__ = (
        Index('idx_scope_visibility', scope, visibility),
        Index('idx_owner_course', user_id, course_id),
        Index('idx_file_hash', file_hash),
    )

    # 关系
    physical_file = relationship("PhysicalFile", back_populates="files")
    folder = relationship("Folder", back_populates="files")
    course = relationship("Course", back_populates="files")
    user = relationship("User", back_populates="files")
    
    # 新增关系
    shares = relationship("FileShare", back_populates="file", cascade="all, delete-orphan")
    access_logs = relationship("FileAccessLog", back_populates="file", cascade="all, delete-orphan")
    document_chunks = relationship("DocumentChunk", back_populates="file", cascade="all, delete-orphan")
    
    @property
    def owner_id(self):
        """为了向后兼容，提供 owner_id 属性"""
        return self.user_id
    
    @property
    def is_global(self) -> bool:
        """检查是否为全局文件"""
        return self.scope == 'global'
    
    @property
    def is_public(self) -> bool:
        """检查是否为公开文件"""
        return self.visibility == 'public'
    
    def can_access(self, user_id: int) -> bool:
        """基础权限检查"""
        # 文件所有者
        if self.user_id == user_id:
            return True
        
        # 公开文件
        if self.visibility == 'public':
            return True
            
        # 其他权限检查需要在 service 层实现
        return False 