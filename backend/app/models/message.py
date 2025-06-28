from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Text, DECIMAL
from sqlalchemy.orm import relationship
from app.models.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    
    # AI相关字段
    model_name = Column(String(50), nullable=True, index=True)
    tokens_used = Column(Integer, nullable=True)
    cost = Column(DECIMAL(10, 4), nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)

    chat = relationship("Chat", back_populates="messages")
    file_attachments = relationship("MessageFileAttachment", back_populates="message", cascade="all, delete-orphan")
    rag_sources = relationship("MessageRAGSource", back_populates="message", cascade="all, delete-orphan") 