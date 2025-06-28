from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
import hashlib
import os
from fastapi import UploadFile
from pathlib import Path
import tempfile

from app.models.file import File
from app.models.folder import Folder
from app.models.course import Course
from app.core.exceptions import NotFoundError, ForbiddenError, BadRequestError
from app.services.local_file_storage import local_file_storage

# Import RAG service
try:
    from app.services.rag_service import get_rag_service
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


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

        # 上传到本地存储
        try:
            file_path, local_path = local_file_storage.upload_file(file, course_id, folder_id)
        except Exception as e:
            raise BadRequestError(f"Failed to upload file to local storage: {e}", "LOCAL_UPLOAD_FAILED")

        # Read file content for processing (reset file pointer)
        file.file.seek(0)
        file_content = file.file.read()
        file_size = len(file_content)
        
        # Reset file pointer for potential future reads
        file.file.seek(0)

        # Determine file type based on content and extension
        file_type = self._determine_file_type(file.filename, file.content_type)

        try:
            # Create file record with local file path
            file_record = File(
                original_name=file.filename,
                file_type=file_type,
                file_size=file_size,
                mime_type=file.content_type or "application/octet-stream",
                course_id=course_id,
                folder_id=folder_id,
                user_id=user_id,
                is_processed=False,
                processing_status="pending",
                file_path=file_path  # 文件本地存储路径
            )
            
            self.db.add(file_record)
            self.db.commit()
            self.db.refresh(file_record)
            
            # 启动异步RAG处理任务
            task_id = self._start_async_rag_processing(file_record, file_content)
            
            return file_record
        except IntegrityError:
            self.db.rollback()
            # 如果数据库操作失败，删除已上传的本地文件
            local_file_storage.delete_file(file_path)
            raise BadRequestError("Failed to upload file", "FILE_UPLOAD_FAILED")

    def _start_async_rag_processing(self, file_record: File, file_content: bytes) -> str:
        """启动异步RAG处理任务"""
        try:
            # 尝试导入Celery任务
            from app.tasks.file_processing import process_file_rag_task
            
            # 启动异步任务
            task = process_file_rag_task.delay(file_record.id, file_content)
            
            print(f"🚀 Started async RAG processing for file {file_record.id}, task ID: {task.id}")
            return str(task.id)
            
        except ImportError:
            print("⚠️ Celery not available, falling back to synchronous processing")
            # 降级到同步处理
            self._process_file_with_rag_sync(file_record, file_content)
            return "sync_processing"
        except Exception as e:
            print(f"❌ Failed to start async task: {e}")
            # 降级到同步处理
            self._process_file_with_rag_sync(file_record, file_content)
            return "sync_fallback"
    
    def _process_file_with_rag_sync(self, file_record: File, file_content: bytes):
        """同步RAG处理（备用方案）"""
        try:
            # Update status to processing
            file_record.processing_status = "processing"
            self.db.commit()
            
            if not RAG_AVAILABLE:
                print("⚠️ RAG service not available, marking as completed without processing")
                file_record.is_processed = True
                file_record.processing_status = "completed"
                self.db.commit()
                return
            
            # Create temporary file for RAG processing
            with tempfile.NamedTemporaryFile(
                suffix=f"_{file_record.original_name}", 
                delete=False
            ) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Process with RAG service
                rag_service = get_rag_service()
                result = rag_service.process_file(file_record, temp_file_path)
                
                print(f"✅ RAG processing completed: {result}")
                
                # Update status to completed
                file_record.is_processed = True
                file_record.processing_status = "completed"
                self.db.commit()
                
            except Exception as e:
                print(f"❌ RAG processing failed: {e}")
                file_record.processing_status = "failed"
                self.db.commit()
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            print(f"❌ File processing error: {e}")
            file_record.processing_status = "failed"
            self.db.commit()

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

    def download_file(self, file_id: int, user_id: int) -> Tuple[File, bytes]:
        """Get file for download (check access via course ownership)"""
        file_record = self.get_file_preview(file_id, user_id)  # Same access logic
        
        # 从本地存储读取文件内容
        if not file_record.file_path:
            raise BadRequestError("File path not found", "FILE_PATH_NOT_FOUND")
        
        file_content = local_file_storage.download_file(file_record.file_path)
        if file_content is None:
            raise BadRequestError("Failed to read file from local storage", "LOCAL_READ_FAILED")
        
        return file_record, file_content

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

        # 删除本地存储中的文件
        if file_record.file_path:
            try:
                local_file_storage.delete_file(file_record.file_path)
            except Exception as e:
                print(f"⚠️ Failed to delete file from local storage: {e}")
                # 继续删除数据库记录，即使本地文件删除失败
        
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