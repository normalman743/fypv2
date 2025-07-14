from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Text, JSON, CheckConstraint
from sqlalchemy.orm import relationship
from app.models.database import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    
    # 新的统一文件关联 (优先使用)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=True, index=True)
    
    # 兼容性字段 (迁移期间保留)
    physical_file_id = Column(Integer, ForeignKey("physical_files.id"), nullable=True, index=True)
    global_file_id = Column(Integer, nullable=True)  # 移除外键约束，因为表可能被删除
    
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)
    chroma_id = Column(String(36), unique=True, nullable=False, index=True)
    chunk_metadata = Column(JSON, nullable=True)  # 重命名以避免与SQLAlchemy保留字冲突
    created_at = Column(DateTime, server_default=func.now())

    # 更新约束：优先使用 file_id
    __table_args__ = (
        CheckConstraint(
            "file_id IS NOT NULL OR physical_file_id IS NOT NULL OR global_file_id IS NOT NULL",
            name="chk_file_reference"
        ),
    )

    # 关系
    file = relationship("File")  # 新的统一关系
    physical_file = relationship("PhysicalFile")  # 兼容性关系
    
    @property
    def source_file_name(self):
        """获取源文件名"""
        if self.file:
            return self.file.original_name
        elif self.physical_file:
            # 通过 physical_file 找到对应的 file
            from sqlalchemy.orm import object_session
            session = object_session(self)
            if session:
                from app.models.file import File
                file_record = session.query(File).filter(
                    File.physical_file_id == self.physical_file_id
                ).first()
                if file_record:
                    return file_record.original_name
        return "Unknown"
