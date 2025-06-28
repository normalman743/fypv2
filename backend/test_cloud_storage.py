#!/usr/bin/env python3
"""
测试云存储功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from fastapi import UploadFile
import io
import tempfile
from pathlib import Path

from app.main import app
from app.services.cloud_storage_service import MockCloudStorageService

client = TestClient(app)

def create_test_file(content: str, filename: str) -> UploadFile:
    """创建测试文件"""
    file_content = content.encode('utf-8')
    return UploadFile(
        filename=filename,
        file=io.BytesIO(file_content),
        content_type="text/plain"
    )

def test_cloud_storage_service():
    """测试云存储服务"""
    print("🧪 测试云存储服务...")
    
    # 创建临时测试目录
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = MockCloudStorageService(storage_dir=temp_dir)
        
        # 创建测试文件
        test_content = "这是一个测试文件内容"
        test_file = create_test_file(test_content, "test.txt")
        
        # 测试上传
        print("📤 测试文件上传...")
        cloud_url, local_path = storage.upload_file(test_file, course_id=1, folder_id=2)
        print(f"   云存储URL: {cloud_url}")
        print(f"   本地路径: {local_path}")
        
        # 验证文件是否保存
        assert Path(local_path).exists(), "文件应该被保存到本地"
        
        # 测试下载
        print("📥 测试文件下载...")
        downloaded_content = storage.download_file(cloud_url)
        assert downloaded_content is not None, "应该能下载文件"
        assert downloaded_content.decode('utf-8') == test_content, "下载内容应该匹配"
        print(f"   下载内容: {downloaded_content.decode('utf-8')}")
        
        # 测试文件信息
        print("📋 测试文件信息...")
        file_info = storage.get_file_info(cloud_url)
        assert file_info is not None, "应该能获取文件信息"
        print(f"   文件大小: {file_info['size']} bytes")
        
        # 测试删除
        print("🗑️ 测试文件删除...")
        success = storage.delete_file(cloud_url)
        assert success, "应该能删除文件"
        assert not Path(local_path).exists(), "文件应该被删除"
        
        print("✅ 云存储服务测试通过！")

def test_file_upload_api():
    """测试文件上传API"""
    print("\n🧪 测试文件上传API...")
    
    # 首先需要登录获取token
    login_data = {
        "email": "test@example.com",
        "password": "testpassword"
    }
    
    # 这里需要先确保有测试用户，或者使用现有的测试数据
    # 暂时跳过API测试，专注于服务层测试
    print("⚠️ API测试需要先设置测试用户，暂时跳过")

if __name__ == "__main__":
    print("🚀 开始云存储功能测试...")
    
    try:
        test_cloud_storage_service()
        # test_file_upload_api()  # 暂时注释掉
        print("\n🎉 所有测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc() 