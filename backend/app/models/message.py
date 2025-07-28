from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Text, DECIMAL, JSON
from sqlalchemy.orm import relationship
from app.models.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False, index=True)  # 'user', 'assistant', 'system'
    
    # AI相关字段
    model_name = Column(String(50), nullable=True, index=True)
    tokens_used = Column(Integer, nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    cost = Column(DECIMAL(20, 8), nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # RAG相关
    rag_sources = Column(JSON, nullable=True)
    
    # 上下文统计字段
    context_size = Column(Integer, nullable=True)
    direct_file_count = Column(Integer, default=0)
    rag_source_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)

    # 关系
    chat = relationship("Chat", back_populates="messages")
    file_references = relationship("MessageFileReference", back_populates="message", cascade="all, delete-orphan")
    rag_sources_tracked = relationship("MessageRAGSource", back_populates="message", cascade="all, delete-orphan") 