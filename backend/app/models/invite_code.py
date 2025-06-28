from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.models.database import Base

class InviteCode(Base):
    __tablename__ = "invite_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), nullable=False, unique=True, index=True)
    description = Column(String(256), nullable=False)
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now()) 