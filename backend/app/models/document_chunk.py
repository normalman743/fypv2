from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Text, JSON
from sqlalchemy.orm import relationship
from app.models.database import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    
    # 统一文件关联
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True)
    
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)
    chroma_id = Column(String(36), unique=True, nullable=False, index=True)
    chunk_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    file = relationship("File", back_populates="document_chunks")
    
    @property
    def source_file_name(self):
        """获取源文件名"""
        if self.file:
            return self.file.original_name
        return "Unknown"
