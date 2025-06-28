from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False)
    description = Column(Text)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    semester = relationship("Semester", back_populates="courses")
    owner = relationship("User", back_populates="courses")
    folders = relationship("Folder", back_populates="course")
    files = relationship("File", back_populates="course")
    chats = relationship("Chat", back_populates="course")