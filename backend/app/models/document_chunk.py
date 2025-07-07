from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Text, JSON, CheckConstraint
from sqlalchemy.orm import relationship
from app.models.database import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    physical_file_id = Column(Integer, ForeignKey("physical_files.id"), nullable=True, index=True)
    global_file_id = Column(Integer, ForeignKey("global_files.id"), nullable=True)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)
    chroma_id = Column(String(36), unique=True, nullable=False, index=True)
    chunk_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # 确保只能关联一种文件的约束
    __table_args__ = (
        CheckConstraint(
            "(physical_file_id IS NOT NULL AND global_file_id IS NULL) OR "
            "(physical_file_id IS NULL AND global_file_id IS NOT NULL)",
            name="chk_file_source"
        ),
    )

    # 关系
    physical_file = relationship("PhysicalFile")
    global_file = relationship("GlobalFile")
