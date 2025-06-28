from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
import hashlib
import os
from fastapi import UploadFile

from app.models.file import File
from app.models.folder import Folder
from app.models.course import Course
from app.core.exceptions import NotFoundError, ForbiddenError, BadRequestError


class FileService:
    def __init__(self, db: Session):
        self.db = db

    def get_folder_files(self, folder_id: int, user_id: int) -> List[File]:
        """Get all files in a folder (check access via course ownership)"""
        # Check if folder exists and user has access via course
        folder = self.db.query(Folder).options(joinedload(Folder.course)).filter(Folder.id == folder_id).first()
        if not folder:
            raise NotFoundError("Folder not found", "FOLDER_NOT_FOUND")
        
        if folder.course.user_id != user_id:
            raise ForbiddenError("You don't have permission to access this folder")

        return self.db.query(File).options(
            joinedload(File.folder)
        ).filter(File.folder_id == folder_id).all()

    def upload_file(self, file: UploadFile, course_id: int, folder_id: int, user_id: int) -> File:
        """Upload file to folder (check course ownership)"""
        # Check if course exists and user has access
        course = self.db.query(Course).filter(
            Course.id == course_id,
            Course.user_id == user_id
        ).first()
        if not course:
            raise NotFoundError("Course not found or access denied", "COURSE_NOT_FOUND")

        # Check if folder exists and belongs to the course
        folder = self.db.query(Folder).filter(
            Folder.id == folder_id,
            Folder.course_id == course_id
        ).first()
        if not folder:
            raise NotFoundError("Folder not found or does not belong to course", "FOLDER_NOT_FOUND")

        # Read file content for processing
        file_content = file.file.read()
        file_size = len(file_content)
        
        # Reset file pointer for potential future reads
        file.file.seek(0)

        # Determine file type based on content and extension
        file_type = self._determine_file_type(file.filename, file.content_type)

        try:
            # Create file record
            file_record = File(
                original_name=file.filename,
                file_type=file_type,
                file_size=file_size,
                mime_type=file.content_type or "application/octet-stream",
                course_id=course_id,
                folder_id=folder_id,
                user_id=user_id,
                is_processed=False,
                processing_status="pending"
            )
            
            self.db.add(file_record)
            self.db.commit()
            self.db.refresh(file_record)
            
            # TODO: Implement actual file storage logic here
            # For now, just mark as completed
            file_record.is_processed = True
            file_record.processing_status = "completed"
            self.db.commit()
            
            return file_record
        except IntegrityError:
            self.db.rollback()
            raise BadRequestError("Failed to upload file", "FILE_UPLOAD_FAILED")

    def get_file_preview(self, file_id: int, user_id: int) -> File:
        """Get file preview info (check access via course ownership)"""
        # Get file with course info
        file_record = self.db.query(File).options(
            joinedload(File.course)
        ).filter(File.id == file_id).first()
        
        if not file_record:
            raise NotFoundError("File not found", "FILE_NOT_FOUND")
        
        # Check if user has access via course ownership
        if file_record.course.user_id != user_id:
            raise ForbiddenError("You don't have permission to access this file")

        return file_record

    def download_file(self, file_id: int, user_id: int) -> File:
        """Get file for download (check access via course ownership)"""
        return self.get_file_preview(file_id, user_id)  # Same access logic

    def delete_file(self, file_id: int, user_id: int) -> bool:
        """Delete file (check access via course ownership)"""
        # Get file with course info
        file_record = self.db.query(File).options(
            joinedload(File.course)
        ).filter(File.id == file_id).first()
        
        if not file_record:
            raise NotFoundError("File not found", "FILE_NOT_FOUND")
        
        # Check if user has access via course ownership
        if file_record.course.user_id != user_id:
            raise ForbiddenError("You don't have permission to delete this file")

        # TODO: Implement actual file deletion from storage here
        
        self.db.delete(file_record)
        self.db.commit()
        return True

    def _determine_file_type(self, filename: str, content_type: str) -> str:
        """Determine file type based on filename and content type"""
        if not filename:
            return "unknown"
        
        filename_lower = filename.lower()
        
        # PDF documents
        if filename_lower.endswith('.pdf') or content_type == 'application/pdf':
            return "course_material"
        
        # Images
        if (filename_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')) or 
            content_type and content_type.startswith('image/')):
            return "image"
        
        # Documents
        if (filename_lower.endswith(('.doc', '.docx', '.txt', '.rtf')) or
            content_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']):
            return "document"
        
        # Presentations
        if (filename_lower.endswith(('.ppt', '.pptx')) or
            content_type in ['application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation']):
            return "presentation"
        
        # Spreadsheets
        if (filename_lower.endswith(('.xls', '.xlsx', '.csv')) or
            content_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']):
            return "spreadsheet"
        
        # Default to course material for unknown types
        return "course_material"