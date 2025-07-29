"""Storage模块数据模型"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func, Text, JSON, Index, BigInteger
from sqlalchemy.orm import relationship
from src.shared.database import Base


class PhysicalFile(Base):
    __tablename__ = "physical_files"

    id = Column(Integer, primary_key=True, index=True)
    file_hash = Column(String(64), unique=True, nullable=False, index=True)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    storage_path = Column(String(500), nullable=False)
    first_uploaded_at = Column(DateTime, server_default=func.now())
    reference_count = Column(Integer, default=0)

    # 关系
    files = relationship("File", back_populates="physical_file")
    temporary_files = relationship("TemporaryFile", back_populates="physical_file")


class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    folder_type = Column(String(20), nullable=False)  # outline, tutorial, lecture, exam, assignment, others
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="folders")
    files = relationship("File", back_populates="folder")


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    physical_file_id = Column(Integer, ForeignKey("physical_files.id"), nullable=False, index=True)
    
    # 基本文件信息
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    
    # 作用域和归属
    scope = Column(String(20), nullable=False, default='course', index=True)
    visibility = Column(String(20), default='private', index=True)
    
    # 关联字段
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 文件元数据
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_hash = Column(String(64), nullable=True, index=True)
    
    # 共享和权限
    is_shareable = Column(Boolean, default=True)
    share_settings = Column(JSON, nullable=True)
    
    # RAG处理相关
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(20), default="pending")
    processing_error = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    chunk_count = Column(Integer, default=0)
    content_preview = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 复合索引优化
    __table_args__ = (
        Index('idx_scope_visibility', scope, visibility),
        Index('idx_owner_course', user_id, course_id),
        Index('idx_file_hash', file_hash),
    )

    # 关系
    physical_file = relationship("PhysicalFile", back_populates="files")
    folder = relationship("Folder", back_populates="files")
    course = relationship("Course", back_populates="files")
    user = relationship("User", back_populates="files")
    
    # 新增关系
    shares = relationship("FileShare", back_populates="file", cascade="all, delete-orphan")
    access_logs = relationship("FileAccessLog", back_populates="file", cascade="all, delete-orphan")
    document_chunks = relationship("DocumentChunk", back_populates="file", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    chunk_metadata = Column(JSON, nullable=True) # 不能使用保留字 metadata
    vector_id = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    file = relationship("File", back_populates="document_chunks")
    message_rag_sources = relationship("MessageRAGSource", back_populates="document_chunk")


class FileShare(Base):
    __tablename__ = "file_shares"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    share_token = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    file = relationship("File", back_populates="shares")
    user = relationship("User")
    access_logs = relationship("FileAccessLog", back_populates="file_share", cascade="all, delete-orphan")


class FileAccessLog(Base):
    __tablename__ = "file_access_logs"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    file_share_id = Column(Integer, ForeignKey("file_shares.id"), nullable=True, index=True)
    access_type = Column(String(20), nullable=False, index=True)  # 'view', 'download'
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    accessed_at = Column(DateTime, server_default=func.now(), index=True)

    # 关系
    file = relationship("File", back_populates="access_logs")
    user = relationship("User")
    file_share = relationship("FileShare", back_populates="access_logs")


class FileGroup(Base):
    __tablename__ = "file_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    creator = relationship("User")
    members = relationship("FileGroupMember", back_populates="file_group", cascade="all, delete-orphan")


class FileGroupMember(Base):
    __tablename__ = "file_group_members"

    id = Column(Integer, primary_key=True, index=True)
    file_group_id = Column(Integer, ForeignKey("file_groups.id"), nullable=False, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False, index=True)
    added_at = Column(DateTime, server_default=func.now())

    # 关系
    file_group = relationship("FileGroup", back_populates="members")
    file = relationship("File")


class TemporaryFile(Base):
    __tablename__ = "temporary_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=True)
    physical_file_id = Column(Integer, ForeignKey("physical_files.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    physical_file = relationship("PhysicalFile", back_populates="temporary_files")
    user = relationship("User")