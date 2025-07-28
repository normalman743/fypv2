from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.models.database import Base

class InviteCode(Base):
    __tablename__ = "invite_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), nullable=False, unique=True, index=True)
    description = Column(String(200), nullable=True)
    is_used = Column(Boolean, default=False, index=True)
    used_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_invite_codes")
    user = relationship("User", foreign_keys=[used_by], back_populates="used_invite_codes") 