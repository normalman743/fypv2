from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
import hashlib
import os
from fastapi import UploadFile
from pathlib import Path
import tempfile

from app.models.file import File
from app.models.physical_file import PhysicalFile
from app.models.folder import Folder
from app.models.course import Course
from app.core.exceptions import NotFoundError, ForbiddenError, BadRequestError
from app.services.local_file_storage import local_file_storage

# Import RAG service
try:
    from app.services.rag_service import get_rag_service, ProductionRAGService
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
            joinedload(File.folder),
            joinedload(File.physical_file)
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
        
        # Calculate file hash for deduplication
        file_hash = hashlib.sha256(file_content).hexdigest()

        try:
            # Use database-level row locking to prevent race conditions
            # Check if physical file already exists with FOR UPDATE lock
            physical_file = self.db.query(PhysicalFile).filter(
                PhysicalFile.file_hash == file_hash
            ).with_for_update().first()
            
            if not physical_file:
                # Double-check after acquiring lock - another process might have created it
                physical_file = self.db.query(PhysicalFile).filter(
                    PhysicalFile.file_hash == file_hash
                ).first()
                
                if not physical_file:
                    # Create new physical file record
                    physical_file = PhysicalFile(
                        file_hash=file_hash,
                        file_size=file_size,
                        mime_type=file.content_type or "application/octet-stream",
                        storage_path=file_path,
                        reference_count=1
                    )
                    self.db.add(physical_file)
                    self.db.flush()  # Get ID without committing
                else:
                    # Another process created it while we were waiting for lock
                    physical_file.reference_count += 1
            else:
                # Increment reference count for existing file (already locked)
                physical_file.reference_count += 1
            
            # Create file record
            file_record = File(
                physical_file_id=physical_file.id,
                original_name=file.filename,
                file_type=file_type,
                course_id=course_id,
                folder_id=folder_id,
                user_id=user_id,
                is_processed=False,
                processing_status="pending"
            )
            
            self.db.add(file_record)
            self.db.commit()
            self.db.refresh(file_record)
            
            # Load physical file relationship
            self.db.refresh(physical_file)
            file_record.physical_file = physical_file
            
            # 内测阶段直接同步处理RAG（10人左右，无需异步）
            self._process_file_with_rag_sync(file_record, file_content)
            
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
                # Process with RAG service (传递数据库会话)
                print(f"🔧 正在创建RAG服务，数据库会话: {self.db}")
                rag_service = ProductionRAGService(db_session=self.db)
                print(f"🔧 RAG服务创建成功，开始处理文件...")
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
            joinedload(File.course),
            joinedload(File.physical_file)
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
        if not file_record.physical_file or not file_record.physical_file.storage_path:
            raise BadRequestError("File path not found", "FILE_PATH_NOT_FOUND")
        
        file_content = local_file_storage.download_file(file_record.physical_file.storage_path)
        if file_content is None:
            raise BadRequestError("Failed to read file from local storage", "LOCAL_READ_FAILED")
        
        return file_record, file_content

    def delete_file(self, file_id: int, user_id: int) -> bool:
        """Delete file (check access via course ownership)"""
        # Get file with course info
        file_record = self.db.query(File).options(
            joinedload(File.course),
            joinedload(File.physical_file)
        ).filter(File.id == file_id).first()
        
        if not file_record:
            raise NotFoundError("File not found", "FILE_NOT_FOUND")
        
        # Check if user has access via course ownership
        if file_record.course.user_id != user_id:
            raise ForbiddenError("You don't have permission to delete this file")

        physical_file = file_record.physical_file
        
        # Delete the file record first
        self.db.delete(file_record)
        
        # Decrease reference count for physical file with proper locking
        if physical_file:
            # Lock the physical file row to prevent race conditions
            locked_physical_file = self.db.query(PhysicalFile).filter(
                PhysicalFile.id == physical_file.id
            ).with_for_update().first()
            
            if locked_physical_file:
                locked_physical_file.reference_count -= 1
                
                # If no more references, delete the physical file and record
                if locked_physical_file.reference_count <= 0:
                    try:
                        local_file_storage.delete_file(locked_physical_file.storage_path)
                    except Exception as e:
                        print(f"⚠️ Failed to delete file from local storage: {e}")
                        # Continue to delete database record even if local file deletion fails
                    
                    self.db.delete(locked_physical_file)
        
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