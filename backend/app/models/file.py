from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

class PhysicalFile(Base):
    __tablename__ = "physical_files"

    id = Column(Integer, primary_key=True, index=True)
    file_hash = Column(String(64), unique=True, nullable=False, index=True, comment="SHA256哈希")
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    storage_path = Column(String(500), nullable=False, comment="实际存储路径")
    first_uploaded_at = Column(DateTime, default=func.now())
    reference_count = Column(Integer, default=0, comment="引用计数")

    # Relationships
    files = relationship("File", back_populates="physical_file")
    document_chunks = relationship("DocumentChunk", back_populates="physical_file")

class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    folder_type = Column(String(20), nullable=False, comment="outline, tutorial, lecture, exam, assignment, others", index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    is_default = Column(Boolean, default=False, comment="是否为系统默认文件夹")
    created_at = Column(DateTime, default=func.now())

    # Relationships
    course = relationship("Course", back_populates="folders")
    files = relationship("File", back_populates="folder")

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    physical_file_id = Column(Integer, ForeignKey("physical_files.id"), nullable=False, index=True, comment="指向物理文件")
    original_name = Column(String(255), nullable=False, comment="用户上传时的文件名")
    file_type = Column(String(50), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(20), default="pending")
    processing_error = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    chunk_count = Column(Integer, default=0)
    content_preview = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    physical_file = relationship("PhysicalFile", back_populates="files")
    course = relationship("Course", back_populates="files")
    folder = relationship("Folder", back_populates="files")
    uploader = relationship("User", back_populates="files")
    message_attachments = relationship("MessageFile", back_populates="file")

class GlobalFile(Base):
    __tablename__ = "global_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    upload_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=True, index=True)
    category = Column(String(50), default="general", comment="分类: general, faq, policy, manual, template", index=True)
    tags = Column(Text, nullable=True) # Storing JSON as Text for now, will use JSON type if supported by DB driver
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_public = Column(Boolean, default=True, comment="是否对所有用户可见", index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(20), default="pending", index=True)
    processing_error = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    chunk_count = Column(Integer, default=0)
    content_preview = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("User") # No back_populates needed if not used from User side
    document_chunks = relationship("DocumentChunk", back_populates="global_file")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    physical_file_id = Column(Integer, ForeignKey("physical_files.id"), nullable=True, index=True, comment="指向普通物理文件")
    global_file_id = Column(Integer, ForeignKey("global_files.id"), nullable=True, index=True, comment="指向全局文件")
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer)
    token_count = Column(Integer)
    chroma_id = Column(String(36), unique=True, nullable=False, index=True)
    chunk_metadata = Column(Text, nullable=True) # Renamed from 'metadata'
    created_at = Column(DateTime, default=func.now())

    # Relationships
    physical_file = relationship("PhysicalFile", back_populates="document_chunks")
    global_file = relationship("GlobalFile", back_populates="document_chunks")

    # Constraint to ensure only one file source is linked
    # __table_args__ = (
    #     CheckConstraint(
    #         '(physical_file_id IS NOT NULL AND global_file_id IS NOT NULL) OR '
    #     ),
    # )
