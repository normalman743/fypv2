from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

class InviteCode(Base):
    __tablename__ = "invite_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    description = Column(String(200), nullable=True, comment="邀请码用途描述")
    is_used = Column(Boolean, default=False, comment="是否已使用", index=True)
    used_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="使用者用户ID")
    used_at = Column(DateTime, nullable=True, comment="使用时间")
    expires_at = Column(DateTime, nullable=True, comment="过期时间", index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    creator = relationship("User", back_populates="invite_codes_created", foreign_keys="[InviteCode.created_by]")
    user_used = relationship("User", back_populates="invite_codes_used", foreign_keys="[InviteCode.used_by]")