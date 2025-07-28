#!/usr/bin/env python3
"""
本地文件存储服务
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile


class LocalFileStorage:
    """本地文件存储服务"""
    
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.getenv("UPLOAD_DIR", "./storage/uploads")
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def upload_file(self, file: UploadFile, course_id: int, folder_id: int) -> Tuple[str, str]:
        """
        上传文件到本地存储
        
        Args:
            file: 上传的文件
            course_id: 课程ID
            folder_id: 文件夹ID
            
        Returns:
            (file_path, local_path): 相对路径和绝对路径
        """
        # 生成唯一文件名
        file_extension = ""
        if file.filename and "." in file.filename:
            file_extension = file.filename.split(".")[-1]
        
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}" if file_extension else str(uuid.uuid4().hex)
        
        # 创建目录结构: storage/uploads/course_{course_id}/folder_{folder_id}/
        course_dir = self.base_dir / f"course_{course_id}"
        folder_dir = course_dir / f"folder_{folder_id}"
        folder_dir.mkdir(parents=True, exist_ok=True)
        
        # 完整文件路径
        full_path = folder_dir / unique_filename
        relative_path = str(full_path.relative_to(self.base_dir))
        
        # 保存文件
        file.file.seek(0)  # 重置文件指针
        with open(full_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"📁 File saved locally: {full_path}")
        return relative_path, str(full_path)
    
    def download_file(self, file_path: str) -> Optional[bytes]:
        """
        从本地存储下载文件
        
        Args:
            file_path: 文件相对路径
            
        Returns:
            文件内容字节
        """
        full_path = self.base_dir / file_path
        
        if not full_path.exists():
            print(f"❌ File not found: {full_path}")
            return None
        
        try:
            with open(full_path, "rb") as f:
                return f.read()
        except Exception as e:
            print(f"❌ Failed to read file {full_path}: {e}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """
        删除本地文件
        
        Args:
            file_path: 文件相对路径
            
        Returns:
            是否删除成功
        """
        full_path = self.base_dir / file_path
        
        if not full_path.exists():
            print(f"⚠️ File not found for deletion: {full_path}")
            return True  # 文件不存在也算删除成功
        
        try:
            full_path.unlink()
            print(f"🗑️ File deleted: {full_path}")
            
            # 尝试删除空的父目录
            try:
                full_path.parent.rmdir()  # 只删除空目录
                print(f"🗑️ Empty directory removed: {full_path.parent}")
            except OSError:
                pass  # 目录不为空，忽略
            
            return True
        except Exception as e:
            print(f"❌ Failed to delete file {full_path}: {e}")
            return False
    
    def get_file_path(self, file_path: str) -> Path:
        """
        获取文件的完整路径
        
        Args:
            file_path: 文件相对路径
            
        Returns:
            文件完整路径
        """
        return self.base_dir / file_path
    
    def file_exists(self, file_path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 文件相对路径
            
        Returns:
            文件是否存在
        """
        return (self.base_dir / file_path).exists()


# 全局本地存储实例
local_file_storage = LocalFileStorage()