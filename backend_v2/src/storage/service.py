"""Storage模块Service层业务逻辑"""
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc
from datetime import datetime, timedelta
import os
import hashlib
from pathlib import Path
from fastapi import UploadFile

from src.shared.exceptions import (
    BaseServiceException, NotFoundServiceException, 
    ConflictServiceException, ValidationServiceException, AccessDeniedServiceException,
    BadRequestServiceException, handle_service_exceptions
)
from src.shared.error_codes import ErrorCodes
from src.shared.base_service import BaseService
from src.shared.config import settings
from .models import PhysicalFile, Folder, File, DocumentChunk, FileShare, FileAccessLog, FileGroup, FileGroupMember, TemporaryFile
from .schemas import CreateFolderRequest, UpdateFolderRequest, CreateFileShareRequest
from .file_storage import get_file_storage



class FolderService(BaseService):
    """文件夹管理服务"""
    
    # 定义方法可能抛出的异常
    METHOD_EXCEPTIONS = {
        "get_course_folders": {NotFoundServiceException, AccessDeniedServiceException, ValidationServiceException},
        "create_folder": {NotFoundServiceException, AccessDeniedServiceException, ConflictServiceException, ValidationServiceException},  
        "update_folder": {NotFoundServiceException, AccessDeniedServiceException, ConflictServiceException, ValidationServiceException},
        "delete_folder": {NotFoundServiceException, AccessDeniedServiceException, ConflictServiceException, ValidationServiceException},
        "get_folder_stats": {ValidationServiceException},
    }
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def get_course_folders(self, course_id: int, user_id: int) -> List[Folder]:
        """获取课程的所有文件夹"""
        try:
            # 验证用户是否有权限访问该课程
            from src.course.models import Course
            from src.auth.models import User
            
            # 先获取当前用户
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise NotFoundServiceException("用户不存在", ErrorCodes.USER_NOT_FOUND)
            
            # 然后检查课程权限
            course = self.db.query(Course).filter(Course.id == course_id).first()
            if not course:
                raise NotFoundServiceException("课程不存在", ErrorCodes.COURSE_NOT_FOUND)
            
            # 验证权限：课程拥有者或管理员
            if course.user_id != user_id and user.role != "admin":
                raise AccessDeniedServiceException("无权限访问该课程", ErrorCodes.ACCESS_DENIED)
            
            # 获取文件夹列表
            folders = self.db.query(Folder)\
                .filter(Folder.course_id == course_id)\
                .order_by(Folder.is_default.desc(), Folder.created_at.asc())\
                .all()
                
            return folders
            
        except (NotFoundServiceException, AccessDeniedServiceException):
            raise
        except Exception as e:
            raise ValidationServiceException(f"获取文件夹列表失败: {str(e)}", ErrorCodes.DATABASE_ERROR)
    
    def create_folder(self, course_id: int, folder_data: CreateFolderRequest, user_id: int) -> Folder:
        """创建文件夹"""
        try:
            # 验证用户是否有权限在该课程创建文件夹
            from src.course.models import Course
            course = self.db.query(Course).filter(
                Course.id == course_id,
                or_(Course.user_id == user_id, Course.user.has(role="admin"))
            ).first()
            
            if not course:
                raise NotFoundServiceException("课程不存在或无权限访问", ErrorCodes.COURSE_NOT_FOUND)
            
            # 检查同名文件夹
            existing_folder = self.db.query(Folder).filter(
                Folder.course_id == course_id,
                Folder.name == folder_data.name
            ).first()
            
            if existing_folder:
                raise ConflictServiceException("文件夹名称已存在", ErrorCodes.FOLDER_NAME_EXISTS)
            
            # 创建文件夹
            folder = Folder(
                name=folder_data.name,
                folder_type=folder_data.folder_type,
                course_id=course_id
            )
            
            self.db.add(folder)
            try:
                self.db.commit()
                self.db.refresh(folder)
            except Exception as e:
                self.db.rollback()
                raise ValidationServiceException(f"创建文件夹失败: {str(e)}", ErrorCodes.DATABASE_ERROR)
            
            return folder
            
        except (NotFoundServiceException, ConflictServiceException):
            self.handle_database_error("创建文件夹", ValidationServiceException("业务错误"))
            raise
        except Exception as e:
            self.handle_database_error("创建文件夹", e)
            raise ValidationServiceException(f"创建文件夹失败: {str(e)}", ErrorCodes.DATABASE_ERROR)
    
    def update_folder(self, folder_id: int, folder_data: UpdateFolderRequest, user_id: int) -> Folder:
        """更新文件夹"""
        try:
            from src.course.models import Course
            # 获取文件夹并验证权限
            folder = self.db.query(Folder)\
                .join(Folder.course)\
                .filter(
                    Folder.id == folder_id,
                    or_(Course.user_id == user_id, Course.user.has(role="admin"))
                ).first()
            
            if not folder:
                raise NotFoundServiceException("文件夹不存在或无权限访问", ErrorCodes.FOLDER_NOT_FOUND)
            
            # 更新字段
            if folder_data.name is not None:
                # 检查同名文件夹
                existing_folder = self.db.query(Folder).filter(
                    Folder.course_id == folder.course_id,
                    Folder.name == folder_data.name,
                    Folder.id != folder_id
                ).first()
                
                if existing_folder:
                    raise ConflictServiceException("文件夹名称已存在", ErrorCodes.FOLDER_NAME_EXISTS)
                
                folder.name = folder_data.name
            
            if folder_data.folder_type is not None:
                folder.folder_type = folder_data.folder_type
            
            self.db.commit()
            self.db.refresh(folder)
            
            return folder
            
        except (NotFoundServiceException, ConflictServiceException):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationServiceException(f"更新文件夹失败: {str(e)}", ErrorCodes.DATABASE_ERROR)
    
    def delete_folder(self, folder_id: int, user_id: int) -> None:
        """删除文件夹"""
        try:
            from src.course.models import Course
            
            # 获取文件夹并验证权限
            folder = self.db.query(Folder)\
                .join(Folder.course)\
                .filter(
                    Folder.id == folder_id,
                    or_(Course.user_id == user_id, Course.user.has(role="admin"))
                ).first()
            
            if not folder:
                raise NotFoundServiceException("文件夹不存在或无权限访问", ErrorCodes.FOLDER_NOT_FOUND)
            
            # 检查是否为默认文件夹
            if folder.is_default:
                raise ConflictServiceException("无法删除默认文件夹", ErrorCodes.CANNOT_DELETE_DEFAULT_FOLDER)
            
            # 检查文件夹是否为空
            file_count = self.db.query(File).filter(File.folder_id == folder_id).count()
            if file_count > 0:
                raise ConflictServiceException("文件夹不为空，无法删除", ErrorCodes.FOLDER_NOT_EMPTY)
            
            # 删除文件夹
            self.db.delete(folder)
            self.db.commit()
            
        except (NotFoundServiceException, ConflictServiceException):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationServiceException(f"删除文件夹失败: {str(e)}", ErrorCodes.DATABASE_ERROR)
    
    def get_folder_stats(self, folder_id: int) -> dict:
        """获取文件夹统计信息"""
        try:
            file_count = self.db.query(File).filter(File.folder_id == folder_id).count()
            
            return {
                "file_count": file_count
            }
            
        except Exception as e:
            raise ValidationServiceException(f"获取文件夹统计失败: {str(e)}", ErrorCodes.DATABASE_ERROR)


