from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.models.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False, index=True)
    content = Column(String(4096), nullable=False)
    role = Column(String(32), nullable=False)  # user或assistant
    tokens_used = Column(Integer, nullable=True)
    cost = Column(Integer, nullable=True)  # 以分为单位
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    chat = relationship("Chat", back_populates="messages") 