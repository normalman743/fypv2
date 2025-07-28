from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.database import Base

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    
    # 外键关系
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    semester = relationship("Semester", back_populates="courses")
    user = relationship("User", back_populates="courses")
    folders = relationship("Folder", back_populates="course")
    files = relationship("File", back_populates="course")
    chats = relationship("Chat", back_populates="course")
