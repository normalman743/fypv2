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
from .chat import Chat
from .message import Message
from .message_reference import MessageFileReference, MessageRAGSource
from .temporary_file import TemporaryFile

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
    
    # Chat system
    'Chat',
    'Message',
    'MessageFileReference',
    'MessageRAGSource',
    
    # Temporary files
    'TemporaryFile',
]