class FileService(BaseService):
    """文件管理服务"""
    
    METHOD_EXCEPTIONS = {
        "get_folder_files": {NotFoundServiceException, AccessDeniedServiceException, ValidationServiceException},
        "upload_file": {NotFoundServiceException, AccessDeniedServiceException, BadRequestServiceException, ValidationServiceException},
        "upload_file_async": {NotFoundServiceException, AccessDeniedServiceException, BadRequestServiceException, ValidationServiceException},
        "download_file": {NotFoundServiceException, AccessDeniedServiceException, ValidationServiceException},
        "delete_file": {NotFoundServiceException, AccessDeniedServiceException, ValidationServiceException},
        "get_or_create_physical_file": {ValidationServiceException},
        "calculate_file_hash": set(),
    }
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def get_folder_files(self, folder_id: int, user_id: int) -> List[File]:
        """获取文件夹中的所有文件 not used ，use asyn instead"""
        try:
            from src.course.models import Course
            
            # 验证用户权限
            folder = self.db.query(Folder)\
                .join(Folder.course)\
                .filter(
                    Folder.id == folder_id,
                    or_(Course.user_id == user_id, Course.user.has(role="admin"))
                ).first()
            
            if not folder:
                raise NotFoundServiceException("文件夹不存在或无权限访问", ErrorCodes.FOLDER_NOT_FOUND)
            
            # 获取文件列表
            files = self.db.query(File)\
                .options(joinedload(File.folder))\
                .filter(File.folder_id == folder_id)\
                .order_by(desc(File.created_at))\
                .all()
                
            return files
            
        except (NotFoundServiceException, ValidationServiceException):
            raise
        except Exception as e:
            raise ValidationServiceException(f"获取文件列表失败: {str(e)}", ErrorCodes.DATABASE_ERROR)
    
    async def upload_file_async(self, file_data, course_id: int, folder_id: int, user_id: int, description: Optional[str] = None, strict: bool = True) -> File:
        """异步上传文件"""
        try:
            from src.course.models import Course
            
            # 验证权限
            folder = self.db.query(Folder)\
                .join(Folder.course)\
                .filter(
                    Folder.id == folder_id,
                    Folder.course_id == course_id,
                    or_(Course.user_id == user_id, Course.user.has(role="admin"))
                ).first()
            
            if not folder:
                raise NotFoundServiceException("文件夹不存在或无权限访问", ErrorCodes.FOLDER_NOT_FOUND)
            
            # 第一层验证：文件类型检查（扩展名）
            self._validate_file_extension(file_data.filename, scope="course", strict=strict)
            
            # 异步读取文件内容
            import asyncio
            loop = asyncio.get_event_loop()
            file_content = await loop.run_in_executor(None, file_data.file.read)
            
            # 文件大小限制检查
            self._validate_file_limits(
                file_size=len(file_content),
                course_id=course_id,
                user_id=user_id
            )
            
            # 第二层验证：尝试解析文件内容
            self._validate_file_parsing(file_content, file_data.filename)
            
            file_hash = self.calculate_file_hash(file_content)
            
            # 获取或创建物理文件
            physical_file = self.get_or_create_physical_file(
                file_content, file_hash, file_data.content_type, len(file_content)
            )
            
            # 创建文件记录
            file_record = File(
                physical_file_id=physical_file.id,
                original_name=file_data.filename,
                file_type=Path(file_data.filename).suffix.lower().lstrip('.'),
                description=description,
                scope='course',
                course_id=course_id,
                folder_id=folder_id,
                user_id=user_id,
                file_size=len(file_content),
                mime_type=file_data.content_type,
                file_hash=file_hash
            )
            
            self.db.add(file_record)
            self.db.commit()
            self.db.refresh(file_record)
            
            # 启动异步RAG处理
            await self._trigger_async_vectorization(file_record.id, user_id)
            
            return file_record
            
        except (NotFoundServiceException, ConflictServiceException):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationServiceException(f"文件上传失败: {str(e)}", ErrorCodes.UPLOAD_ERROR)
    
    def upload_file(self, file_data, course_id: int, folder_id: int, user_id: int, description: Optional[str] = None) -> File:
        """上传文件
        
        @deprecated: 已弃用，请使用 upload_file_async 异步版本
        """
        try:
            from src.course.models import Course
            
            # 验证权限
            folder = self.db.query(Folder)\
                .join(Folder.course)\
                .filter(
                    Folder.id == folder_id,
                    Folder.course_id == course_id,
                    or_(Course.user_id == user_id, Course.user.has(role="admin"))
                ).first()
            
            if not folder:
                raise NotFoundServiceException("文件夹不存在或无权限访问", ErrorCodes.FOLDER_NOT_FOUND)
            
            # 第一层验证：文件类型检查（扩展名）
            self._validate_file_extension(file_data.filename, scope="course")
            
            # 读取文件内容和计算哈希
            file_content = file_data.file.read()
            
            # 文件大小限制检查
            self._validate_file_limits(
                file_size=len(file_content),
                course_id=course_id,
                user_id=user_id
            )
            
            # 第二层验证：尝试解析文件内容
            self._validate_file_parsing(file_content, file_data.filename)
            
            file_hash = self.calculate_file_hash(file_content)
            
            # 获取或创建物理文件
            physical_file = self.get_or_create_physical_file(
                file_content, file_hash, file_data.content_type, len(file_content)
            )
            
            # 创建文件记录
            file_record = File(
                physical_file_id=physical_file.id,
                original_name=file_data.filename,
                file_type=Path(file_data.filename).suffix.lower().lstrip('.'),
                description=description,
                scope='course',
                course_id=course_id,
                folder_id=folder_id,
                user_id=user_id,
                file_size=len(file_content),
                mime_type=file_data.content_type,
                file_hash=file_hash
            )
            
            self.db.add(file_record)
            self.db.commit()
            self.db.refresh(file_record)
            
            return file_record
            
        except (NotFoundServiceException, ConflictServiceException):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationServiceException(f"文件上传失败: {str(e)}", ErrorCodes.UPLOAD_ERROR)
    
    @handle_service_exceptions
    def download_file(self, file_id: int, user_id: int, access_type: str = "download") -> Tuple[File, bytes]:
        """下载文件"""
        try:
            # 获取文件并验证权限
            file_record = self.db.query(File)\
                .options(joinedload(File.physical_file))\
                .filter(File.id == file_id)\
                .first()
            
            if not file_record:
                raise NotFoundServiceException("文件不存在", ErrorCodes.FILE_NOT_FOUND)
            
            # 验证访问权限
            if file_record.scope == 'course':
                # 课程文件需要验证课程权限
                from src.course.models import Course
                course = self.db.query(Course).filter(
                    Course.id == file_record.course_id,
                    or_(Course.user_id == user_id, Course.user.has(role="admin"))
                ).first()
                
                if not course:
                    raise AccessDeniedServiceException("无权限访问该文件", ErrorCodes.ACCESS_DENIED)
            
            elif file_record.scope == 'temporary':
                # 临时文件只能被创建者访问
                if file_record.user_id != user_id:
                    raise AccessDeniedServiceException("无权限访问该文件", ErrorCodes.ACCESS_DENIED)
            
            # 从存储中读取文件内容
            file_storage = get_file_storage()
            file_content = file_storage.read_file(file_record.physical_file.storage_path)
            
            if file_content is None:
                raise NotFoundServiceException("文件不存在于存储中", ErrorCodes.FILE_MISSING)
            
            # 记录访问日志
            access_log = FileAccessLog(
                file_id=file_id,
                user_id=user_id,
                access_type=access_type
            )
            self.db.add(access_log)
            try:
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                raise ValidationServiceException(f"记录文件访问日志失败: {str(e)}", ErrorCodes.DATABASE_ERROR)
            
            return file_record, file_content
            
        except (NotFoundServiceException, ValidationServiceException):
            raise
        except Exception as e:
            raise ValidationServiceException(f"文件下载失败: {str(e)}", ErrorCodes.DATABASE_ERROR)
    
    @handle_service_exceptions
    def delete_file(self, file_id: int, user_id: int) -> None:
        """删除文件"""
        try:
            # 获取文件及其物理文件信息
            file_record = self.db.query(File)\
                .options(joinedload(File.physical_file))\
                .filter(File.id == file_id)\
                .first()
            
            if not file_record:
                raise NotFoundServiceException("文件不存在", ErrorCodes.FILE_NOT_FOUND)
            
            # 验证权限：只能删除自己的文件或管理员
            from src.auth.models import User
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if file_record.user_id != user_id and user.role != "admin":
                raise AccessDeniedServiceException("无权限删除该文件", ErrorCodes.ACCESS_DENIED)
            
            # 获取物理文件信息
            physical_file = file_record.physical_file
            
            # 删除文件记录
            self.db.delete(file_record)
            
            # 减少物理文件引用计数
            if physical_file:
                physical_file.reference_count -= 1
                
                # 如果没有引用了，删除物理文件
                if physical_file.reference_count <= 0:
                    file_storage = get_file_storage()
                    file_storage.delete_file(physical_file.storage_path)
                    self.db.delete(physical_file)
            
            self.db.commit()
            
        except (NotFoundServiceException, AccessDeniedServiceException):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationServiceException(f"删除文件失败: {str(e)}", ErrorCodes.DATABASE_ERROR)
    
    @handle_service_exceptions
    def get_or_create_physical_file(self, file_content: bytes, file_hash: str, mime_type: str, file_size: int) -> PhysicalFile:
        """获取或创建物理文件"""
        try:
            # 查找现有的物理文件
            physical_file = self.db.query(PhysicalFile).filter(
                PhysicalFile.file_hash == file_hash
            ).first()
            
            if physical_file:
                # 增加引用计数
                physical_file.reference_count += 1
                self.db.commit()
                return physical_file
            
            # 获取文件存储实例
            file_storage = get_file_storage()
            
            # 获取文件扩展名（如果有的话）
            file_extension = ""
            if mime_type.startswith("image/"):
                ext_map = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif"}
                file_extension = ext_map.get(mime_type, "")
            elif mime_type == "application/pdf":
                file_extension = ".pdf"
            elif mime_type.startswith("text/"):
                file_extension = ".txt"
            
            # 实际保存文件到存储路径
            storage_path, _ = file_storage.save_file_by_hash(file_content, file_hash, file_extension)
            
            # 创建物理文件记录
            physical_file = PhysicalFile(
                file_hash=file_hash,
                file_size=file_size,
                mime_type=mime_type,
                storage_path=storage_path,
                reference_count=1
            )
            
            self.db.add(physical_file)
            self.db.commit()
            self.db.refresh(physical_file)
            
            return physical_file
            
        except Exception as e:
            self.db.rollback()
            raise ValidationServiceException(f"处理物理文件失败: {str(e)}", ErrorCodes.STORAGE_ERROR)
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """计算文件SHA256哈希值"""
        return hashlib.sha256(file_content).hexdigest()
    
    def _validate_file_limits(self, file_size: int, course_id: int = None, user_id: int = None) -> None:
        """统一的文件限制检查"""
        
        # 1. 单文件大小检查
        if file_size > settings.max_file_size:  # 50MB
            raise BadRequestServiceException(
                f"文件大小超过限制，最大允许{settings.max_file_size // 1024 // 1024}MB", 
                ErrorCodes.FILE_TOO_LARGE
            )
        
        # 2. Course文件：检查课程存储限制
        if course_id:
            course_usage = self._get_course_storage_usage(course_id)
            if course_usage + file_size > settings.max_course_size:  # 200MB
                raise BadRequestServiceException(
                    f"课程存储空间不足，已使用{course_usage // 1024 // 1024}MB，限制{settings.max_course_size // 1024 // 1024}MB", 
                    ErrorCodes.STORAGE_LIMIT_EXCEEDED
                )
        
        # 3. 用户总存储检查（Course + Temp）
        if user_id:
            user_usage = self._get_user_storage_usage(user_id)
            if user_usage + file_size > settings.max_user_storage:  # 1GB
                raise BadRequestServiceException(
                    f"个人存储空间不足，已使用{user_usage // 1024 // 1024}MB，限制{settings.max_user_storage // 1024 // 1024}MB", 
                    ErrorCodes.STORAGE_LIMIT_EXCEEDED
                )
    
    def _validate_file_extension(self, filename: str, scope: str = "course", strict: bool = True) -> None:
        """第一层验证：文件扩展名检查（仅在严格模式下执行）"""
        if not strict:
            return  # 非严格模式：跳过第一层验证
        
        import os
        file_ext = os.path.splitext(filename)[1].lower()
        
        if scope == "temp":
            # 临时文件：文档 + 图片
            allowed_extensions = settings.allowed_temp_extensions_list
            scope_desc = "临时"
        else:
            # 课程和全局文件：仅文档
            allowed_extensions = settings.allowed_document_extensions_list
            scope_desc = "课程/全局"
        
        if file_ext not in allowed_extensions:
            allowed_str = ", ".join(allowed_extensions)
            raise BadRequestServiceException(
                f"不支持的文件类型 {file_ext}。{scope_desc}文件支持的类型: {allowed_str}",
                ErrorCodes.INVALID_FILE_EXTENSION
            )
    
    def _validate_file_parsing(self, file_content: bytes, filename: str) -> None:
        """第二层验证：尝试解析文件内容（严格和非严格模式都执行）"""
        # 第二层验证总是执行，无论是否严格模式
        
        import os
        file_ext = os.path.splitext(filename)[1].lower()
        
        # 跳过图片类型的解析验证
        if file_ext in settings.allowed_image_extensions_list:
            return
        
        # 尝试文本解析
        try:
            # 尝试UTF-8解码
            content = file_content.decode('utf-8')
            if len(content.strip()) < 10:  # 内容太短认为无效
                raise BadRequestServiceException(
                    f"文件内容过短或无效，无法用于RAG处理",
                    ErrorCodes.PROCESSING_ERROR
                )
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                content = file_content.decode('gbk')
                if len(content.strip()) < 10:
                    raise BadRequestServiceException(
                        f"文件内容过短或无效，无法用于RAG处理",
                        ErrorCodes.PROCESSING_ERROR
                    )
            except UnicodeDecodeError:
                # 对于二进制文件（如PDF），这里应该检查文件头
                if file_ext == '.pdf' and file_content.startswith(b'%PDF'):
                    return  # PDF文件有效
                elif file_ext in ['.docx', '.doc'] and b'PK' in file_content[:10]:
                    return  # Office文件有效
                else:
                    raise BadRequestServiceException(
                        f"无法解析文件内容，请确保文件格式正确",
                        ErrorCodes.PROCESSING_ERROR
                    )
    
    def _get_course_storage_usage(self, course_id: int) -> int:
        """获取课程当前存储使用量"""
        from sqlalchemy import func
        result = self.db.query(func.sum(File.file_size))\
            .filter(File.course_id == course_id, File.scope == 'course')\
            .scalar()
        return result or 0
    
    def _get_user_storage_usage(self, user_id: int) -> int:
        """获取用户总存储使用量"""
        from sqlalchemy import func
        
        # Course文件大小
        course_size = self.db.query(func.sum(File.file_size))\
            .filter(File.user_id == user_id, File.scope == 'course')\
            .scalar() or 0
            
        # 临时文件大小
        temp_size = self.db.query(func.sum(TemporaryFile.file_size))\
            .filter(TemporaryFile.user_id == user_id)\
            .scalar() or 0
            
        return course_size + temp_size
    
    async def _trigger_async_vectorization(self, file_id: int, user_id: int) -> None:
        """触发异步RAG向量化处理"""
        try:
            # 导入AI Service
            from src.ai.service import AIService
            
            # 在线程池中运行向量化处理，避免阻塞
            import asyncio
            loop = asyncio.get_event_loop()
            
            def run_vectorization():
                # 创建新的数据库会话用于后台处理
                from src.shared.database import SessionLocal
                bg_db = SessionLocal()
                try:
                    ai_service = AIService(bg_db)
                    result = ai_service.vectorize_file(file_id, user_id)
                    self.logger.info(f"文件 {file_id} RAG处理完成: {result}")
                    return result
                except Exception as e:
                    self.logger.error(f"文件 {file_id} RAG处理失败: {e}")
                    return {"status": "failed", "error": str(e)}
                finally:
                    bg_db.close()
            
            # 在后台线程中执行，不等待结果
            loop.run_in_executor(None, run_vectorization)
            self.logger.info(f"已启动文件 {file_id} 的异步RAG处理")
            
        except Exception as e:
            self.logger.warning(f"启动异步RAG处理失败 (file_id: {file_id}): {e}")
            # 不抛出异常，避免影响文件上传流程


