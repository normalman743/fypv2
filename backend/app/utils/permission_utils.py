"""
Centralized permission checking utilities for consistent authorization across the application.

This module provides standardized permission checking functions that should be used
by all services to ensure consistent security policies.
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.course import Course
from app.models.file import File
from app.models.file_share import FileShare
from app.core.exceptions import ForbiddenError, NotFoundError


class PermissionChecker:
    """Centralized permission checking utility"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_course_access(self, course_id: int, user_id: int, action: str = 'read') -> bool:
        """
        Check if user has access to a course
        
        Args:
            course_id: Course ID to check
            user_id: User ID requesting access
            action: Type of access ('read', 'write', 'delete', 'manage')
            
        Returns:
            bool: True if access is allowed
        """
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            return False
        
        # Course owner has all permissions
        if course.user_id == user_id:
            return True
        
        # Check admin permissions
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.role == 'admin':
            return True
        
        # For non-owners, only read access might be granted through sharing
        if action == 'read':
            return self._check_course_sharing_access(course_id, user_id)
        
        return False
    
    def check_file_access(self, file_id: int, user_id: int, action: str = 'read') -> bool:
        """
        Check if user has access to a file
        
        Args:
            file_id: File ID to check
            user_id: User ID requesting access
            action: Type of access ('read', 'write', 'delete', 'share')
            
        Returns:
            bool: True if access is allowed
        """
        file_record = self.db.query(File).filter(File.id == file_id).first()
        if not file_record:
            return False
        
        # File owner has all permissions
        if file_record.user_id == user_id:
            return True
            
        # Check admin permissions (limited for personal files)
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.role == 'admin':
            # Admins can't access personal files of other users
            if file_record.scope == 'personal':
                return False
            return True
        
        # Public files allow read access
        if action == 'read' and file_record.visibility == 'public':
            return True
        
        # Course files: check course access
        if file_record.scope == 'course' and file_record.course_id:
            if action == 'read' and file_record.visibility == 'course':
                return self.check_course_access(file_record.course_id, user_id, 'read')
        
        # Check direct file sharing
        return self._check_file_sharing_access(file_id, user_id, action)
    
    def require_course_access(self, course_id: int, user_id: int, action: str = 'read') -> Course:
        """
        Require course access or raise exception
        
        Returns:
            Course: The course object if access is allowed
            
        Raises:
            NotFoundError: If course doesn't exist
            ForbiddenError: If access is denied
        """
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise NotFoundError("Course not found", "COURSE_NOT_FOUND")
        
        if not self.check_course_access(course_id, user_id, action):
            raise ForbiddenError(f"No {action} access to this course")
        
        return course
    
    def require_file_access(self, file_id: int, user_id: int, action: str = 'read') -> File:
        """
        Require file access or raise exception
        
        Returns:
            File: The file object if access is allowed
            
        Raises:
            NotFoundError: If file doesn't exist
            ForbiddenError: If access is denied
        """
        file_record = self.db.query(File).filter(File.id == file_id).first()
        if not file_record:
            raise NotFoundError("File not found", "FILE_NOT_FOUND")
        
        if not self.check_file_access(file_id, user_id, action):
            raise ForbiddenError(f"No {action} access to this file")
        
        return file_record
    
    def _check_course_sharing_access(self, course_id: int, user_id: int) -> bool:
        """Check if user has course access through sharing"""
        
        # Method 1: Direct course sharing
        course_share = self.db.query(FileShare).filter(
            FileShare.shared_with_type == 'course',
            FileShare.shared_with_id == course_id
        ).first()
        if course_share:
            return True
        
        # Method 2: Check permission table for course access
        from app.models.permission import Permission
        from sqlalchemy import func
        
        course_permission = self.db.query(Permission).filter(
            Permission.resource_type == 'course',
            Permission.resource_id == str(course_id),
            Permission.subject_type == 'user',
            Permission.subject_id == str(user_id),
            Permission.action.in_(['read', 'access']),
            Permission.effect == 'allow',
            Permission.is_active == True
        ).first()
        
        if course_permission:
            # Check if not expired
            if course_permission.expires_at is None or course_permission.expires_at > func.now():
                return True
        
        return False
    
    def _check_file_sharing_access(self, file_id: int, user_id: int, action: str) -> bool:
        """Check if user has file access through sharing"""
        
        # Map actions to permission levels
        action_mapping = {
            'read': ['read', 'comment', 'edit', 'manage'],
            'write': ['edit', 'manage'],
            'delete': ['manage'],
            'share': ['manage']
        }
        
        allowed_levels = action_mapping.get(action, ['manage'])
        
        # Check direct file sharing
        share = self.db.query(FileShare).filter(
            FileShare.file_id == file_id,
            FileShare.shared_with_type == 'user',
            FileShare.shared_with_id == user_id,
            FileShare.permission_level.in_(allowed_levels)
        ).first()
        
        return share is not None


def get_permission_checker(db: Session) -> PermissionChecker:
    """Get a permission checker instance"""
    return PermissionChecker(db)


# Convenience functions for common permission checks
def check_course_ownership(db: Session, course_id: int, user_id: int) -> bool:
    """Check if user owns the course"""
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == user_id
    ).first()
    return course is not None


def check_file_ownership(db: Session, file_id: int, user_id: int) -> bool:
    """Check if user owns the file"""
    file_record = db.query(File).filter(
        File.id == file_id,
        File.user_id == user_id
    ).first()
    return file_record is not None


def require_course_ownership(db: Session, course_id: int, user_id: int) -> Course:
    """Require course ownership or raise exception"""
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == user_id
    ).first()
    
    if not course:
        raise NotFoundError("Course not found or access denied", "COURSE_NOT_FOUND")
    
    return course


def require_file_ownership(db: Session, file_id: int, user_id: int) -> File:
    """Require file ownership or raise exception"""
    file_record = db.query(File).filter(
        File.id == file_id,
        File.user_id == user_id
    ).first()
    
    if not file_record:
        raise NotFoundError("File not found or access denied", "FILE_NOT_FOUND")
    
    return file_record