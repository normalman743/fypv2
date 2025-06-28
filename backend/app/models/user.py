from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(128))
    role = Column(String(20), default="user", comment="user, admin", index=True)
    balance = Column(DECIMAL(10, 2), default=1.00)
    total_spent = Column(DECIMAL(10, 2), default=0.00)
    preferred_language = Column(String(20), default="zh_CN", comment="zh_CN, en")
    preferred_theme = Column(String(20), default="light", comment="light, dark, system")
    last_opened_semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    semesters = relationship("Semester", back_populates="last_opened_by_users")
    courses = relationship("Course", back_populates="owner")
    chats = relationship("Chat", back_populates="owner")
    files = relationship("File", back_populates="uploader")
    invite_codes_created = relationship("InviteCode", back_populates="creator", foreign_keys="[InviteCode.created_by]")
    invite_codes_used = relationship("InviteCode", back_populates="user_used", foreign_keys="[InviteCode.used_by]")