class TemporaryFileService(BaseService):
    """临时文件管理服务"""
    
    METHOD_EXCEPTIONS = {
        "upload_temporary_file": {BadRequestServiceException, ValidationServiceException},
        "upload_temporary_file_async": {BadRequestServiceException, ValidationServiceException},
        "download_temporary_file": {NotFoundServiceException, ValidationServiceException},
        "delete_temporary_file": {NotFoundServiceException, ValidationServiceException},
        "cleanup_expired_files": {ValidationServiceException},
    }
    
    def __init__(self, db: Session):
        super().__init__(db)
        # 使用FileService中的通用方法
        self._file_service = FileService(db)
    
    
    @handle_service_exceptions
    async def upload_temporary_file_async(self, file_data: UploadFile, user_id: int, expiry_hours: int = 24, purpose: Optional[str] = None, strict: bool = True) -> TemporaryFile:
        """异步上传临时文件"""
        try:
            # 计算过期时间
            expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
            
            # 第一层验证：文件类型检查（扩展名）
            self._file_service._validate_file_extension(file_data.filename, scope="temp", strict=strict)
            
            # 异步读取文件内容
            import asyncio
            loop = asyncio.get_event_loop()
            file_data.file.seek(0)
            file_content = await loop.run_in_executor(None, file_data.file.read)
            file_data.file.seek(0)
            
            # 文件大小限制检查（临时文件只检查用户限制）
            self._file_service._validate_file_limits(
                file_size=len(file_content),
                user_id=user_id
            )
            
            # 获取文件存储实例并保存临时文件
            file_storage = get_file_storage()
            file_path, _ = file_storage.save_temporary_file(
                file_content, 
                user_id, 
                file_data.filename or "unknown"
            )
            
            # 创建临时文件记录
            temp_file = TemporaryFile(
                filename=file_data.filename or "unknown",
                file_path=file_path,
                file_size=len(file_content),
                mime_type=file_data.content_type or "application/octet-stream",
                user_id=user_id,
                expires_at=expires_at,
                purpose=purpose
            )
            
            self.db.add(temp_file)
            self.db.commit()
            self.db.refresh(temp_file)
            
            return temp_file
            
        except Exception as e:
            self.db.rollback()
            raise ValidationServiceException(f"上传临时文件失败: {str(e)}", ErrorCodes.UPLOAD_ERROR)
    
    @handle_service_exceptions
    def upload_temporary_file(self, file_data: UploadFile, user_id: int, expiry_hours: int = 24, purpose: Optional[str] = None) -> TemporaryFile:
        """上传临时文件
        
        @deprecated: 已弃用，请使用 upload_temporary_file_async 异步版本
        """
        try:
            # 计算过期时间
            expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
            
            # 第一层验证：文件类型检查（扩展名）
            self._file_service._validate_file_extension(file_data.filename, scope="temp")
            
            # 读取文件内容
            file_data.file.seek(0)
            file_content = file_data.file.read()
            file_data.file.seek(0)
            
            # 文件大小限制检查（临时文件只检查用户限制）
            self._file_service._validate_file_limits(
                file_size=len(file_content),
                user_id=user_id
            )
            
            # 获取文件存储实例并保存临时文件
            file_storage = get_file_storage()
            file_path, _ = file_storage.save_temporary_file(
                file_content, 
                user_id, 
                file_data.filename or "unknown"
            )
            
            # 创建临时文件记录
            temp_file = TemporaryFile(
                filename=file_data.filename or "unknown",
                file_path=file_path,
                file_size=len(file_content),
                mime_type=file_data.content_type or "application/octet-stream",
                user_id=user_id,
                expires_at=expires_at,
                purpose=purpose
            )
            
            self.db.add(temp_file)
            self.db.commit()
            self.db.refresh(temp_file)
            
            return temp_file
            
        except Exception as e:
            self.db.rollback()
            raise ValidationServiceException(f"上传临时文件失败: {str(e)}", ErrorCodes.UPLOAD_ERROR)
    
    @handle_service_exceptions
    def download_temporary_file(self, file_id: int, user_id: int) -> Tuple[TemporaryFile, bytes]:
        """下载临时文件"""
        try:
            # 获取临时文件
            temp_file = self.db.query(TemporaryFile).filter(
                TemporaryFile.id == file_id,
                TemporaryFile.user_id == user_id
            ).first()
            
            if not temp_file:
                raise NotFoundServiceException("临时文件不存在", ErrorCodes.TEMP_FILE_NOT_FOUND)
            
            # 检查是否过期
            if temp_file.expires_at < datetime.utcnow():
                raise ValidationServiceException("临时文件已过期", ErrorCodes.TEMP_FILE_EXPIRED)
            
            # 从存储中读取文件内容
            file_storage = get_file_storage()
            file_content = file_storage.read_file(temp_file.file_path)
            
            if file_content is None:
                raise NotFoundServiceException("临时文件不存在于存储中", ErrorCodes.TEMP_FILE_MISSING)
            
            return temp_file, file_content
            
        except (NotFoundServiceException, ValidationServiceException):
            raise
        except Exception as e:
            raise ValidationServiceException(f"下载临时文件失败: {str(e)}", ErrorCodes.DATABASE_ERROR)
    
    @handle_service_exceptions
    def delete_temporary_file(self, file_id: int, user_id: int) -> None:
        """删除临时文件"""
        try:
            temp_file = self.db.query(TemporaryFile).filter(
                TemporaryFile.id == file_id,
                TemporaryFile.user_id == user_id
            ).first()
            
            if not temp_file:
                raise NotFoundServiceException("临时文件不存在", ErrorCodes.TEMP_FILE_NOT_FOUND)
            
            # 删除实际文件
            file_storage = get_file_storage()
            file_storage.delete_file(temp_file.file_path)
            
            # 删除数据库记录
            self.db.delete(temp_file)
            self.db.commit()
            
        except NotFoundServiceException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationServiceException(f"删除临时文件失败: {str(e)}", ErrorCodes.DATABASE_ERROR)
    
    def cleanup_expired_files(self) -> int:
        """清理过期的临时文件"""
        try:
            # 查找过期文件
            expired_files = self.db.query(TemporaryFile).options(
                joinedload(TemporaryFile.physical_file)  # 预加载物理文件关系
            ).filter(
                TemporaryFile.expires_at < datetime.utcnow()
            ).all()
            
            count = len(expired_files)
            file_storage = get_file_storage()
            
            # 删除过期文件
            for temp_file in expired_files:
                physical_file = temp_file.physical_file
                
                # 删除临时文件记录
                self.db.delete(temp_file)
                
                # 更新物理文件引用计数
                if physical_file:
                    physical_file.reference_count -= 1
                    
                    # 如果没有其他引用，删除物理文件
                    if physical_file.reference_count <= 0:
                        try:
                            # 删除磁盘上的实际文件
                            file_storage.delete_file(physical_file.storage_path)
                            # 删除物理文件记录
                            self.db.delete(physical_file)
                        except Exception as e:
                            from src.shared.logging import get_logger
                            logger = get_logger(__name__)
                            logger.warning(f"Failed to delete physical file {physical_file.storage_path}: {e}")
                            # 继续执行，不阻断整个清理过程
            
            self.db.commit()
            
            # 清理空目录
            file_storage.cleanup_empty_directories()
            
            return count
            
        except Exception as e:
            self.db.rollback()
            raise ValidationServiceException(f"清理过期文件失败: {str(e)}", ErrorCodes.DATABASE_ERROR)


