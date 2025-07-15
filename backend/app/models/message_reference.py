from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, DECIMAL
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.database import Base


class MessageFileReference(Base):
    __tablename__ = "message_file_references"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    reference_type = Column(Enum('file', 'folder', name='reference_type'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    message = relationship("Message", back_populates="file_references")
    file = relationship("File")


class MessageRAGSource(Base):
    __tablename__ = "message_rag_sources"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    source_file = Column(String(256), nullable=False)
    chunk_id = Column(Integer, ForeignKey("document_chunks.id"), nullable=True)
    relevance_score = Column(DECIMAL(5, 4), nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    message = relationship("Message", back_populates="rag_sources_tracked")
    chunk = relationship("DocumentChunk")