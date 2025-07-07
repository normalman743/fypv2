from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.models.database import Base

class MessageFileAttachment(Base):
    __tablename__ = "message_file_attachments"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False, index=True)
    filename = Column(String(256), nullable=False)  # Generated filename for storage
    created_at = Column(DateTime, server_default=func.now())

    message = relationship("Message", back_populates="file_attachments")
    file = relationship("File")

class MessageRAGSource(Base):
    __tablename__ = "message_rag_sources"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    source_file = Column(String(256), nullable=False)
    chunk_id = Column(Integer, nullable=False)
    relevance_score = Column(String(32), nullable=True)  # For future use
    created_at = Column(DateTime, server_default=func.now())

    message = relationship("Message", back_populates="rag_sources_rel")