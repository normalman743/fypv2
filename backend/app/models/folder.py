from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.models.database import Base

class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    folder_type = Column(String(20), nullable=False)  # outline, tutorial, lecture, exam, assignment, others
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    course = relationship("Course", back_populates="folders")
    files = relationship("File", back_populates="folder") 