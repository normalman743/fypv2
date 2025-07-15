#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
删除操作测试脚本
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

def test_file_deletion():
    """测试文件删除功能"""
    print("🗑️ 文件删除测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 1. 先创建一个文件夹
    print("\n1️⃣ 创建测试文件夹")
    folder_data = {
        "name": "待删除测试文件夹",
        "description": "用于测试删除功能",
        "scope": "personal"
    }
    
    folder_response = client.post("/api/v1/folders", json=folder_data)
    print_response(folder_response, "创建文件夹")
    
    folder_id = None
    if folder_response.status_code == 200:
        result = folder_response.json()
        if result.get("success"):
            folder_id = result["data"]["folder"]["id"]
            print(f"✅ 创建文件夹成功，ID: {folder_id}")
    
    # 2. 上传测试文件
    print("\n2️⃣ 上传测试文件")
    test_file_path = create_test_file("这是待删除的测试文件", "delete_test.txt")
    
    file_id = None
    try:
        upload_data = {
            "scope": "personal",
            "folder_id": folder_id
        }
        
        with open(test_file_path, 'rb') as f:
            files = {'file': ('delete_test.txt', f, 'text/plain')}
            upload_response = client.post("/api/v1/files/upload", data=upload_data, files=files)
        
        print_response(upload_response, "文件上传")
        
        if upload_response.status_code == 200:
            result = upload_response.json()
            if result.get("success"):
                file_id = result["data"]["file"]["id"]
                print(f"✅ 文件上传成功，ID: {file_id}")
        
        # 3. 删除文件
        if file_id:
            print(f"\n3️⃣ 删除文件 (ID: {file_id})")
            delete_file_response = client.delete(f"/api/v1/files/{file_id}")
            print_response(delete_file_response, "删除文件")
            
            if delete_file_response.status_code == 200:
                print("✅ 文件删除成功")
                
                # 4. 验证文件已被删除
                print(f"\n4️⃣ 验证文件已被删除")
                get_file_response = client.get(f"/api/v1/files/{file_id}")
                print_response(get_file_response, "获取已删除文件")
                
                if get_file_response.status_code == 404:
                    print("✅ 文件确实已被删除")
                else:
                    print("⚠️ 文件可能未被正确删除")
            else:
                print("❌ 文件删除失败")
        
    finally:
        # 清理临时文件
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)
    
    # 5. 删除文件夹
    if folder_id:
        print(f"\n5️⃣ 删除文件夹 (ID: {folder_id})")
        delete_folder_response = client.delete(f"/api/v1/folders/{folder_id}")
        print_response(delete_folder_response, "删除文件夹")
        
        if delete_folder_response.status_code == 200:
            print("✅ 文件夹删除成功")
        else:
            print("❌ 文件夹删除失败")

