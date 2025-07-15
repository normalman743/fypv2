from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.database import Base


class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(50), nullable=False, unique=True, index=True)
    config_value = Column(Text, nullable=True)
    description = Column(String(200), nullable=True)
    is_public = Column(Boolean, default=False)  # 是否对普通用户可见
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    updated_by_user = relationship("User")