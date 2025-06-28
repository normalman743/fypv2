from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.models.database import Base

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(20), default="pending")
    file_path = Column(String(500), nullable=True)  # 文件存储路径
    created_at = Column(DateTime, server_default=func.now())

    folder = relationship("Folder", back_populates="files")
    course = relationship("Course", back_populates="files")
    user = relationship("User", back_populates="files") 