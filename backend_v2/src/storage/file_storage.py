"""文件存储工具类 - 基于v1实现但适应v2架构"""
import os
import shutil
import hashlib
from pathlib import Path
from typing import Tuple, Optional, BinaryIO
from fastapi import UploadFile

from src.shared.config import settings
from src.shared.logging import get_logger

logger = get_logger(__name__)


class LocalFileStorage:
    """本地文件存储服务 - 基于SHA256去重存储"""
    
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            base_dir = settings.storage_data_dir
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录结构
        self.uploads_dir = self.base_dir / "uploads"
        self.temp_dir = self.base_dir / "temp"
        self.uploads_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        logger.info(f"LocalFileStorage initialized: {self.base_dir}")
    
    def save_file_by_hash(self, file_content: bytes, file_hash: str, file_extension: str = "") -> Tuple[str, Path]:
        """
        基于哈希值保存文件（去重存储）
        
        Args:
            file_content: 文件内容
            file_hash: 文件SHA256哈希
            file_extension: 文件扩展名
            
        Returns:
            (relative_path, full_path): 相对路径和绝对路径
        """
        # 使用哈希值的前两位作为子目录（分散存储）
        sub_dir = file_hash[:2]
        storage_dir = self.uploads_dir / sub_dir
        storage_dir.mkdir(exist_ok=True)
        
        # 文件名: 哈希值 + 扩展名
        filename = f"{file_hash}{file_extension}"
        full_path = storage_dir / filename
        relative_path = str(full_path.relative_to(self.base_dir))
        
        # 如果文件已存在，直接返回路径（去重）
        if full_path.exists():
            logger.info(f"File already exists (deduplication): {relative_path}")
            return relative_path, full_path
        
        # 保存文件
        try:
            with open(full_path, "wb") as f:
                f.write(file_content)
            logger.info(f"File saved: {relative_path}")
            return relative_path, full_path
        except Exception as e:
            logger.error(f"Failed to save file {relative_path}: {e}")
            raise
    
    def save_upload_file(self, upload_file: UploadFile) -> Tuple[str, bytes, str]:
        """
        保存上传文件并返回相关信息
        
        Args:
            upload_file: FastAPI UploadFile对象
            
        Returns:
            (relative_path, file_content, file_hash): 相对路径、文件内容、哈希值
        """
        # 读取文件内容
        upload_file.file.seek(0)
        file_content = upload_file.file.read()
        upload_file.file.seek(0)  # 重置指针
        
        # 计算哈希值
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # 获取文件扩展名
        file_extension = ""
        if upload_file.filename and "." in upload_file.filename:
            file_extension = "." + upload_file.filename.split(".")[-1].lower()
        
        # 保存文件
        relative_path, _ = self.save_file_by_hash(file_content, file_hash, file_extension)
        
        return relative_path, file_content, file_hash
    
    def save_temporary_file(self, file_content: bytes, user_id: int, original_filename: str) -> Tuple[str, Path]:
        """
        保存临时文件
        
        Args:
            file_content: 文件内容
            user_id: 用户ID
            original_filename: 原始文件名
            
        Returns:
            (relative_path, full_path): 相对路径和绝对路径
        """
        # 创建用户临时目录
        user_temp_dir = self.temp_dir / f"user_{user_id}"
        user_temp_dir.mkdir(exist_ok=True)
        
        # 生成唯一文件名: 时间戳 + 原始文件名
        import uuid
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"{timestamp}_{unique_id}_{original_filename}"
        
        full_path = user_temp_dir / filename
        relative_path = str(full_path.relative_to(self.base_dir))
        
        # 保存文件
        try:
            with open(full_path, "wb") as f:
                f.write(file_content)
            logger.info(f"Temporary file saved: {relative_path}")
            return relative_path, full_path
        except Exception as e:
            logger.error(f"Failed to save temporary file {relative_path}: {e}")
            raise
    
    def read_file(self, relative_path: str) -> Optional[bytes]:
        """
        读取文件内容
        
        Args:
            relative_path: 文件相对路径
            
        Returns:
            文件内容字节，如果文件不存在返回None
        """
        full_path = self.base_dir / relative_path
        
        if not full_path.exists():
            logger.warning(f"File not found: {relative_path}")
            return None
        
        try:
            with open(full_path, "rb") as f:
                content = f.read()
            logger.debug(f"File read: {relative_path} ({len(content)} bytes)")
            return content
        except Exception as e:
            logger.error(f"Failed to read file {relative_path}: {e}")
            return None
    
    def delete_file(self, relative_path: str) -> bool:
        """
        删除文件
        
        Args:
            relative_path: 文件相对路径
            
        Returns:
            是否删除成功
        """
        full_path = self.base_dir / relative_path
        
        if not full_path.exists():
            logger.warning(f"File not found for deletion: {relative_path}")
            return True  # 文件不存在也算删除成功
        
        try:
            full_path.unlink()
            logger.info(f"File deleted: {relative_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {relative_path}: {e}")
            return False
    
    def file_exists(self, relative_path: str) -> bool:
        """检查文件是否存在"""
        full_path = self.base_dir / relative_path
        return full_path.exists()
    
    def get_file_size(self, relative_path: str) -> Optional[int]:
        """获取文件大小"""
        full_path = self.base_dir / relative_path
        if full_path.exists():
            return full_path.stat().st_size
        return None
    
    def cleanup_empty_directories(self):
        """清理空目录"""
        try:
            for root, dirs, files in os.walk(self.base_dir, topdown=False):
                for dir_name in dirs:
                    dir_path = Path(root) / dir_name
                    try:
                        if not any(dir_path.iterdir()):  # 目录为空
                            dir_path.rmdir()
                            logger.info(f"Empty directory removed: {dir_path}")
                    except OSError:
                        pass  # 目录不为空或其他错误，忽略
        except Exception as e:
            logger.error(f"Failed to cleanup empty directories: {e}")


# 全局文件存储实例
_file_storage = None

def get_file_storage() -> LocalFileStorage:
    """获取文件存储实例（单例模式）"""
    global _file_storage
    if _file_storage is None:
        _file_storage = LocalFileStorage()
    return _file_storage