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
from .semester import Semester
from .course import Course
from .folder import Folder
from .file import File
from .physical_file import PhysicalFile
from .document_chunk import DocumentChunk
from .file_share import FileShare, FileAccessLog, FileGroup, FileGroupMember  # 新增文件共享模型
from .chat import Chat
from .message import Message

# Export all models
__all__ = [
    # Database
    'Base',
    
    # User management
    'User',
    'InviteCode',
    
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
]
