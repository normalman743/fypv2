# -*- coding: utf-8 -*-
"""
Models package initialization.
This file imports all model classes to ensure they are registered with SQLAlchemy.
"""

# Import database configuration and Base
from .database import Base

# Import all model classes
from .user import User
from .invite_code import InviteCode
from .email_verification import EmailVerification
from .semester import Semester
from .course import Course
from .folder import Folder
from .file import File
from .physical_file import PhysicalFile
from .document_chunk import DocumentChunk
from .file_share import FileShare, FileAccessLog, FileGroup, FileGroupMember  # 新增文件共享模型
from .chat import Chat
from .message import Message
from .permission import Permission, Role, SubjectRole  # 权限系统模型
from .message_reference import MessageFileReference, MessageRAGSource  # 消息关联模型
from .audit_log import AuditLog  # 审计日志模型
from .system_config import SystemConfig  # 系统配置模型
from .temporary_file import TemporaryFile  # 临时文件模型

# Export all models
__all__ = [
    # Database
    'Base',
    
    # User management
    'User',
    'InviteCode',
    'EmailVerification',
    
    # Course management
    'Semester', 
    'Course',
    
    # File system
    'Folder',
    'File',
    'PhysicalFile',
    'DocumentChunk',
    'FileShare',
    'FileAccessLog', 
    'FileGroup',
    'FileGroupMember',
    
    # Chat system
    'Chat',
    'Message',
    'MessageFileReference',
    'MessageRAGSource',
    
    # Permission system
    'Permission',
    'Role', 
    'SubjectRole',
    
    # System management
    'AuditLog',
    'SystemConfig',
    'TemporaryFile',
]