class GlobalFileService(BaseService):
    """全局文件管理服务（管理员专用）"""
    
    METHOD_EXCEPTIONS = {
        "upload_global_file": {ValidationServiceException, AccessDeniedServiceException},
        "get_global_files": {AccessDeniedServiceException, ValidationServiceException},
        "delete_global_file": {NotFoundServiceException, AccessDeniedServiceException, ValidationServiceException},
    }
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.file_storage = get_file_storage()
    
    def _validate_file_extension(self, filename: str, scope: str = "global", strict: bool = True) -> None:
        """第一层验证：文件扩展名检查（仅在严格模式下执行）"""
        if not settings.strict_file_validation:
            return  # 非严格模式：跳过第一层验证
        
        import os
        file_ext = os.path.splitext(filename)[1].lower()
        
        # 全局文件只允许文档类型
        allowed_extensions = settings.allowed_document_extensions_list
        
        if file_ext not in allowed_extensions:
            allowed_str = ", ".join(allowed_extensions)
            raise BadRequestServiceException(
                f"不支持的文件类型 {file_ext}。全局文件支持的类型: {allowed_str}",
                ErrorCodes.INVALID_FILE_EXTENSION
            )
    
    async def upload_global_file_async(
        self, 
        file: UploadFile, 
        admin_user_id: int,
        description: Optional[str] = None,
        strict: bool = True
    ) -> File:
        """异步上传全局文件（管理员专用）"""
        try:
            # 验证管理员权限
            from src.auth.models import User
            admin = self.db.query(User).filter(
                User.id == admin_user_id,
                User.role == "admin"
            ).first()
            if not admin:
                raise AccessDeniedServiceException("需要管理员权限", ErrorCodes.ADMIN_REQUIRED)

            # 第一层验证：文件类型检查（扩展名） - 全局文件只允许文档类型
            self._validate_file_extension(file.filename, scope="global", strict=strict)

            # 异步保存文件并获取哈希值
            import asyncio
            loop = asyncio.get_event_loop()
            storage_path, file_content, file_hash = await loop.run_in_executor(
                None, self.file_storage.save_upload_file, file
            )

            # 检查是否已存在相同哈希的物理文件
            physical_file = self.db.query(PhysicalFile).filter(
                PhysicalFile.file_hash == file_hash
            ).first()

            if not physical_file:
                physical_file = PhysicalFile(
                    file_hash=file_hash,
                    file_size=len(file_content),
                    mime_type=file.content_type or "application/octet-stream",
                    storage_path=storage_path,
                    reference_count=1
                )
                self.db.add(physical_file)
                self.db.flush()
            else:
                physical_file.reference_count += 1

            # 创建全局文件记录
            global_file = File(
                physical_file_id=physical_file.id,
                original_name=file.filename,
                file_type=self._determine_file_type(file.filename, file.content_type),
                description=description,
                scope='global',  # 关键：标记为全局文件
                visibility='public',
                course_id=None,
                folder_id=None,
                user_id=admin_user_id,
                file_size=len(file_content),
                mime_type=file.content_type,
                file_hash=file_hash,
                is_processed=False,
                processing_status="pending"
            )

            self.db.add(global_file)
            self.db.commit()
            self.db.refresh(global_file)

            # 启动异步RAG处理
            await self._trigger_async_vectorization(global_file.id, admin_user_id)

            return global_file

        except (AccessDeniedServiceException, ValidationServiceException):
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationServiceException(f"上传全局文件失败: {str(e)}", ErrorCodes.UPLOAD_ERROR)
    
    def upload_global_file(
        self, 
        file: UploadFile, 
        admin_user_id: int,
        description: Optional[str] = None
    ) -> File:
        """上传全局文件（管理员专用）
        
        @deprecated: 已弃用，请使用 upload_global_file_async 异步版本
        """
        try:
            # 验证管理员权限
            from src.auth.models import User
            admin = self.db.query(User).filter(
                User.id == admin_user_id,
                User.role == "admin"
            ).first()
            if not admin:
                raise AccessDeniedServiceException("需要管理员权限", ErrorCodes.ADMIN_REQUIRED)

            # 第一层验证：文件类型检查（扩展名） - 全局文件只允许文档类型
            self._validate_file_extension(file.filename, scope="global")

            # 保存文件并获取哈希值
            storage_path, file_content, file_hash = self.file_storage.save_upload_file(file)

            # 检查是否已存在相同哈希的物理文件
            physical_file = self.db.query(PhysicalFile).filter(
                PhysicalFile.file_hash == file_hash
            ).first()

            if not physical_file:
                physical_file = PhysicalFile(
                    file_hash=file_hash,
                    file_size=len(file_content),
                    mime_type=file.content_type or "application/octet-stream",
                    storage_path=storage_path,
                    reference_count=1
                )
                self.db.add(physical_file)
                self.db.flush()
            else:
                physical_file.reference_count += 1

            # 创建全局文件记录
            global_file = File(
                physical_file_id=physical_file.id,
                original_name=file.filename,
                file_type=self._determine_file_type(file.filename, file.content_type),
                description=description,
                scope='global',  # 关键：标记为全局文件
                visibility='public',
                course_id=None,
                folder_id=None,
                user_id=admin_user_id,
                file_size=len(file_content),
                mime_type=file.content_type,
                file_hash=file_hash,
                is_processed=False,
                processing_status="pending"
            )

            self.db.add(global_file)
            self.db.commit()
            self.db.refresh(global_file)

            return global_file

        except (AccessDeniedServiceException, ValidationServiceException):
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationServiceException(f"上传全局文件失败: {str(e)}", ErrorCodes.UPLOAD_ERROR)

    def get_global_files(
        self, 
        admin_user_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> List[File]:
        """获取全局文件列表（管理员专用）"""
        try:
            # 验证管理员权限
            from src.auth.models import User
            admin = self.db.query(User).filter(
                User.id == admin_user_id,
                User.role == "admin"
            ).first()
            if not admin:
                raise AccessDeniedServiceException("需要管理员权限", ErrorCodes.ADMIN_REQUIRED)

            # 查询全局文件
            files = self.db.query(File)\
                .options(joinedload(File.physical_file))\
                .filter(File.scope == 'global')\
                .order_by(desc(File.created_at))\
                .offset(skip)\
                .limit(limit)\
                .all()

            return files

        except AccessDeniedServiceException:
            raise
        except Exception as e:
            raise ValidationServiceException(f"获取全局文件列表失败: {str(e)}", ErrorCodes.QUERY_ERROR)

    def delete_global_file(self, file_id: int, admin_user_id: int) -> bool:
        """删除全局文件（管理员专用）"""
        try:
            # 验证管理员权限
            from src.auth.models import User
            admin = self.db.query(User).filter(
                User.id == admin_user_id,
                User.role == "admin"
            ).first()
            if not admin:
                raise AccessDeniedServiceException("需要管理员权限", ErrorCodes.ADMIN_REQUIRED)

            # 查找全局文件
            file_record = self.db.query(File).options(
                joinedload(File.physical_file)
            ).filter(
                File.id == file_id,
                File.scope == 'global'  # 确保是全局文件
            ).first()

            if not file_record:
                raise NotFoundServiceException("全局文件不存在", ErrorCodes.GLOBAL_FILE_NOT_FOUND)

            physical_file = file_record.physical_file

            # 删除文件记录
            self.db.delete(file_record)

            # 更新物理文件引用计数
            if physical_file:
                physical_file.reference_count -= 1

                # 如果没有其他引用，删除物理文件
                if physical_file.reference_count <= 0:
                    try:
                        self.file_storage.delete_file(physical_file.storage_path)
                        self.db.delete(physical_file)
                    except Exception as e:
                        from src.shared.logging import get_logger
                        logger = get_logger(__name__)
                        logger.warning(f"Failed to delete physical file: {e}")

            self.db.commit()
            return True

        except (NotFoundServiceException, AccessDeniedServiceException):
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationServiceException(f"删除全局文件失败: {str(e)}", ErrorCodes.DELETE_ERROR)

    def _determine_file_type(self, filename: str, content_type: str) -> str:
        """推断文件类型"""
        if not filename:
            return "unknown"

        filename_lower = filename.lower()
        if filename_lower.endswith('.pdf'):
            return "pdf"
        elif filename_lower.endswith(('.doc', '.docx')):
            return "document"
        elif filename_lower.endswith(('.jpg', '.jpeg', '.png', '.gif')):
            return "image"
        else:
            return "document"
    
    async def _trigger_async_vectorization(self, file_id: int, user_id: int) -> None:
        """触发异步RAG向量化处理"""
        try:
            # 导入AI Service
            from src.ai.service import AIService
            
            # 在线程池中运行向量化处理，避免阻塞
            import asyncio
            loop = asyncio.get_event_loop()
            
            def run_vectorization():
                # 创建新的数据库会话用于后台处理
                from src.shared.database import SessionLocal
                bg_db = SessionLocal()
                try:
                    ai_service = AIService(bg_db)
                    result = ai_service.vectorize_file(file_id, user_id)
                    self.logger.info(f"全局文件 {file_id} RAG处理完成: {result}")
                    return result
                except Exception as e:
                    self.logger.error(f"全局文件 {file_id} RAG处理失败: {e}")
                    return {"status": "failed", "error": str(e)}
                finally:
                    bg_db.close()
            
            # 在后台线程中执行，不等待结果
            loop.run_in_executor(None, run_vectorization)
            self.logger.info(f"已启动全局文件 {file_id} 的异步RAG处理")
            
        except Exception as e:
            self.logger.warning(f"启动异步RAG处理失败 (global file_id: {file_id}): {e}")
            # 不抛出异常，避免影响文件上传流程