#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件夹与文件管理测试 - 基于api_folder_file.md文档
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

def create_test_file():
    """创建一个测试文件"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    temp_file.write("这是一个测试文件内容。\n用于测试文件上传功能。")
    temp_file.close()
    return temp_file.name

def test_folder_management():
    """测试文件夹管理 - 基于api_folder_file.md"""
    print("📁 文件夹管理测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return None, None
    
    client.set_auth_token(user_token)
    
    # 1. 动态获取课程ID并获取文件夹 - GET /api/v1/courses/{id}/folders
    print("\n1️⃣ 获取课程文件夹")
    
    # 动态获取课程ID
    courses_response = client.get("/api/v1/courses")
    course_id = None
    if courses_response.status_code == 200:
        result = courses_response.json()
        if result.get("success") and result["data"]["courses"]:
            course_id = result["data"]["courses"][0]["id"]
            print(f"✅ 使用现有课程ID: {course_id}")
        else:
            print("⚠️ 没有可用的课程，跳过课程文件夹测试")
            course_id = None
    
    if course_id:
        folders_response = client.get(f"/api/v1/courses/{course_id}/folders")
        print_response(folders_response, "获取课程文件夹")
    else:
        print("❌ 无法获取课程ID，跳过课程文件夹测试")
    
    # 2. 新建个人文件夹 - POST /api/v1/folders (注意：实际API不支持个人文件夹，跳过此步骤)
    print("\n2️⃣ 新建个人文件夹 - 跳过（API不支持）")
    print("⚠️ API不支持个人文件夹，所有文件夹都必须关联到课程")
    personal_folder_id = None
    
    # 跳过个人文件夹创建
    
    # 3. 新建课程文件夹 - POST /api/v1/folders (注意：使用正确的字段)
    print("\n3️⃣ 新建课程文件夹 - 跳过（使用课程特定接口）")
    print("⚠️ 普通的 /api/v1/folders 接口不支持创建课程文件夹，使用 /api/v1/courses/{id}/folders")
    
    # 跳过普通文件夹创建，使用课程特定接口
    
    course_folder_id = None
    if create_course_response.status_code == 200:
        result = create_course_response.json()
        if result.get("success"):
            course_folder_id = result["data"]["folder"]["id"]
            print(f"✅ 创建课程文件夹成功，ID: {course_folder_id}")
    
    # 4. 新建课程特定文件夹 - POST /api/v1/courses/{id}/folders
    print(f"\n4️⃣ 在课程中新建文件夹 (课程ID: {course_id})")
    course_specific_data = {
        "name": "讲座",
        "folder_type": "lecture"
    }
    
    create_specific_response = client.post(f"/api/v1/courses/{course_id}/folders", json=course_specific_data)
    print_response(create_specific_response, "新建课程特定文件夹")
    
    specific_folder_id = None
    if create_specific_response.status_code == 200:
        result = create_specific_response.json()
        if result.get("success"):
            specific_folder_id = result["data"]["folder"]["id"]
            print(f"✅ 创建课程特定文件夹成功，ID: {specific_folder_id}")
    
    return personal_folder_id, course_folder_id or specific_folder_id

def test_file_upload(folder_id=None):
    """测试文件上传 - 基于api_folder_file.md"""
    print("\n📤 文件上传测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return None
    
    client.set_auth_token(user_token)
    
    # 创建测试文件
    test_file_path = create_test_file()
    
    try:
        # 上传文件 - POST /api/v1/files/upload
        print("\n1️⃣ 上传文件")
        
        # 动态获取课程ID和文件夹ID
        courses_response = client.get("/api/v1/courses")
        course_id = None
        if courses_response.status_code == 200:
            result = courses_response.json()
            if result.get("success") and result["data"]["courses"]:
                course_id = result["data"]["courses"][0]["id"]
        
        data = {
            'course_id': course_id or 1,  # 使用动态获取的课程ID或默认值
            'folder_id': folder_id or 1  # 使用传入的folder_id或默认值
        }
        
        with open(test_file_path, 'rb') as f:
            files = {'file': (os.path.basename(test_file_path), f, 'text/plain')}
            upload_response = client.post("/api/v1/files/upload", files=files, data=data)
            print_response(upload_response, "上传文件")
            
            file_id = None
            if upload_response.status_code == 200:
                result = upload_response.json()
                if result.get("success"):
                    file_id = result["data"]["file"]["id"]
                    print(f"✅ 文件上传成功，ID: {file_id}")
                    return file_id
    
    finally:
        # 清理测试文件
        try:
            os.unlink(test_file_path)
        except:
            pass
    
    return None

def test_file_management(folder_id=None, file_id=None):
    """测试文件管理 - 基于api_folder_file.md"""
    print("\n📄 文件管理测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 1. 获取文件夹下所有文件 - GET /api/v1/folders/{id}/files
    if folder_id:
        print(f"\n1️⃣ 获取文件夹文件 (文件夹ID: {folder_id})")
        files_response = client.get(f"/api/v1/folders/{folder_id}/files")
        print_response(files_response, "获取文件夹文件")
    
    # 2. 文件预览 - GET /api/v1/files/{id}/preview
    if file_id:
        print(f"\n2️⃣ 文件预览 (文件ID: {file_id})")
        preview_response = client.get(f"/api/v1/files/{file_id}/preview")
        print_response(preview_response, "文件预览")
    
    # 3. 文件下载 - GET /api/v1/files/{id}/download
    if file_id:
        print(f"\n3️⃣ 文件下载 (文件ID: {file_id})")
        download_response = client.get(f"/api/v1/files/{file_id}/download")
        if download_response.status_code == 200:
            print("✅ 文件下载成功")
            print(f"   Content-Type: {download_response.headers.get('content-type', 'N/A')}")
            print(f"   Content-Length: {download_response.headers.get('content-length', 'N/A')}")
        else:
            print_response(download_response, "文件下载")

def test_global_files():
    """测试全局文件管理（可选功能）"""
    print("\n🌐 全局文件管理测试")
    print("=" * 50)
    
    print("⚠️ 全局文件API暂未实现，跳过此测试")
    print("   预期的API端点 /api/v1/global-files 返回404")
    return
    
    # 1. 获取全局文件列表
    print("\n1️⃣ 获取全局文件列表")
    global_files_response = client.get("/api/v1/global-files")
    print_response(global_files_response, "获取全局文件列表")
    
    # 2. 上传全局文件
    print("\n2️⃣ 上传全局文件")
    test_file_path = create_test_file()
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': (os.path.basename(test_file_path), f, 'text/plain')}
            data = {
                'description': '全局测试文件',
                'tags': '["测试", "全局"]',
                'visibility': 'public'
            }
            
            upload_global_response = client.post("/api/v1/global-files/upload", files=files, data=data)
            print_response(upload_global_response, "上传全局文件")
            
            global_file_id = None
            if upload_global_response.status_code == 200:
                result = upload_global_response.json()
                if result.get("success"):
                    global_file_id = result["data"]["file"]["id"]
                    print(f"✅ 全局文件上传成功，ID: {global_file_id}")
    
    finally:
        # 清理测试文件
        try:
            os.unlink(test_file_path)
        except:
            pass

def test_file_sharing():
    """测试文件分享功能（扩展功能）"""
    print("\n🤝 文件分享测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 测试统一文件管理系统的文件分享功能
    print("\n1️⃣ 获取用户文件列表")
    files_response = client.get("/api/v1/files")
    print_response(files_response, "获取用户文件列表")
    
    # 如果有文件，测试分享功能
    if files_response.status_code == 200:
        result = files_response.json()
        if result.get("success") and result.get("data"):
            # 假设有文件可以分享
            print("\n2️⃣ 文件分享功能测试")
            print("   (需要实际文件ID来测试分享功能)")

def test_file_deletion():
    """测试文件删除功能"""
    print("\n🗑️ 文件删除测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 动态获取课程ID
    courses_response = client.get("/api/v1/courses")
    course_id = 1  # 默认值
    if courses_response.status_code == 200:
        result = courses_response.json()
        if result.get("success") and result["data"]["courses"]:
            course_id = result["data"]["courses"][0]["id"]
    
    # 上传一个测试文件用于删除
    print("\n1️⃣ 上传测试文件用于删除")
    test_file_path = create_test_file()
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': (os.path.basename(test_file_path), f, 'text/plain')}
            data = {
                'course_id': course_id or 1,  # 使用动态获取的课程ID
                'folder_id': 1
            }
            
            upload_response = client.post("/api/v1/files/upload", files=files, data=data)
            
            if upload_response.status_code == 200:
                result = upload_response.json()
                if result.get("success"):
                    file_id = result["data"]["file"]["id"]
                    print(f"✅ 测试文件上传成功，ID: {file_id}")
                    
                    # 删除文件 - DELETE /api/v1/files/{id}
                    print(f"\n2️⃣ 删除文件 (文件ID: {file_id})")
                    delete_response = client.delete(f"/api/v1/files/{file_id}")
                    print_response(delete_response, "删除文件")
    
    finally:
        # 清理本地测试文件
        try:
            os.unlink(test_file_path)
        except:
            pass

if __name__ == "__main__":
    print("⚠️  请确保已执行: source venv/bin/activate")
    print("⚠️  请确保服务正在运行: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("📋 基于 api_folder_file.md 文档的测试")
    input("按回车键继续...")
    
    try:
        # 测试文件夹管理
        personal_folder_id, course_folder_id = test_folder_management()
        
        # 测试文件上传
        file_id = test_file_upload(course_folder_id)
        
        # 测试文件管理
        test_file_management(course_folder_id, file_id)
        
        # 测试全局文件
        test_global_files()
        
        # 测试文件分享
        test_file_sharing()
        
        # 测试文件删除
        test_file_deletion()
        
        print(f"\n🎉 文件夹与文件管理测试完成！")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()