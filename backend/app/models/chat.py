from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, func
from sqlalchemy.orm import relationship
from app.models.database import Base

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
    
    # RAG配置
    rag_enabled = Column(Boolean, default=True)
    max_context_length = Column(Integer, default=4000)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), index=True)

    course = relationship("Course", back_populates="chats")
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan") 