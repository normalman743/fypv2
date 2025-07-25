from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Text
from sqlalchemy.orm import relationship
from app.models.database import Base
from datetime import datetime, timedelta

class TemporaryFile(Base):
    __tablename__ = "temporary_files"

    id = Column(Integer, primary_key=True, index=True)
    physical_file_id = Column(Integer, ForeignKey("physical_files.id"), nullable=False, index=True)
    
    # 基本文件信息
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    
    # 上传者信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 临时文件特有字段
    token = Column(String(64), unique=True, index=True, nullable=False)  # 用于访问文件的唯一token
    expires_at = Column(DateTime, nullable=False, index=True)  # 过期时间
    purpose = Column(String(50), nullable=True)  # 用途说明，如 'chat_upload', 'preview' 等
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    physical_file = relationship("PhysicalFile", back_populates="temporary_files")
    user = relationship("User", back_populates="temporary_files")
    
    @property
    def is_expired(self) -> bool:
        """检查文件是否已过期"""
        return datetime.utcnow() > self.expires_at
    
    @classmethod
    def default_expiry_time(cls):
        """默认过期时间：从配置中读取"""
        from app.core.config import settings
        return datetime.utcnow() + timedelta(hours=settings.temporary_file_expiry_hours)