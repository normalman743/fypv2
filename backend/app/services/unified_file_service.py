import hashlib
import os
import tempfile
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from app.models.file import File
from app.models.physical_file import PhysicalFile
from app.models.file_share import FileShare, FileAccessLog
from app.models.user import User
from app.models.course import Course
from app.models.temporary_file import TemporaryFile
from app.services.local_file_storage import local_file_storage
from app.services.rag_service import ProductionRAGService
from app.utils.file_validation import validate_regular_file_upload, validate_temporary_file_upload, FileValidator
import secrets
from datetime import datetime, timedelta


class UnifiedFileService:
    """统一文件服务 - 替代原来的 file_service 和 global_file_service"""
    
    def __init__(self, db: Session):
        self.db = db

    def upload_file(
        self,
        file: UploadFile,
        user_id: int,
        scope: str = 'course',
        course_id: Optional[int] = None,
        folder_id: Optional[int] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        visibility: str = 'private'
    ) -> File:
        """
        统一文件上传接口
        
        Args:
            file: 上传的文件
            user_id: 上传用户ID
            scope: 文件作用域 ('course', 'global', 'personal')
            course_id: 课程ID (scope='course'时必需)
            folder_id: 文件夹ID (可选)
            description: 文件描述
            tags: 标签列表
            visibility: 可见性 ('private', 'course', 'public', 'shared')
        """
        
        # 1. 验证参数
        self._validate_upload_params(scope, course_id, folder_id, user_id)
        
        # 2. 验证文件类型（白名单）
        valid, error_msg = validate_regular_file_upload(file.filename)
        if not valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 3. 读取和处理文件内容 - 使用流式处理避免内存溢出
        from app.utils.file_stream_utils import get_file_size_and_hash
        file_size, file_hash = get_file_size_and_hash(file.file)
        
        # 调试信息
        print(f"File upload: {file.filename}, size: {file_size}, hash: {file_hash}")
        
        file_info = {
            'original_name': file.filename,
            'mime_type': file.content_type or "application/octet-stream",
            'file_size': file_size,
            'file_hash': file_hash
        }
        
        # 3. 检查是否已存在相同文件
        existing_file = self._check_existing_file(file_hash, user_id, scope, course_id)
        if existing_file:
            from app.core.exceptions import BadRequestError
            raise BadRequestError(
                f"文件已存在: {existing_file.original_name} (ID: {existing_file.id})，您可以直接使用该文件",
                "FILE_ALREADY_EXISTS"
            )
        
        # 4. 获取或创建 PhysicalFile - 传递文件对象而非内容
        physical_file = self._get_or_create_physical_file(file_info, file.file, scope)
        
        # 5. 创建 File 记录
        file_record = self._create_file_record(
            physical_file=physical_file,
            file_info=file_info,
            user_id=user_id,
            scope=scope,
            course_id=course_id,
            folder_id=folder_id,
            description=description,
            tags=tags,
            visibility=visibility
        )
        
        # 6. 触发 RAG 处理
        self._trigger_rag_processing(file_record, physical_file)
        
        return file_record

    def _validate_upload_params(self, scope: str, course_id: Optional[int], folder_id: Optional[int], user_id: int):
        """验证上传参数"""
        if scope not in ['course', 'global', 'personal']:
            raise HTTPException(status_code=400, detail="Invalid scope")
        
        if scope == 'course' and not course_id:
            raise HTTPException(status_code=400, detail="course_id is required for course scope")
        
        if scope == 'course' and course_id:
            # 验证用户是否有权限上传到该课程
            course = self.db.query(Course).filter(Course.id == course_id).first()
            if not course:
                raise HTTPException(status_code=404, detail="Course not found")
            # TODO: 添加课程权限检查
            
            # 对于课程文件，folder_id是必需的（与API文档保持一致）
            if folder_id is None:
                raise HTTPException(status_code=400, detail="folder_id is required for course scope")
            
            # 验证文件夹是否存在且属于该课程
            from app.models.folder import Folder
            folder = self.db.query(Folder).filter(
                Folder.id == folder_id,
                Folder.course_id == course_id
            ).first()
            if not folder:
                raise HTTPException(
                    status_code=404, 
                    detail="Folder not found or does not belong to course"
                )

    def _check_existing_file(
        self, 
        file_hash: str, 
        user_id: int, 
        scope: str, 
        course_id: Optional[int]
    ) -> Optional[File]:
        """检查是否已存在相同文件"""
        # 确保hash不为空
        if not file_hash:
            return None
            
        query = self.db.query(File).filter(
            File.file_hash == file_hash,
            File.user_id == user_id,
            File.scope == scope
        )
        
        if scope == 'course' and course_id:
            query = query.filter(File.course_id == course_id)
        
        existing_file = query.first()
        if existing_file:
            print(f"Found existing file with hash {file_hash}: {existing_file.id}")
        
        return existing_file

    def _get_or_create_physical_file(
        self, 
        file_info: dict, 
        file_obj, 
        scope: str
    ) -> PhysicalFile:
        """获取或创建 PhysicalFile 记录"""
        
        # 检查是否已存在相同 hash 的物理文件
        physical_file = self.db.query(PhysicalFile).filter(
            PhysicalFile.file_hash == file_info['file_hash']
        ).first()
        
        if physical_file:
            # 更新引用计数
            physical_file.reference_count += 1
            self.db.commit()
            return physical_file
        
        # 创建新的物理文件
        storage_path = self._generate_storage_path(file_info, scope)
        full_path = local_file_storage.base_dir / storage_path
        
        # 确保目录存在
        os.makedirs(full_path.parent, exist_ok=True)
        
        # 保存文件 - 使用流式写入避免内存溢出
        import shutil
        with open(full_path, "wb") as f:
            file_obj.seek(0)
            shutil.copyfileobj(file_obj, f)  # 流式复制，不占用大量内存
            file_obj.seek(0)  # 重置文件指针
        
        # 创建数据库记录
        physical_file = PhysicalFile(
            file_hash=file_info['file_hash'],
            file_size=file_info['file_size'],
            mime_type=file_info['mime_type'],
            storage_path=str(storage_path),
            reference_count=1
        )
        
        self.db.add(physical_file)
        self.db.commit()
        self.db.refresh(physical_file)
        
        return physical_file

    def _generate_storage_path(self, file_info: dict, scope: str) -> str:
        """生成存储路径"""
        file_hash = file_info['file_hash']
        original_name = file_info['original_name']
        
        if scope == 'global':
            return f"global/{file_hash}_{original_name}"
        elif scope == 'course':
            return f"course/{file_hash}_{original_name}"
        elif scope == 'temporary':
            return f"temporary/{file_hash}_{original_name}"
        else:  # personal
            return f"personal/{file_hash}_{original_name}"

    def _create_file_record(
        self,
        physical_file: PhysicalFile,
        file_info: dict,
        user_id: int,
        scope: str,
        course_id: Optional[int],
        folder_id: Optional[int],
        description: Optional[str],
        tags: Optional[List[str]],
        visibility: str
    ) -> File:
        """创建 File 记录"""
        
        # 推断文件类型
        file_type = self._infer_file_type(file_info['mime_type'], file_info['original_name'])
        
        file_record = File(
            physical_file_id=physical_file.id,
            original_name=file_info['original_name'],
            file_type=file_type,
            scope=scope,
            visibility=visibility,
            course_id=course_id,
            folder_id=folder_id,
            user_id=user_id,
            file_size=file_info['file_size'],
            mime_type=file_info['mime_type'],
            file_hash=file_info['file_hash'],
            description=description,
            tags=tags,
            is_processed=False,
            processing_status="pending"
        )
        
        self.db.add(file_record)
        self.db.commit()
        self.db.refresh(file_record)
        
        return file_record

    def _infer_file_type(self, mime_type: str, filename: str) -> str:
        """推断文件类型"""
        if 'pdf' in mime_type.lower():
            return 'pdf'
        elif 'document' in mime_type.lower() or filename.endswith(('.doc', '.docx')):
            return 'doc'
        elif 'text' in mime_type.lower() or filename.endswith(('.txt', '.md')):
            return 'txt'
        else:
            return 'unknown'

    def _trigger_rag_processing(self, file_record: File, physical_file: PhysicalFile):
        """触发 RAG 处理"""
        try:
            full_path = local_file_storage.base_dir / physical_file.storage_path
            
            # 先验证文件内容是否可解析
            is_valid, error_msg = FileValidator.validate_document_parsing(
                str(full_path), file_record.original_name
            )
            
            if not is_valid:
                # 内容验证失败，标记为失败状态
                file_record.processing_status = "failed"
                file_record.processing_error = error_msg
                file_record.is_processed = False
                self.db.commit()
                return
            
            # 内容验证通过，执行RAG处理
            rag_service = ProductionRAGService(db_session=self.db)
            rag_service.process_file(file_record, str(full_path))
            
            file_record.is_processed = True
            file_record.processing_status = "completed"
        except Exception as e:
            file_record.processing_status = "failed"
            file_record.processing_error = str(e)
        
        self.db.commit()

    # 共享相关方法
    def share_file(
        self,
        file_id: int,
        shared_with_type: str,
        shared_with_id: Optional[int],
        permission_level: str,
        shared_by: int,
        can_reshare: bool = False,
        expires_at: Optional[str] = None
    ) -> FileShare:
        """共享文件"""
        
        # 验证文件存在且有权限
        file_record = self.db.query(File).filter(File.id == file_id).first()
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        if file_record.user_id != shared_by:
            raise HTTPException(status_code=403, detail="No permission to share this file")
        
        # 创建共享记录
        share = FileShare(
            file_id=file_id,
            shared_with_type=shared_with_type,
            shared_with_id=shared_with_id,
            permission_level=permission_level,
            shared_by=shared_by,
            can_reshare=can_reshare,
            expires_at=expires_at
        )
        
        self.db.add(share)
        self.db.commit()
        self.db.refresh(share)
        
        return share

    def get_accessible_files(
        self,
        user_id: int,
        scope: Optional[str] = None,
        course_id: Optional[int] = None,
        include_shared: bool = True
    ) -> List[File]:
        """获取用户可访问的文件列表"""
        
        query = self.db.query(File)
        
        # 基础过滤
        if scope:
            query = query.filter(File.scope == scope)
        if course_id:
            query = query.filter(File.course_id == course_id)
        
        # 权限过滤
        conditions = []
        
        # 1. 用户拥有的文件
        conditions.append(File.user_id == user_id)
        
        # 2. 公开文件
        if scope == 'global' or not scope:
            conditions.append(File.visibility == 'public')
        
        # 3. 课程文件 (如果用户是课程成员)
        if course_id:
            conditions.append(
                (File.scope == 'course') & 
                (File.course_id == course_id) & 
                (File.visibility.in_(['course', 'public']))
            )
        
        # 4. 共享给用户的文件
        if include_shared:
            shared_file_ids = self.db.query(FileShare.file_id).filter(
                FileShare.shared_with_type == 'user',
                FileShare.shared_with_id == user_id
            ).subquery()
            
            conditions.append(File.id.in_(shared_file_ids))
        
        # 应用条件
        if conditions:
            from sqlalchemy import or_
            query = query.filter(or_(*conditions))
        
        return query.all()

    def log_file_access(
        self,
        file_id: int,
        user_id: int,
        action: str,
        access_via: str = 'direct',
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """记录文件访问日志"""
        
        log = FileAccessLog(
            file_id=file_id,
            user_id=user_id,
            action=action,
            access_via=access_via,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(log)
        self.db.commit()

    def delete_file(self, file_id: int, user_id: int) -> bool:
        """删除文件"""
        
        file_record = self.db.query(File).filter(
            File.id == file_id,
            File.user_id == user_id
        ).first()
        
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found or no permission")
        
        # 删除文件记录
        self.db.delete(file_record)
        
        # 更新 PhysicalFile 引用计数
        physical_file = file_record.physical_file
        physical_file.reference_count -= 1
        
        # 如果没有其他引用，删除物理文件
        if physical_file.reference_count <= 0:
            try:
                full_path = local_file_storage.base_dir / physical_file.storage_path
                if os.path.exists(full_path):
                    os.remove(full_path)
                self.db.delete(physical_file)
            except Exception as e:
                # 记录日志但不阻断删除
                print(f"Failed to delete physical file: {e}")
        
        self.db.commit()
        return True

    # 迁移兼容方法
    def upload_global_file(
        self,
        file: UploadFile,
        description: str,
        tags: list,
        user_id: int
    ) -> File:
        """兼容原 global_file_service.upload_global_file 方法"""
        return self.upload_file(
            file=file,
            user_id=user_id,
            scope='global',
            description=description,
            tags=tags,
            visibility='public'
        )

    def upload_temporary_file(
        self,
        file: UploadFile,
        user_id: int,
        purpose: Optional[str] = None,
        expiry_hours: Optional[int] = None
    ) -> TemporaryFile:
        """
        上传临时文件 - 复用普通文件上传的去重逻辑
        
        Args:
            file: 上传的文件
            user_id: 上传用户ID
            purpose: 用途说明，如 'chat_upload', 'preview' 等
            expiry_hours: 过期小时数
        """
        
        # 1. 验证文件类型（文档+图片）
        valid, error_msg = validate_temporary_file_upload(file.filename)
        if not valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 2. 读取和处理文件内容 - 使用流式处理避免内存溢出
        from app.utils.file_stream_utils import get_file_size_and_hash
        file_size, file_hash = get_file_size_and_hash(file.file)
        
        print(f"Temporary file upload: {file.filename}, size: {file_size}, hash: {file_hash}")
        
        file_info = {
            'original_name': file.filename,
            'mime_type': file.content_type or "application/octet-stream",
            'file_size': file_size,
            'file_hash': file_hash
        }
        
        # 3. 获取或创建 PhysicalFile - 传递文件对象而非内容
        physical_file = self._get_or_create_physical_file(file_info, file.file, scope='temporary')
        
        # 4. 生成唯一token
        token = secrets.token_urlsafe(32)
        
        # 5. 计算过期时间
        if expiry_hours is None:
            from app.core.config import settings
            expiry_hours = getattr(settings, 'temporary_file_expiry_hours', 24)
        
        expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
        
        # 6. 创建临时文件记录
        temp_file = TemporaryFile(
            physical_file_id=physical_file.id,
            original_name=file.filename,
            file_type=file.filename.split('.')[-1] if '.' in file.filename else '',
            file_size=file_size,
            mime_type=file.content_type or "application/octet-stream",
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            purpose=purpose
        )
        
        self.db.add(temp_file)
        self.db.commit()
        self.db.refresh(temp_file)
        
        print(f"✅ Temporary file created: ID={temp_file.id}, Token={token[:16]}...")
        
        return temp_file

    def get_temporary_file_by_token(self, token: str) -> Optional[TemporaryFile]:
        """通过token获取临时文件"""
        return self.db.query(TemporaryFile).filter(
            TemporaryFile.token == token,
            TemporaryFile.expires_at > datetime.utcnow()
        ).first()

    def get_temporary_file_by_id(self, file_id: int, user_id: int) -> Optional[TemporaryFile]:
        """通过ID获取用户的临时文件"""
        return self.db.query(TemporaryFile).filter(
            TemporaryFile.id == file_id,
            TemporaryFile.user_id == user_id,
            TemporaryFile.expires_at > datetime.utcnow()
        ).first()

    def download_temporary_file(self, token: str) -> Tuple[TemporaryFile, bytes]:
        """
        通过token下载临时文件
        
        Returns:
            (temp_file, file_content): 临时文件对象和文件内容
        """
        temp_file = self.get_temporary_file_by_token(token)
        if not temp_file:
            raise HTTPException(status_code=404, detail="文件不存在或已过期")
        
        # 获取物理文件
        physical_file = temp_file.physical_file
        if not physical_file:
            raise HTTPException(status_code=404, detail="物理文件不存在")
        
        # 安全地构建文件路径
        file_path = self._validate_and_resolve_path(physical_file.storage_path)
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            return temp_file, content
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="文件不存在")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")

    def delete_temporary_file(self, temp_file: TemporaryFile) -> bool:
        """
        删除临时文件
        
        Args:
            temp_file: 要删除的临时文件对象
            
        Returns:
            是否删除成功
        """
        try:
            # 删除临时文件记录
            self.db.delete(temp_file)
            
            # 更新物理文件引用计数
            physical_file = temp_file.physical_file
            if physical_file:
                physical_file.reference_count -= 1
                
                # 如果没有其他引用，删除物理文件
                if physical_file.reference_count <= 0:
                    try:
                        file_path = self._validate_and_resolve_path(physical_file.storage_path)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        self.db.delete(physical_file)
                    except Exception as e:
                        print(f"Failed to delete physical file: {e}")
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Failed to delete temporary file: {e}")
            return False

    def _validate_and_resolve_path(self, storage_path: str) -> str:
        """
        验证并解析安全的文件路径
        
        Args:
            storage_path: 存储路径
            
        Returns:
            完整的安全文件路径
            
        Raises:
            HTTPException: 路径不安全时抛出异常
        """
        # 如果已经是绝对路径，直接验证
        if os.path.isabs(storage_path):
            full_path = storage_path
        else:
            # 相对路径，基于base_dir构建
            full_path = local_file_storage.base_dir / storage_path
            full_path = str(full_path)
        
        # 规范化路径
        full_path = os.path.normpath(full_path)
        base_dir = str(local_file_storage.base_dir.resolve())
        
        # 检查路径是否在允许的目录内（防止目录遍历攻击）
        if not full_path.startswith(base_dir):
            raise HTTPException(status_code=403, detail="访问被拒绝：路径不在允许范围内")
        
        return full_path