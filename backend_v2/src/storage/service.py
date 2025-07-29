"""Storage模块Service层业务逻辑"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc
from datetime import datetime, timedelta
import os
import hashlib
from pathlib import Path

from src.shared.exceptions import BaseServiceException
from .models import PhysicalFile, Folder, File, DocumentChunk, FileShare, FileAccessLog, FileGroup, FileGroupMember, TemporaryFile
from .schemas import CreateFolderRequest, UpdateFolderRequest, CreateFileShareRequest


class StorageServiceException(BaseServiceException):
    """Storage服务异常基类"""
    pass


class FolderService:
    """文件夹管理服务"""
    
    # 定义方法可能抛出的异常
    METHOD_EXCEPTIONS = {
        "get_course_folders": [StorageServiceException],
        "create_folder": [StorageServiceException],
        "update_folder": [StorageServiceException],
        "delete_folder": [StorageServiceException],
        "get_folder_stats": [StorageServiceException],
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_course_folders(self, course_id: int, user_id: int) -> List[Folder]:
        """获取课程的所有文件夹"""
        try:
            # 验证用户是否有权限访问该课程
            from src.course.models import Course
            from src.auth.models import User
            
            # 先获取当前用户
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise StorageServiceException("用户不存在", "USER_NOT_FOUND")
            
            # 然后检查课程权限
            course = self.db.query(Course).filter(Course.id == course_id).first()
            if not course:
                raise StorageServiceException("课程不存在", "COURSE_NOT_FOUND")
            
            # 验证权限：课程拥有者或管理员
            if course.user_id != user_id and user.role != "admin":
                raise StorageServiceException("无权限访问该课程", "ACCESS_DENIED")
            
            # 获取文件夹列表
            folders = self.db.query(Folder)\
                .filter(Folder.course_id == course_id)\
                .order_by(Folder.is_default.desc(), Folder.created_at.asc())\
                .all()
                
            return folders
            
        except StorageServiceException:
            raise
        except Exception as e:
            raise StorageServiceException(f"获取文件夹列表失败: {str(e)}", "DATABASE_ERROR")
    
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
                raise StorageServiceException("课程不存在或无权限访问", "COURSE_NOT_FOUND")
            
            # 检查同名文件夹
            existing_folder = self.db.query(Folder).filter(
                Folder.course_id == course_id,
                Folder.name == folder_data.name
            ).first()
            
            if existing_folder:
                raise StorageServiceException("文件夹名称已存在", "FOLDER_NAME_EXISTS")
            
            # 创建文件夹
            folder = Folder(
                name=folder_data.name,
                folder_type=folder_data.folder_type,
                course_id=course_id
            )
            
            self.db.add(folder)
            self.db.commit()
            self.db.refresh(folder)
            
            return folder
            
        except StorageServiceException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise StorageServiceException(f"创建文件夹失败: {str(e)}", "DATABASE_ERROR")
    
    def update_folder(self, folder_id: int, folder_data: UpdateFolderRequest, user_id: int) -> Folder:
        """更新文件夹"""
        try:
            # 获取文件夹并验证权限
            folder = self.db.query(Folder)\
                .join(Folder.course)\
                .filter(
                    Folder.id == folder_id,
                    or_(Course.user_id == user_id, Course.user.has(role="admin"))
                ).first()
            
            if not folder:
                raise StorageServiceException("文件夹不存在或无权限访问", "FOLDER_NOT_FOUND")
            
            # 更新字段
            if folder_data.name is not None:
                # 检查同名文件夹
                existing_folder = self.db.query(Folder).filter(
                    Folder.course_id == folder.course_id,
                    Folder.name == folder_data.name,
                    Folder.id != folder_id
                ).first()
                
                if existing_folder:
                    raise StorageServiceException("文件夹名称已存在", "FOLDER_NAME_EXISTS")
                
                folder.name = folder_data.name
            
            if folder_data.folder_type is not None:
                folder.folder_type = folder_data.folder_type
            
            self.db.commit()
            self.db.refresh(folder)
            
            return folder
            
        except StorageServiceException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise StorageServiceException(f"更新文件夹失败: {str(e)}", "DATABASE_ERROR")
    
    def delete_folder(self, folder_id: int, user_id: int) -> None:
        """删除文件夹"""
        try:
            # 获取文件夹并验证权限
            folder = self.db.query(Folder)\
                .join(Folder.course)\
                .filter(
                    Folder.id == folder_id,
                    or_(Course.user_id == user_id, Course.user.has(role="admin"))
                ).first()
            
            if not folder:
                raise StorageServiceException("文件夹不存在或无权限访问", "FOLDER_NOT_FOUND")
            
            # 检查是否为默认文件夹
            if folder.is_default:
                raise StorageServiceException("无法删除默认文件夹", "CANNOT_DELETE_DEFAULT_FOLDER")
            
            # 检查文件夹是否为空
            file_count = self.db.query(File).filter(File.folder_id == folder_id).count()
            if file_count > 0:
                raise StorageServiceException("文件夹不为空，无法删除", "FOLDER_NOT_EMPTY")
            
            # 删除文件夹
            self.db.delete(folder)
            self.db.commit()
            
        except StorageServiceException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise StorageServiceException(f"删除文件夹失败: {str(e)}", "DATABASE_ERROR")
    
    def get_folder_stats(self, folder_id: int) -> dict:
        """获取文件夹统计信息"""
        try:
            file_count = self.db.query(File).filter(File.folder_id == folder_id).count()
            
            return {
                "file_count": file_count
            }
            
        except Exception as e:
            raise StorageServiceException(f"获取文件夹统计失败: {str(e)}", "DATABASE_ERROR")


class FileService:
    """文件管理服务"""
    
    METHOD_EXCEPTIONS = {
        "get_folder_files": [StorageServiceException],
        "upload_file": [StorageServiceException],
        "download_file": [StorageServiceException],
        "delete_file": [StorageServiceException],
        "get_or_create_physical_file": [StorageServiceException],
        "calculate_file_hash": [],
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_folder_files(self, folder_id: int, user_id: int) -> List[File]:
        """获取文件夹中的所有文件"""
        try:
            # 验证用户权限
            folder = self.db.query(Folder)\
                .join(Folder.course)\
                .filter(
                    Folder.id == folder_id,
                    or_(Course.user_id == user_id, Course.user.has(role="admin"))
                ).first()
            
            if not folder:
                raise StorageServiceException("文件夹不存在或无权限访问", "FOLDER_NOT_FOUND")
            
            # 获取文件列表
            files = self.db.query(File)\
                .options(joinedload(File.folder))\
                .filter(File.folder_id == folder_id)\
                .order_by(desc(File.created_at))\
                .all()
                
            return files
            
        except StorageServiceException:
            raise
        except Exception as e:
            raise StorageServiceException(f"获取文件列表失败: {str(e)}", "DATABASE_ERROR")
    
    def upload_file(self, file_data, course_id: int, folder_id: int, user_id: int, description: Optional[str] = None) -> File:
        """上传文件"""
        try:
            # 验证权限
            folder = self.db.query(Folder)\
                .join(Folder.course)\
                .filter(
                    Folder.id == folder_id,
                    Folder.course_id == course_id,
                    or_(Course.user_id == user_id, Course.user.has(role="admin"))
                ).first()
            
            if not folder:
                raise StorageServiceException("文件夹不存在或无权限访问", "FOLDER_NOT_FOUND")
            
            # 读取文件内容和计算哈希
            file_content = file_data.file.read()
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
            
        except StorageServiceException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise StorageServiceException(f"文件上传失败: {str(e)}", "UPLOAD_ERROR")
    
    def download_file(self, file_id: int, user_id: int, access_type: str = "download") -> Tuple[File, str]:
        """下载文件"""
        try:
            # 获取文件并验证权限
            file_record = self.db.query(File)\
                .options(joinedload(File.physical_file))\
                .filter(File.id == file_id)\
                .first()
            
            if not file_record:
                raise StorageServiceException("文件不存在", "FILE_NOT_FOUND")
            
            # 验证访问权限
            if file_record.scope == 'course':
                # 课程文件需要验证课程权限
                from src.course.models import Course
                course = self.db.query(Course).filter(
                    Course.id == file_record.course_id,
                    or_(Course.user_id == user_id, Course.user.has(role="admin"))
                ).first()
                
                if not course:
                    raise StorageServiceException("无权限访问该文件", "ACCESS_DENIED")
            
            elif file_record.scope == 'temporary':
                # 临时文件只能被创建者访问
                if file_record.user_id != user_id:
                    raise StorageServiceException("无权限访问该文件", "ACCESS_DENIED")
            
            # 记录访问日志
            access_log = FileAccessLog(
                file_id=file_id,
                user_id=user_id,
                access_type=access_type
            )
            self.db.add(access_log)
            self.db.commit()
            
            return file_record, file_record.physical_file.storage_path
            
        except StorageServiceException:
            raise
        except Exception as e:
            raise StorageServiceException(f"文件下载失败: {str(e)}", "DATABASE_ERROR")
    
    def delete_file(self, file_id: int, user_id: int) -> None:
        """删除文件"""
        try:
            # 获取文件并验证权限
            file_record = self.db.query(File).filter(File.id == file_id).first()
            
            if not file_record:
                raise StorageServiceException("文件不存在", "FILE_NOT_FOUND")
            
            # 验证权限：只能删除自己的文件或管理员
            from src.auth.models import User
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if file_record.user_id != user_id and user.role != "admin":
                raise StorageServiceException("无权限删除该文件", "ACCESS_DENIED")
            
            # 删除文件记录
            self.db.delete(file_record)
            self.db.commit()
            
        except StorageServiceException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise StorageServiceException(f"删除文件失败: {str(e)}", "DATABASE_ERROR")
    
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
            
            # 创建新的物理文件
            # 这里需要实际的文件存储逻辑，暂时用占位符
            storage_path = f"files/{file_hash[:2]}/{file_hash}"
            
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
            
            # TODO: 实际保存文件到存储路径
            
            return physical_file
            
        except Exception as e:
            self.db.rollback()
            raise StorageServiceException(f"处理物理文件失败: {str(e)}", "STORAGE_ERROR")
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """计算文件SHA256哈希值"""
        return hashlib.sha256(file_content).hexdigest()


class TemporaryFileService:
    """临时文件管理服务"""
    
    METHOD_EXCEPTIONS = {
        "upload_temporary_file": [StorageServiceException],
        "download_temporary_file": [StorageServiceException],
        "delete_temporary_file": [StorageServiceException],
        "cleanup_expired_files": [StorageServiceException],
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def upload_temporary_file(self, file_data, user_id: int, expiry_hours: int = 24, purpose: Optional[str] = None) -> TemporaryFile:
        """上传临时文件"""
        try:
            # 计算过期时间
            expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
            
            # 读取文件内容
            file_content = file_data.file.read()
            
            # 这里应该保存文件到临时存储位置
            # 暂时用占位符路径
            file_path = f"temp/{user_id}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file_data.filename}"
            
            # 创建临时文件记录
            temp_file = TemporaryFile(
                filename=file_data.filename,
                file_path=file_path,
                file_size=len(file_content),
                mime_type=file_data.content_type,
                user_id=user_id,
                expires_at=expires_at
            )
            
            self.db.add(temp_file)
            self.db.commit()
            self.db.refresh(temp_file)
            
            # TODO: 实际保存文件到临时存储位置
            
            return temp_file
            
        except Exception as e:
            self.db.rollback()
            raise StorageServiceException(f"上传临时文件失败: {str(e)}", "UPLOAD_ERROR")
    
    def download_temporary_file(self, file_id: int, user_id: int) -> Tuple[TemporaryFile, str]:
        """下载临时文件"""
        try:
            # 获取临时文件
            temp_file = self.db.query(TemporaryFile).filter(
                TemporaryFile.id == file_id,
                TemporaryFile.user_id == user_id
            ).first()
            
            if not temp_file:
                raise StorageServiceException("临时文件不存在", "TEMP_FILE_NOT_FOUND")
            
            # 检查是否过期
            if temp_file.expires_at < datetime.utcnow():
                raise StorageServiceException("临时文件已过期", "TEMP_FILE_EXPIRED")
            
            return temp_file, temp_file.file_path
            
        except StorageServiceException:
            raise
        except Exception as e:
            raise StorageServiceException(f"下载临时文件失败: {str(e)}", "DATABASE_ERROR")
    
    def delete_temporary_file(self, file_id: int, user_id: int) -> None:
        """删除临时文件"""
        try:
            temp_file = self.db.query(TemporaryFile).filter(
                TemporaryFile.id == file_id,
                TemporaryFile.user_id == user_id
            ).first()
            
            if not temp_file:
                raise StorageServiceException("临时文件不存在", "TEMP_FILE_NOT_FOUND")
            
            # 删除文件记录
            self.db.delete(temp_file)
            self.db.commit()
            
            # TODO: 删除实际文件
            
        except StorageServiceException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise StorageServiceException(f"删除临时文件失败: {str(e)}", "DATABASE_ERROR")
    
    def cleanup_expired_files(self) -> int:
        """清理过期的临时文件"""
        try:
            # 查找过期文件
            expired_files = self.db.query(TemporaryFile).filter(
                TemporaryFile.expires_at < datetime.utcnow()
            ).all()
            
            count = len(expired_files)
            
            # 删除过期文件
            for temp_file in expired_files:
                self.db.delete(temp_file)
                # TODO: 删除实际文件
            
            self.db.commit()
            
            return count
            
        except Exception as e:
            self.db.rollback()
            raise StorageServiceException(f"清理过期文件失败: {str(e)}", "DATABASE_ERROR")