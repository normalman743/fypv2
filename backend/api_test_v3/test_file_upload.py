#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件上传和管理测试
使用前请先: source venv/bin/activate
运行: python api_test_v3/test_file_upload.py
"""

import sys
import os
import tempfile
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import APIClient, print_response, extract_token_from_response
from config import test_config
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_user_token(user_type="user"):
    """获取用户token"""
    client = APIClient()
    user_data = test_config.default_users[user_type]
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    
    if login_response.status_code == 200:
        token = extract_token_from_response(login_response)
        if token:
            return token
    return None

def create_test_file(content="这是一个测试文件", filename="test.txt"):
    """创建测试文件"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=filename)
    temp_file.write(content)
    temp_file.close()
    return temp_file.name

def test_folder_management():
    """测试文件夹管理"""
    print("📁 文件夹管理测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return None
    
    client.set_auth_token(user_token)
    
    # 1. 获取所有文件夹
    print("\n1️⃣ 获取所有文件夹")
    folders_response = client.get("/api/v1/folders")
    print_response(folders_response, "获取文件夹列表")
    
    # 2. 创建新文件夹
    print("\n2️⃣ 创建新文件夹")
    folder_data = {
        "name": "测试文件夹",
        "description": "用于测试的文件夹",
        "scope": "personal"
    }
    
    create_folder_response = client.post("/api/v1/folders", json=folder_data)
    print_response(create_folder_response, "创建文件夹")
    
    folder_id = None
    if create_folder_response.status_code == 200:
        result = create_folder_response.json()
        if result.get("success"):
            folder_id = result["data"]["id"]
            print(f"✅ 创建文件夹成功，ID: {folder_id}")
    
    # 3. 获取特定文件夹信息
    if folder_id:
        print(f"\n3️⃣ 获取文件夹信息 (ID: {folder_id})")
        folder_detail_response = client.get(f"/api/v1/folders/{folder_id}")
        print_response(folder_detail_response, "文件夹详情")
    
    # 4. 更新文件夹信息
    if folder_id:
        print(f"\n4️⃣ 更新文件夹信息")
        update_data = {
            "name": "测试文件夹（更新）",
            "description": "更新后的文件夹描述"
        }
        update_response = client.put(f"/api/v1/folders/{folder_id}", json=update_data)
        print_response(update_response, "更新文件夹")
    
    return folder_id

def test_file_upload():
    """测试文件上传"""
    print("\n📄 文件上传测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return None
    
    client.set_auth_token(user_token)
    
    # 创建测试文件夹
    folder_id = test_folder_management()
    
    # 1. 创建测试文件
    test_file_path = create_test_file("这是一个测试文档内容\n用于测试文件上传功能", "test_document.txt")
    
    try:
        # 2. 上传文件
        print("\n1️⃣ 上传文件")
        upload_data = {
            "scope": "personal",
            "folder_id": folder_id
        }
        
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_document.txt', f, 'text/plain')}
            upload_response = client.post("/api/v1/files/upload", data=upload_data, files=files)
        
        print_response(upload_response, "文件上传")
        
        file_id = None
        if upload_response.status_code == 200:
            result = upload_response.json()
            if result.get("success"):
                file_id = result["data"]["id"]
                print(f"✅ 文件上传成功，ID: {file_id}")
        
        # 3. 获取文件信息
        if file_id:
            print(f"\n2️⃣ 获取文件信息 (ID: {file_id})")
            file_detail_response = client.get(f"/api/v1/files/{file_id}")
            print_response(file_detail_response, "文件详情")
        
        # 4. 获取文件夹下的文件列表
        if folder_id:
            print(f"\n3️⃣ 获取文件夹下的文件")
            folder_files_response = client.get(f"/api/v1/folders/{folder_id}/files")
            print_response(folder_files_response, "文件夹文件列表")
        
        # 5. 下载文件
        if file_id:
            print(f"\n4️⃣ 下载文件")
            download_response = client.get(f"/api/v1/files/{file_id}/download")
            print(f"下载状态码: {download_response.status_code}")
            if download_response.status_code == 200:
                print(f"✅ 文件下载成功，大小: {len(download_response.content)} 字节")
                print(f"文件内容预览: {download_response.content[:50]}...")
            else:
                print(f"❌ 文件下载失败")
        
        # 6. 更新文件信息
        if file_id:
            print(f"\n5️⃣ 更新文件信息")
            update_data = {
                "name": "更新后的文件名.txt",
                "description": "更新后的文件描述"
            }
            update_response = client.put(f"/api/v1/files/{file_id}", json=update_data)
            print_response(update_response, "更新文件")
        
        # 7. 文件预览
        if file_id:
            print(f"\n6️⃣ 文件预览")
            preview_response = client.get(f"/api/v1/files/{file_id}/preview")
            print_response(preview_response, "文件预览")
        
        # 8. 文件状态查询
        if file_id:
            print(f"\n7️⃣ 文件状态查询")
            status_response = client.get(f"/api/v1/files/{file_id}/status")
            print_response(status_response, "文件状态")
        
        # 9. 文件访问日志
        if file_id:
            print(f"\n8️⃣ 文件访问日志")
            access_logs_response = client.get(f"/api/v1/files/{file_id}/access-logs")
            print_response(access_logs_response, "文件访问日志")
        
        return file_id
        
    finally:
        # 清理临时文件
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)

def test_file_management():
    """测试文件管理功能"""
    print("\n🗂️ 文件管理测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 1. 获取所有文件
    print("\n1️⃣ 获取所有文件")
    files_response = client.get("/api/v1/files")
    print_response(files_response, "获取文件列表")
    
    # 2. 按条件搜索文件
    print("\n2️⃣ 搜索文件")
    search_response = client.get("/api/v1/files", params={"search": "test"})
    print_response(search_response, "搜索文件")
    
    # 3. 按文件类型筛选
    print("\n3️⃣ 按类型筛选文件")
    filter_response = client.get("/api/v1/files", params={"file_type": "txt"})
    print_response(filter_response, "筛选文件")

def test_global_files():
    """测试全局文件管理"""
    print("\n🌍 全局文件管理测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 1. 获取全局文件列表
    print(f"\n1️⃣ 获取全局文件列表")
    global_files_response = client.get("/api/v1/global-files")
    print_response(global_files_response, "全局文件列表")
    
    # 2. 上传全局文件
    print(f"\n2️⃣ 上传全局文件")
    test_file_path = create_test_file("这是一个全局文件内容\n用于测试全局文件上传功能", "global_test.txt")
    
    try:
        upload_data = {
            "scope": "global"
        }
        
        with open(test_file_path, 'rb') as f:
            files = {'file': ('global_test.txt', f, 'text/plain')}
            upload_response = client.post("/api/v1/global-files/upload", data=upload_data, files=files)
        
        print_response(upload_response, "全局文件上传")
        
        global_file_id = None
        if upload_response.status_code == 200:
            result = upload_response.json()
            if result.get("success"):
                global_file_id = result["data"]["id"]
                print(f"✅ 全局文件上传成功，ID: {global_file_id}")
        
        # 3. 删除全局文件
        if global_file_id:
            print(f"\n3️⃣ 删除全局文件")
            delete_response = client.delete(f"/api/v1/global-files/{global_file_id}")
            print_response(delete_response, "删除全局文件")
        
    finally:
        # 清理临时文件
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)

def test_file_sharing():
    """测试文件分享功能"""
    print("\n🔗 文件分享测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 先上传一个文件
    file_id = test_file_upload()
    
    if file_id:
        # 1. 创建分享链接
        print(f"\n1️⃣ 创建分享链接")
        share_data = {
            "expires_in_days": 7,
            "allow_download": True
        }
        share_response = client.post(f"/api/v1/files/{file_id}/share", json=share_data)
        print_response(share_response, "创建分享")
        
        # 2. 获取文件的分享列表
        print(f"\n2️⃣ 获取文件分享列表")
        shares_response = client.get(f"/api/v1/files/{file_id}/shares")
        print_response(shares_response, "文件分享列表")

if __name__ == "__main__":
    print("⚠️  请确保已执行: source venv/bin/activate")
    print("⚠️  请确保服务正在运行: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    input("按回车键继续...")
    
    try:
        test_folder_management()
        test_file_upload()
        test_file_management()
        test_global_files()
        test_file_sharing()
        print(f"\n🎉 文件上传和管理测试完成！")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()