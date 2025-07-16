#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨模块删除操作测试 - 整合所有API文档中的删除功能
使用前请先: source venv/bin/activate
运行: python api_test_v3/test_delete_operations.py
"""

import sys
import os
import tempfile
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import APIClient, print_response, extract_token_from_response
from config import test_config
import logging
from datetime import datetime, timedelta

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

def get_admin_token():
    """获取管理员token"""
    return get_user_token("admin")

def create_test_file(content="测试文件内容", filename="test.txt"):
    """创建测试文件"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=filename)
    temp_file.write(content)
    temp_file.close()
    return temp_file.name

def test_message_deletion():
    """测试消息删除 - 基于api_chat_message_rag.md"""
    print("💬 消息删除测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 1. 创建测试聊天
    print("\n1️⃣ 创建测试聊天")
    chat_data = {
        "chat_type": "general",
        "first_message": "这是一个用于删除测试的消息",
        "course_id": None,
        "custom_prompt": None,
        "file_ids": []
    }
    
    chat_response = client.post("/api/v1/chats", json=chat_data)
    print_response(chat_response, "创建测试聊天")
    
    chat_id = None
    if chat_response.status_code == 200:
        result = chat_response.json()
        if result.get("success"):
            chat_id = result["data"]["chat"]["id"]
            print(f"✅ 创建测试聊天成功，ID: {chat_id}")
    
    # 2. 发送额外消息用于删除
    if chat_id:
        print(f"\n2️⃣ 发送额外消息 (Chat ID: {chat_id})")
        message_data = {
            "content": "这条消息将被删除",
            "file_ids": []
        }
        
        message_response = client.post(f"/api/v1/chats/{chat_id}/messages", json=message_data)
        print_response(message_response, "发送消息")
        
        message_id = None
        if message_response.status_code == 200:
            result = message_response.json()
            if result.get("success"):
                message_id = result["data"]["user_message"]["id"]
                print(f"✅ 发送消息成功，ID: {message_id}")
                
                # 3. 删除消息 - DELETE /api/v1/messages/{id}
                print(f"\n3️⃣ 删除消息 (Message ID: {message_id})")
                delete_response = client.delete(f"/api/v1/messages/{message_id}")
                print_response(delete_response, "删除消息")
    
    return chat_id

def test_chat_deletion(chat_id=None):
    """测试聊天删除 - 基于api_chat_message_rag.md"""
    print("\n💬 聊天删除测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 如果没有提供chat_id，创建一个新的
    if not chat_id:
        print("\n1️⃣ 创建临时聊天用于删除")
        chat_data = {
            "chat_type": "general",
            "first_message": "临时聊天，即将删除",
            "course_id": None,
            "custom_prompt": None,
            "file_ids": []
        }
        
        chat_response = client.post("/api/v1/chats", json=chat_data)
        if chat_response.status_code == 200:
            result = chat_response.json()
            if result.get("success"):
                chat_id = result["data"]["chat"]["id"]
                print(f"✅ 创建临时聊天成功，ID: {chat_id}")
    
    # 删除聊天 - DELETE /api/v1/chats/{id}
    if chat_id:
        print(f"\n2️⃣ 删除聊天 (Chat ID: {chat_id})")
        delete_response = client.delete(f"/api/v1/chats/{chat_id}")
        print_response(delete_response, "删除聊天")

def test_file_deletion():
    """测试文件删除 - 基于api_folder_file.md"""
    print("\n📄 文件删除测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 1. 上传测试文件
    print("\n1️⃣ 上传测试文件")
    test_file_path = create_test_file("测试文件内容 - 用于删除", "delete_test.txt")
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': (os.path.basename(test_file_path), f, 'text/plain')}
            # 动态获取课程ID
            courses_response = client.get("/api/v1/courses")
            course_id = 1  # 默认值
            if courses_response.status_code == 200:
                result = courses_response.json()
                if result.get("success") and result["data"]["courses"]:
                    course_id = result["data"]["courses"][0]["id"]
            
            data = {
                'course_id': course_id,
                'folder_id': 1
            }
            
            upload_response = client.post("/api/v1/files/upload", files=files, data=data)
            print_response(upload_response, "上传测试文件")
            
            if upload_response.status_code == 200:
                result = upload_response.json()
                if result.get("success"):
                    file_id = result["data"]["file"]["id"]
                    print(f"✅ 上传文件成功，ID: {file_id}")
                    
                    # 2. 删除文件 - DELETE /api/v1/files/{id}
                    print(f"\n2️⃣ 删除文件 (File ID: {file_id})")
                    delete_response = client.delete(f"/api/v1/files/{file_id}")
                    print_response(delete_response, "删除文件")
    
    finally:
        # 清理本地测试文件
        try:
            os.unlink(test_file_path)
        except:
            pass

def test_invite_code_deletion():
    """测试邀请码删除 - 基于api_admin.md"""
    print("\n🎫 邀请码删除测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取管理员权限
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ 无法获取管理员token，跳过测试")
        return
    
    client.set_auth_token(admin_token)
    
    # 1. 创建测试邀请码
    print("\n1️⃣ 创建测试邀请码")
    future_date = datetime.now() + timedelta(days=7)
    create_data = {
        "description": "用于删除测试的邀请码",
        "expires_at": future_date.isoformat() + "Z"
    }
    
    create_response = client.post("/api/v1/invite-codes", json=create_data)
    print_response(create_response, "创建测试邀请码")
    
    if create_response.status_code == 200:
        result = create_response.json()
        if result.get("success"):
            invite_code_id = result["data"]["invite_code"]["id"]
            print(f"✅ 创建邀请码成功，ID: {invite_code_id}")
            
            # 2. 删除邀请码 - DELETE /api/v1/invite-codes/{id}
            print(f"\n2️⃣ 删除邀请码 (ID: {invite_code_id})")
            delete_response = client.delete(f"/api/v1/invite-codes/{invite_code_id}")
            print_response(delete_response, "删除邀请码")

def test_course_deletion():
    """测试课程删除 - 基于api_semester_course.md"""
    print("\n📚 课程删除测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取管理员权限
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ 无法获取管理员token，跳过测试")
        return
    
    client.set_auth_token(admin_token)
    
    # 1. 创建测试课程
    print("\n1️⃣ 创建测试课程")
    create_data = {
        "name": "待删除测试课程",
        "code": "DEL101",
        "description": "这个课程将被删除",
        "semester_id": 1  # 默认使用第一个学期
    }
    
    create_response = client.post("/api/v1/courses", json=create_data)
    print_response(create_response, "创建测试课程")
    
    if create_response.status_code == 200:
        result = create_response.json()
        if result.get("success"):
            course_id = result["data"]["course"]["id"]
            print(f"✅ 创建课程成功，ID: {course_id}")
            
            # 2. 删除课程 - DELETE /api/v1/courses/{id}
            print(f"\n2️⃣ 删除课程 (ID: {course_id})")
            delete_response = client.delete(f"/api/v1/courses/{course_id}")
            print_response(delete_response, "删除课程")

def test_semester_deletion():
    """测试学期删除 - 基于api_semester_course.md"""
    print("\n📅 学期删除测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取管理员权限
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ 无法获取管理员token，跳过测试")
        return
    
    client.set_auth_token(admin_token)
    
    # 1. 创建测试学期
    print("\n1️⃣ 创建测试学期")
    future_start = datetime.now() + timedelta(days=365)
    future_end = future_start + timedelta(days=120)
    
    create_data = {
        "name": "待删除测试学期",
        "code": "DEL2026",
        "start_date": future_start.isoformat() + "Z",
        "end_date": future_end.isoformat() + "Z"
    }
    
    create_response = client.post("/api/v1/semesters", json=create_data)
    print_response(create_response, "创建测试学期")
    
    if create_response.status_code == 200:
        result = create_response.json()
        if result.get("success"):
            semester_id = result["data"]["semester"]["id"]
            print(f"✅ 创建学期成功，ID: {semester_id}")
            
            # 2. 删除学期 - DELETE /api/v1/semesters/{id}
            print(f"\n2️⃣ 删除学期 (ID: {semester_id})")
            delete_response = client.delete(f"/api/v1/semesters/{semester_id}")
            print_response(delete_response, "删除学期")

def test_folder_deletion():
    """测试文件夹删除 - 基于api_folder_file.md"""
    print("\n📁 文件夹删除测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 1. 创建测试文件夹
    print("\n1️⃣ 创建测试文件夹")
    create_data = {
        "name": "待删除测试文件夹",
        "description": "这个文件夹将被删除",
        "scope": "personal"
    }
    
    create_response = client.post("/api/v1/folders", json=create_data)
    print_response(create_response, "创建测试文件夹")
    
    if create_response.status_code == 200:
        result = create_response.json()
        if result.get("success"):
            folder_id = result["data"]["folder"]["id"]
            print(f"✅ 创建文件夹成功，ID: {folder_id}")
            
            # 2. 删除文件夹 - DELETE /api/v1/folders/{id}
            print(f"\n2️⃣ 删除文件夹 (ID: {folder_id})")
            delete_response = client.delete(f"/api/v1/folders/{folder_id}")
            print_response(delete_response, "删除文件夹")

if __name__ == "__main__":
    print("⚠️  请确保已执行: source venv/bin/activate")
    print("⚠️  请确保服务正在运行: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("🗑️ 跨模块删除操作综合测试")
    print("📋 测试所有API文档中的删除功能")
    input("按回车键继续...")
    
    try:
        # 测试消息删除（包含聊天删除）
        chat_id = test_message_deletion()
        test_chat_deletion(chat_id)
        
        # 测试文件和文件夹删除
        test_file_deletion()
        test_folder_deletion()
        
        # 测试管理员删除功能
        test_invite_code_deletion()
        test_course_deletion()
        test_semester_deletion()
        
        print(f"\n🎉 跨模块删除操作测试完成！")
        print("✅ 测试了以下删除功能：")
        print("   - 消息删除 (api_chat_message_rag.md)")
        print("   - 聊天删除 (api_chat_message_rag.md)")
        print("   - 文件删除 (api_folder_file.md)")
        print("   - 文件夹删除 (api_folder_file.md)")
        print("   - 邀请码删除 (api_admin.md)")
        print("   - 课程删除 (api_semester_course.md)")
        print("   - 学期删除 (api_semester_course.md)")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()