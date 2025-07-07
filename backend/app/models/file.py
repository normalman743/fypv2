from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func, Text
from sqlalchemy.orm import relationship
from app.models.database import Base

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    physical_file_id = Column(Integer, ForeignKey("physical_files.id"), nullable=False, index=True)
    
    # 用户层面的文件信息
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    
    # 关联字段
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # RAG处理相关
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(20), default="pending")
    processing_error = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    chunk_count = Column(Integer, default=0)
    content_preview = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    physical_file = relationship("PhysicalFile", back_populates="files")
    folder = relationship("Folder", back_populates="files")
    course = relationship("Course", back_populates="files")
    user = relationship("User", back_populates="files") 