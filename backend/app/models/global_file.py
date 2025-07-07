from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func, Text, JSON
from sqlalchemy.orm import relationship
from app.models.database import Base

class GlobalFile(Base):
    __tablename__ = "global_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    upload_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=True, index=True)
    
    # 分类管理
    category = Column(String(50), default="general", index=True)
    tags = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    
    # 权限控制
    is_active = Column(Boolean, default=True, index=True)
    is_public = Column(Boolean, default=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # RAG处理相关
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(20), default="pending", index=True)
    processing_error = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    chunk_count = Column(Integer, default=0)
    content_preview = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    creator = relationship("User", back_populates="created_global_files")
