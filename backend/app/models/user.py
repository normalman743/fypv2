from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")  # user, admin
    
    # 用户余额和消费
    balance = Column(Float, default=1.00)
    total_spent = Column(Float, default=0.00)
    
    # 用户偏好设置
    preferred_language = Column(String(20), default="zh_CN")
    preferred_theme = Column(String(20), default="light")
    last_opened_semester_id = Column(Integer, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 软删除
    is_active = Column(Boolean, default=True)
    
    # 关系
    courses = relationship("Course", back_populates="user")
    files = relationship("File", back_populates="user")
    chats = relationship("Chat", back_populates="user")
