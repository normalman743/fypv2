import os
import uuid
import hashlib
from typing import Optional, Tuple
from pathlib import Path
import tempfile
import shutil
from fastapi import UploadFile

class MockCloudStorageService:
    """Mock云存储服务，用于测试"""
    
    def __init__(self, storage_dir: str = "mock_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        print(f"📁 Mock云存储初始化在: {self.storage_dir.absolute()}")
    
    def upload_file(self, file: UploadFile, course_id: int, folder_id: int) -> Tuple[str, str]:
        """
        上传文件到mock云存储
        
        Returns:
            Tuple[str, str]: (cloud_url, file_path)
        """
        # 生成唯一的文件名
        file_extension = Path(file.filename).suffix if file.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # 创建目录结构: mock_storage/course_{course_id}/folder_{folder_id}/
        course_dir = self.storage_dir / f"course_{course_id}"
        folder_dir = course_dir / f"folder_{folder_id}"
        folder_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        file_path = folder_dir / unique_filename
        
        # 读取并保存文件内容
        file_content = file.file.read()
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # 重置文件指针
        file.file.seek(0)
        
        # 生成云存储URL（mock）
        cloud_url = f"mock://storage/course_{course_id}/folder_{folder_id}/{unique_filename}"
        
        print(f"📤 文件上传成功: {file.filename} -> {cloud_url}")
        print(f"📍 本地路径: {file_path}")
        
        return cloud_url, str(file_path)
    
    def download_file(self, cloud_url: str) -> Optional[bytes]:
        """
        从mock云存储下载文件
        
        Returns:
            Optional[bytes]: 文件内容
        """
        try:
            # 解析mock URL: mock://storage/course_1/folder_2/filename.pdf
            if not cloud_url.startswith("mock://storage/"):
                print(f"❌ 无效的mock URL: {cloud_url}")
                return None
            
            # 提取相对路径
            relative_path = cloud_url.replace("mock://storage/", "")
            file_path = self.storage_dir / relative_path
            
            if not file_path.exists():
                print(f"❌ 文件不存在: {file_path}")
                return None
            
            # 读取文件内容
            with open(file_path, "rb") as f:
                content = f.read()
            
            print(f"📥 文件下载成功: {cloud_url} -> {len(content)} bytes")
            return content
            
        except Exception as e:
            print(f"❌ 文件下载失败: {e}")
            return None
    
    def delete_file(self, cloud_url: str) -> bool:
        """
        从mock云存储删除文件
        
        Returns:
            bool: 是否删除成功
        """
        try:
            if not cloud_url.startswith("mock://storage/"):
                return False
            
            relative_path = cloud_url.replace("mock://storage/", "")
            file_path = self.storage_dir / relative_path
            
            if file_path.exists():
                file_path.unlink()
                print(f"🗑️ 文件删除成功: {cloud_url}")
                return True
            else:
                print(f"⚠️ 文件不存在，无法删除: {cloud_url}")
                return False
                
        except Exception as e:
            print(f"❌ 文件删除失败: {e}")
            return False
    
    def get_file_info(self, cloud_url: str) -> Optional[dict]:
        """
        获取文件信息
        
        Returns:
            Optional[dict]: 文件信息
        """
        try:
            if not cloud_url.startswith("mock://storage/"):
                return None
            
            relative_path = cloud_url.replace("mock://storage/", "")
            file_path = self.storage_dir / relative_path
            
            if not file_path.exists():
                return None
            
            stat = file_path.stat()
            return {
                "size": stat.st_size,
                "created_at": stat.st_ctime,
                "modified_at": stat.st_mtime,
                "path": str(file_path)
            }
            
        except Exception as e:
            print(f"❌ 获取文件信息失败: {e}")
            return None

# 全局实例
mock_cloud_storage = MockCloudStorageService() 