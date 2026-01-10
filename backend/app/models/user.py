from sqlalchemy import Column, Integer, String, DateTime, Boolean, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), default="user", index=True)  # user, admin
    
    # 用户余额和消费
    balance = Column(DECIMAL(10, 2), default=0.10)
    total_spent = Column(DECIMAL(10, 2), default=0.00)
    
    # 用户偏好设置
    preferred_language = Column(String(20), default="zh_CN")
    preferred_theme = Column(String(20), default="light")
    last_opened_semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=True)
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    courses = relationship("Course", back_populates="user")
    files = relationship("File", back_populates="user")
    chats = relationship("Chat", back_populates="user")
    created_invite_codes = relationship("InviteCode", foreign_keys="InviteCode.created_by", back_populates="creator")
    used_invite_codes = relationship("InviteCode", foreign_keys="InviteCode.used_by", back_populates="user")
    email_verifications = relationship("EmailVerification", back_populates="user")
    temporary_files = relationship("TemporaryFile", back_populates="user")
