import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.models.temporary_file import TemporaryFile
from app.models.physical_file import PhysicalFile
from app.models.user import User
from app.core.config import settings
from app.services.local_file_storage import local_file_storage
import hashlib
import logging

logger = logging.getLogger(__name__)

class TemporaryFileService:
    """临时文件服务"""
    
    @staticmethod
    async def upload_temporary_file(
        db: Session,
        user: User,
        file: UploadFile,
        purpose: Optional[str] = None,
        expiry_hours: Optional[int] = None
    ) -> TemporaryFile:
        """
        上传临时文件 - 基于现有FileService逻辑简化
        """
        try:
            logger.info(f"📤 上传临时文件: {file.filename} ({user.username})")
            
            # 使用现有的本地文件存储，临时文件也用course_id=0, folder_id=0
            file_path, local_path = local_file_storage.upload_file(file, course_id=0, folder_id=0)
            
            # 读取文件内容用于哈希计算
            file.file.seek(0)
            file_content = file.file.read()
            file_size = len(file_content)
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # 重置文件指针
            file.file.seek(0)
            
            logger.info(f"   文件大小: {file_size} bytes，哈希: {file_hash[:16]}...")
            
            # 检查物理文件是否已存在
            physical_file = db.query(PhysicalFile).filter(
                PhysicalFile.file_hash == file_hash
            ).first()
            
            if not physical_file:
                # 创建新的物理文件记录
                physical_file = PhysicalFile(
                    file_hash=file_hash,
                    file_size=file_size,
                    mime_type=file.content_type or "application/octet-stream",
                    storage_path=local_path,
                    reference_count=1
                )
                db.add(physical_file)
                db.flush()  # 获取ID
                logger.info(f"   ✅ 新物理文件记录已创建")
            else:
                # 增加引用计数
                physical_file.reference_count += 1
                logger.info(f"   🔄 复用现有物理文件，引用计数: {physical_file.reference_count}")
            
            # 生成唯一token
            token = secrets.token_urlsafe(32)
            
            # 计算过期时间
            if expiry_hours is None:
                expiry_hours = settings.temporary_file_expiry_hours
            expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
            
            # 创建临时文件记录
            temp_file = TemporaryFile(
                physical_file_id=physical_file.id,
                original_name=file.filename,
                file_type=file.filename.split('.')[-1] if '.' in file.filename else '',
                file_size=file_size,
                mime_type=file.content_type or "application/octet-stream",
                user_id=user.id,
                token=token,
                purpose=purpose,
                expires_at=expires_at
            )
            
            db.add(temp_file)
            db.commit()
            
            logger.info(f"   🎉 临时文件上传成功: token={token[:10]}..., 过期时间={expires_at}")
            return temp_file
            
        except Exception as e:
            logger.error(f"临时文件上传失败: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to upload temporary file: {str(e)}")
    
    @staticmethod
    def get_temporary_file_by_token(db: Session, token: str) -> Optional[TemporaryFile]:
        """通过token获取临时文件"""
        return db.query(TemporaryFile).filter(TemporaryFile.token == token).first()