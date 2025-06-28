from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    chat_type = Column(String(20), nullable=False, comment="general, course", index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    custom_prompt = Column(Text)
    rag_enabled = Column(Boolean, default=True, comment="是否启用RAG检索")
    max_context_length = Column(Integer, default=4000, comment="最大上下文长度")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    course = relationship("Course", back_populates="chats")
    owner = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat")