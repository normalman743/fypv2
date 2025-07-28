"""Chat模块数据模型"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, func, DECIMAL, JSON
from sqlalchemy.orm import relationship
from src.shared.database import Base


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    chat_type = Column(String(20), nullable=False, index=True)  # 'general', 'course'
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    custom_prompt = Column(Text, nullable=True)
    
    # AI模型配置
    ai_model = Column(String(20), nullable=False, default='Star', index=True)  # 'Star', 'StarPlus', 'StarCode'
    search_enabled = Column(Boolean, nullable=False, default=False)
    
    # 对话配置
    context_mode = Column(String(20), nullable=False, default='Standard', index=True)  # Economy/Standard/Premium/Max
    
    # RAG配置
    rag_enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), index=True)

    course = relationship("Course", back_populates="chats")
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")


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


class MessageFileReference(Base):
    __tablename__ = "message_file_references"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    message = relationship("Message", back_populates="file_references")
    file = relationship("File")


class MessageRAGSource(Base):
    __tablename__ = "message_rag_sources"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    document_chunk_id = Column(Integer, ForeignKey("document_chunks.id"), nullable=False, index=True)
    relevance_score = Column(DECIMAL(5, 4), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    message = relationship("Message", back_populates="rag_sources_tracked")
    document_chunk = relationship("DocumentChunk", back_populates="message_rag_sources")