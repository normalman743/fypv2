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
from .global_file import GlobalFile
from .document_chunk import DocumentChunk
from .chat import Chat
from .message import Message
from .message_file import MessageFile
from .message_attachment import MessageFileAttachment, MessageRAGSource

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
    'GlobalFile',
    'DocumentChunk',
    
    # Chat system
    'Chat',
    'Message',
    'MessageFile',
    'MessageFileAttachment',
    'MessageRAGSource',
]
