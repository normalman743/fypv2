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
from app.models.temporary_file import TemporaryFile
from app.core.exceptions import NotFoundError, ForbiddenError, BadRequestError
from app.services.local_file_storage import local_file_storage
from app.utils.file_validation import validate_regular_file_upload, FileValidator

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
        import logging
        logging.info(f"[FileUpload] Starting upload - course_id: {course_id}, folder_id: {folder_id}, user_id: {user_id}, filename: {file.filename}")
        
        # Check if course exists and user has access
        course = self.db.query(Course).filter(
            Course.id == course_id,
            Course.user_id == user_id
        ).first()
        if not course:
            logging.error(f"[FileUpload] Course {course_id} not found or user {user_id} has no access")
            raise NotFoundError("Course not found or access denied", "COURSE_NOT_FOUND")

        # Check if folder exists and belongs to the course
        folder = self.db.query(Folder).filter(
            Folder.id == folder_id,
            Folder.course_id == course_id
        ).first()
        if not folder:
            logging.error(f"[FileUpload] Folder {folder_id} not found or does not belong to course {course_id}")
            # Log available folders for debugging
            available_folders = self.db.query(Folder.id, Folder.name).filter(Folder.course_id == course_id).all()
            logging.info(f"[FileUpload] Available folders for course {course_id}: {available_folders}")
            raise NotFoundError("Folder not found or does not belong to course", "FOLDER_NOT_FOUND")

        # 上传到本地存储
        try:
            file_path, local_path = local_file_storage.upload_file(file, course_id, folder_id)
        except Exception as e:
            raise BadRequestError(f"Failed to upload file to local storage: {e}", "LOCAL_UPLOAD_FAILED")

        # 获取文件大小和哈希 - 使用流式处理避免内存溢出
        from app.utils.file_stream_utils import get_file_size_and_hash
        file_size, file_hash = get_file_size_and_hash(file.file)

        # Determine file type based on content and extension
        file_type = self._determine_file_type(file.filename, file.content_type)

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
            
            logging.info(f"[FileUpload] Creating file record with folder_id: {folder_id}")
            self.db.add(file_record)
            self.db.commit()
            self.db.refresh(file_record)
            logging.info(f"[FileUpload] File record created - id: {file_record.id}, folder_id: {file_record.folder_id}")
            
            # Load physical file relationship
            self.db.refresh(physical_file)
            file_record.physical_file = physical_file
            
            # 内测阶段直接同步处理RAG（10人左右，无需异步）
            self._process_file_with_rag_sync(file_record, local_path)
            
            return file_record
        except IntegrityError:
            self.db.rollback()
            # 如果数据库操作失败，删除已上传的本地文件
            local_file_storage.delete_file(file_path)
            raise BadRequestError("Failed to upload file", "FILE_UPLOAD_FAILED")

    def _start_async_rag_processing(self, file_record: File, file_path: str) -> str:
        """启动异步RAG处理任务"""
        try:
            # 尝试导入Celery任务
            from app.tasks.file_processing import process_file_rag_task
            
            # 启动异步任务 - 传递文件路径而非文件内容，避免内存浪费
            task = process_file_rag_task.delay(file_record.id, file_path)
            
            print(f"🚀 Started async RAG processing for file {file_record.id}, task ID: {task.id}")
            return str(task.id)
            
        except ImportError:
            print("⚠️ Celery not available, falling back to synchronous processing")
            # 降级到同步处理
            self._process_file_with_rag_sync(file_record, file_path)
            return "sync_processing"
        except Exception as e:
            print(f"❌ Failed to start async task: {e}")
            # 降级到同步处理
            self._process_file_with_rag_sync(file_record, file_path)
            return "sync_fallback"
    
    def _process_file_with_rag_sync(self, file_record: File, file_path: str):
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
            
            try:
                # Process with RAG service directly using the saved file path
                print(f"🔧 正在创建RAG服务，数据库会话: {self.db}")
                rag_service = ProductionRAGService(db_session=self.db)
                print(f"🔧 RAG服务创建成功，开始处理文件: {file_path}")
                result = rag_service.process_file(file_record, file_path)
                
                print(f"✅ RAG processing completed: {result}")
                
                # Update status to completed
                file_record.is_processed = True
                file_record.processing_status = "completed"
                self.db.commit()
                
            except Exception as e:
                print(f"❌ RAG processing failed: {e}")
                file_record.processing_status = "failed"
                self.db.commit()
                    
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

    def download_file(self, file_id: int, user_id: int) -> Tuple[File, str]:
        """Get file for download (check access via course ownership)
        
        Returns:
            Tuple of (file_record, file_path) - file_path is the absolute disk path
        """
        file_record = self.get_file_preview(file_id, user_id)  # Same access logic
        
        # 获取本地存储文件路径
        if not file_record.physical_file or not file_record.physical_file.storage_path:
            raise BadRequestError("File path not found", "FILE_PATH_NOT_FOUND")
        
        file_path = local_file_storage.get_file_path(file_record.physical_file.storage_path)
        if not os.path.exists(file_path):
            raise BadRequestError("File not found on disk", "LOCAL_FILE_NOT_FOUND")
        
        return file_record, file_path

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

    # ==================== 全局文件管理 ====================

    def upload_global_file(
        self,
        file: UploadFile,
        user_id: int,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        visibility: str = 'public'
    ) -> File:
        """上传全局文件（管理员专用）"""
        valid, error_msg = validate_regular_file_upload(file.filename)
        if not valid:
            raise BadRequestError(error_msg, "INVALID_FILE_TYPE")
        
        from app.utils.file_stream_utils import get_file_size_and_hash
        file_size, file_hash = get_file_size_and_hash(file.file)
        
        # 检查是否已存在
        existing = self.db.query(File).filter(
            File.file_hash == file_hash,
            File.scope == 'global'
        ).first()
        if existing:
            raise BadRequestError(
                f"文件已存在: {existing.original_name} (ID: {existing.id})",
                "FILE_ALREADY_EXISTS"
            )
        
        # 获取或创建物理文件
        physical_file = self.db.query(PhysicalFile).filter(
            PhysicalFile.file_hash == file_hash
        ).first()
        
        if physical_file:
            physical_file.reference_count += 1
        else:
            storage_path = f"global/{file_hash}_{file.filename}"
            full_path = local_file_storage.base_dir / storage_path
            os.makedirs(full_path.parent, exist_ok=True)
            
            import shutil
            with open(full_path, "wb") as f:
                file.file.seek(0)
                shutil.copyfileobj(file.file, f)
                file.file.seek(0)
            
            physical_file = PhysicalFile(
                file_hash=file_hash,
                file_size=file_size,
                mime_type=file.content_type or "application/octet-stream",
                storage_path=str(storage_path),
                reference_count=1
            )
            self.db.add(physical_file)
            self.db.flush()
        
        file_type = self._determine_file_type(file.filename, file.content_type)
        
        file_record = File(
            physical_file_id=physical_file.id,
            original_name=file.filename,
            file_type=file_type,
            scope='global',
            visibility=visibility,
            course_id=None,
            folder_id=None,
            user_id=user_id,
            file_size=file_size,
            mime_type=file.content_type or "application/octet-stream",
            file_hash=file_hash,
            description=description,
            tags=tags,
            is_processed=False,
            processing_status="pending"
        )
        self.db.add(file_record)
        self.db.commit()
        self.db.refresh(file_record)
        
        # 触发RAG处理
        self._process_global_file_rag(file_record, physical_file)
        
        return file_record

    def _process_global_file_rag(self, file_record: File, physical_file: PhysicalFile):
        """处理全局文件的RAG"""
        try:
            full_path = local_file_storage.base_dir / physical_file.storage_path
            
            is_valid, error_msg = FileValidator.validate_document_parsing(
                str(full_path), file_record.original_name
            )
            if not is_valid:
                file_record.processing_status = "failed"
                file_record.processing_error = error_msg
                self.db.commit()
                return
            
            if RAG_AVAILABLE:
                rag_service = ProductionRAGService(db_session=self.db)
                rag_service.process_file(file_record, str(full_path))
                file_record.is_processed = True
                file_record.processing_status = "completed"
            else:
                file_record.is_processed = True
                file_record.processing_status = "completed"
        except Exception as e:
            file_record.processing_status = "failed"
            file_record.processing_error = str(e)
        self.db.commit()

    def get_global_files(self, visibility: Optional[str] = None) -> List[File]:
        """获取全局文件列表"""
        query = self.db.query(File).filter(File.scope == 'global')
        if visibility:
            query = query.filter(File.visibility == visibility)
        return query.all()

    def delete_global_file(self, file_id: int) -> bool:
        """删除全局文件"""
        file_record = self.db.query(File).filter(
            File.id == file_id,
            File.scope == 'global'
        ).first()
        
        if not file_record:
            raise NotFoundError("Global file not found", "FILE_NOT_FOUND")
        
        physical_file = file_record.physical_file
        self.db.delete(file_record)
        
        if physical_file:
            physical_file.reference_count -= 1
            if physical_file.reference_count <= 0:
                try:
                    full_path = local_file_storage.base_dir / physical_file.storage_path
                    if os.path.exists(full_path):
                        os.remove(full_path)
                    self.db.delete(physical_file)
                except Exception as e:
                    import logging
                    logging.warning(f"Failed to delete physical file: {e}")
        
        self.db.commit()
        return True

    def upload_temporary_file(self, file: UploadFile, user_id: int, purpose: str = None, expiry_hours: int = None) -> TemporaryFile:
        """上传临时文件（不关联课程，自动过期）"""
        import uuid
        from datetime import datetime, timedelta
        from app.utils.file_stream_utils import get_file_size_and_hash
        
        # 上传到本地存储（临时文件目录）
        try:
            file_path, local_path = local_file_storage.upload_file(file, course_id=0, folder_id=0)
        except Exception as e:
            raise BadRequestError(f"Failed to upload temporary file: {e}", "LOCAL_UPLOAD_FAILED")
        
        # 获取文件大小和哈希
        file_size, file_hash = get_file_size_and_hash(file.file)
        
        # 文件类型
        file_type = self._determine_file_type(file.filename, file.content_type)
        
        try:
            # 查找或创建物理文件
            physical_file = self.db.query(PhysicalFile).filter(
                PhysicalFile.file_hash == file_hash
            ).with_for_update().first()
            
            if not physical_file:
                physical_file = PhysicalFile(
                    file_hash=file_hash,
                    file_size=file_size,
                    mime_type=file.content_type or "application/octet-stream",
                    storage_path=file_path,
                    reference_count=1
                )
                self.db.add(physical_file)
                self.db.flush()
            else:
                physical_file.reference_count += 1
            
            # 过期时间
            if expiry_hours is None:
                try:
                    from app.core.config import settings
                    expiry_hours = getattr(settings, 'temporary_file_expiry_hours', 24)
                except Exception:
                    expiry_hours = 24
            
            # 创建临时文件记录
            temp_file = TemporaryFile(
                physical_file_id=physical_file.id,
                original_name=file.filename,
                file_type=file_type,
                file_size=file_size,
                mime_type=file.content_type or "application/octet-stream",
                user_id=user_id,
                token=uuid.uuid4().hex,
                expires_at=datetime.utcnow() + timedelta(hours=expiry_hours),
                purpose=purpose
            )
            self.db.add(temp_file)
            self.db.commit()
            self.db.refresh(temp_file)
            
            return temp_file
        except IntegrityError:
            self.db.rollback()
            local_file_storage.delete_file(file_path)
            raise BadRequestError("Failed to upload temporary file", "TEMP_UPLOAD_FAILED")

    def download_temporary_file(self, token: str) -> Tuple[TemporaryFile, str]:
        """下载临时文件（通过token访问，无需登录验证）
        
        Returns:
            Tuple of (temp_file, file_path)
        """
        temp_file = self.db.query(TemporaryFile).options(
            joinedload(TemporaryFile.physical_file)
        ).filter(TemporaryFile.token == token).first()
        
        if not temp_file:
            raise NotFoundError("临时文件不存在", "TEMP_FILE_NOT_FOUND")
        
        if temp_file.is_expired:
            raise BadRequestError("临时文件已过期", "TEMP_FILE_EXPIRED")
        
        if not temp_file.physical_file or not temp_file.physical_file.storage_path:
            raise BadRequestError("临时文件物理路径不存在", "TEMP_FILE_PATH_NOT_FOUND")
        
        file_path = local_file_storage.get_file_path(temp_file.physical_file.storage_path)
        if not os.path.exists(file_path):
            raise BadRequestError("临时文件在磁盘上不存在", "TEMP_FILE_DISK_NOT_FOUND")
        
        return temp_file, str(file_path)

    def delete_temporary_file(self, file_id: int, user_id: int) -> bool:
        """删除临时文件（只能删除自己上传的）"""
        temp_file = self.db.query(TemporaryFile).options(
            joinedload(TemporaryFile.physical_file)
        ).filter(
            TemporaryFile.id == file_id,
            TemporaryFile.user_id == user_id
        ).first()
        
        if not temp_file:
            raise NotFoundError("临时文件不存在或无权限", "TEMP_FILE_NOT_FOUND")
        
        physical_file = temp_file.physical_file
        self.db.delete(temp_file)
        
        if physical_file:
            physical_file.reference_count -= 1
            if physical_file.reference_count <= 0:
                try:
                    full_path = local_file_storage.get_file_path(physical_file.storage_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                    self.db.delete(physical_file)
                except Exception as e:
                    import logging
                    logging.warning(f"Failed to delete physical temp file: {e}")
        
        self.db.commit()
        return True