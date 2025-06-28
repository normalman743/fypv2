from sqlalchemy import Column, Integer, String, Text, DateTime, DECIMAL, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False, comment="user, assistant, system", index=True)
    model_name = Column(String(50), nullable=True, comment="使用的模型名称", index=True)
    tokens_used = Column(Integer)
    cost = Column(DECIMAL(10, 4))
    response_time_ms = Column(Integer, nullable=True, comment="响应时间（毫秒）")
    rag_sources = Column(JSON, nullable=True, comment="RAG检索的来源文档")
    created_at = Column(DateTime, default=func.now(), index=True)

    # Relationships
    chat = relationship("Chat", back_populates="messages")
    file_attachments = relationship("MessageFile", back_populates="message")

class MessageFile(Base):
    __tablename__ = "message_files"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False, index=True)

    # Relationships
    message = relationship("Message", back_populates="file_attachments")
    file = relationship("File", back_populates="message_attachments")