def test_message_deletion():
    """测试消息删除功能"""
    print("\n💬 消息删除测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 1. 创建测试聊天会话
    print("\n1️⃣ 创建测试聊天会话")
    chat_data = {
        "title": "待删除测试聊天",
        "description": "用于测试删除功能",
        "scope": "personal"
    }
    
    chat_response = client.post("/api/v1/chats", json=chat_data)
    print_response(chat_response, "创建聊天")
    
    chat_id = None
    if chat_response.status_code == 200:
        result = chat_response.json()
        if result.get("success"):
            chat_id = result["data"]["id"]
            print(f"✅ 创建聊天成功，ID: {chat_id}")
    
    # 2. 发送测试消息
    message_id = None
    if chat_id:
        print(f"\n2️⃣ 发送测试消息")
        message_data = {
            "content": "这是一条待删除的测试消息",
            "message_type": "user"
        }
        
        message_response = client.post(f"/api/v1/chats/{chat_id}/messages", json=message_data)
        print_response(message_response, "发送消息")
        
        if message_response.status_code == 200:
            result = message_response.json()
            if result.get("success"):
                message_id = result["data"]["id"]
                print(f"✅ 消息发送成功，ID: {message_id}")
    
    # 3. 删除消息
    if message_id:
        print(f"\n3️⃣ 删除消息 (ID: {message_id})")
        delete_message_response = client.delete(f"/api/v1/messages/{message_id}")
        print_response(delete_message_response, "删除消息")
        
        if delete_message_response.status_code == 200:
            print("✅ 消息删除成功")
        else:
            print("❌ 消息删除失败")
    
    # 4. 删除聊天会话
    if chat_id:
        print(f"\n4️⃣ 删除聊天会话 (ID: {chat_id})")
        delete_chat_response = client.delete(f"/api/v1/chats/{chat_id}")
        print_response(delete_chat_response, "删除聊天")
        
        if delete_chat_response.status_code == 200:
            print("✅ 聊天删除成功")
            
            # 5. 验证聊天已被删除
            print(f"\n5️⃣ 验证聊天已被删除")
            get_chat_response = client.get(f"/api/v1/chats/{chat_id}")
            print_response(get_chat_response, "获取已删除聊天")
            
            if get_chat_response.status_code == 404:
                print("✅ 聊天确实已被删除")
            else:
                print("⚠️ 聊天可能未被正确删除")
        else:
            print("❌ 聊天删除失败")

def test_course_semester_deletion():
    """测试课程和学期删除功能"""
    print("\n🎓 课程和学期删除测试")
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
    semester_data = {
        "name": "待删除测试学期",
        "code": "DELETE-TEST",
        "is_active": True
    }
    
    semester_response = client.post("/api/v1/semesters", json=semester_data)
    print_response(semester_response, "创建学期")
    
    semester_id = None
    if semester_response.status_code == 200:
        result = semester_response.json()
        if result.get("success"):
            semester_id = result["data"]["semester"]["id"]
            print(f"✅ 创建学期成功，ID: {semester_id}")
    
    # 2. 创建测试课程
    course_id = None
    if semester_id:
        print(f"\n2️⃣ 创建测试课程")
        course_data = {
            "name": "待删除测试课程",
            "code": "DELETE-COURSE",
            "description": "用于测试删除功能的课程",
            "semester_id": semester_id
        }
        
        course_response = client.post("/api/v1/courses", json=course_data)
        print_response(course_response, "创建课程")
        
        if course_response.status_code == 200:
            result = course_response.json()
            if result.get("success"):
                course_id = result["data"]["course"]["id"]
                print(f"✅ 创建课程成功，ID: {course_id}")
    
    # 3. 删除课程
    if course_id:
        print(f"\n3️⃣ 删除课程 (ID: {course_id})")
        delete_course_response = client.delete(f"/api/v1/courses/{course_id}")
        print_response(delete_course_response, "删除课程")
        
        if delete_course_response.status_code == 200:
            print("✅ 课程删除成功")
        else:
            print("❌ 课程删除失败")
    
    # 4. 删除学期
    if semester_id:
        print(f"\n4️⃣ 删除学期 (ID: {semester_id})")
        delete_semester_response = client.delete(f"/api/v1/semesters/{semester_id}")
        print_response(delete_semester_response, "删除学期")
        
        if delete_semester_response.status_code == 200:
            print("✅ 学期删除成功")
        else:
            print("❌ 学期删除失败")

def test_invite_code_deletion():
    """测试邀请码删除功能"""
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
    from datetime import datetime, timedelta
    future_date = datetime.now() + timedelta(days=7)
    
    invite_data = {
        "code": "DELETE-TEST-2024",
        "description": "待删除测试邀请码",
        "expires_at": future_date.isoformat(),
        "is_active": True
    }
    
    invite_response = client.post("/api/v1/admin/invite-codes", json=invite_data)
    print_response(invite_response, "创建邀请码")
    
    invite_id = None
    if invite_response.status_code == 200:
        result = invite_response.json()
        if result.get("success"):
            invite_id = result["data"]["id"]
            print(f"✅ 创建邀请码成功，ID: {invite_id}")
    
    # 2. 删除邀请码
    if invite_id:
        print(f"\n2️⃣ 删除邀请码 (ID: {invite_id})")
        delete_invite_response = client.delete(f"/api/v1/admin/invite-codes/{invite_id}")
        print_response(delete_invite_response, "删除邀请码")
        
        if delete_invite_response.status_code == 200:
            print("✅ 邀请码删除成功")
        else:
            print("❌ 邀请码删除失败")

if __name__ == "__main__":
    print("⚠️  请确保已执行: source venv/bin/activate")
    print("⚠️  请确保服务正在运行: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("⚠️  此测试会创建和删除测试数据")
    input("按回车键继续...")
    
    try:
        test_file_deletion()
        test_message_deletion()
        test_course_semester_deletion()
        test_invite_code_deletion()
        print(f"\n🎉 删除操作测试完成！")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()