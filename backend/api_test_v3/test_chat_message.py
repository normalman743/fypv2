#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天和消息功能测试 - 基于api_chat_message_rag.md文档
使用前请先: source venv/bin/activate
运行: python api_test_v3/test_chat_message.py
"""

import sys
import os
import time
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

def test_chat_management():
    """测试聊天管理 - 基于api_chat_message_rag.md"""
    print("💬 聊天管理测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return None
    
    client.set_auth_token(user_token)
    
    # 1. 获取聊天列表 - GET /api/v1/chats
    print("\n1️⃣ 获取聊天列表")
    chats_response = client.get("/api/v1/chats")
    print_response(chats_response, "获取聊天列表")
    
    # 2. 创建通用聊天 - POST /api/v1/chats
    print("\n2️⃣ 创建通用聊天")
    create_general_data = {
        "chat_type": "general",
        "first_message": "崇基学院体育馆的开放时间是什么时候",
        "course_id": None,
        "custom_prompt": None,
        "file_ids": []
    }
    
    create_chat_response = client.post("/api/v1/chats", json=create_general_data)
    print_response(create_chat_response, "创建通用聊天")
    
    chat_id = None
    if create_chat_response.status_code == 200:
        result = create_chat_response.json()
        if result.get("success"):
            chat_id = result["data"]["chat"]["id"]
            print(f"✅ 创建聊天成功，ID: {chat_id}")
    
    # 3. 创建课程聊天 - POST /api/v1/chats (需要课程ID)
    print("\n3️⃣ 创建课程聊天")
    create_course_data = {
        "chat_type": "course",
        "first_message": "这节课讲了什么",
        "course_id": 1,  # 假设存在课程ID为1
        "custom_prompt": None,
        "file_ids": []
    }
    
    create_course_chat_response = client.post("/api/v1/chats", json=create_course_data)
    print_response(create_course_chat_response, "创建课程聊天")
    
    course_chat_id = None
    if create_course_chat_response.status_code == 200:
        result = create_course_chat_response.json()
        if result.get("success"):
            course_chat_id = result["data"]["chat"]["id"]
            print(f"✅ 创建课程聊天成功，ID: {course_chat_id}")
    
    # 4. 更新聊天标题 - PUT /api/v1/chats/{id}
    if chat_id:
        print(f"\n4️⃣ 更新聊天标题 (ID: {chat_id})")
        update_data = {
            "title": "体育馆开放时间咨询"
        }
        update_response = client.put(f"/api/v1/chats/{chat_id}", json=update_data)
        print_response(update_response, "更新聊天标题")
    
    return chat_id, course_chat_id

def test_message_management(chat_id=None):
    """测试消息管理 - 基于api_chat_message_rag.md"""
    print("\n📝 消息管理测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    if not chat_id:
        print("❌ 没有可用的聊天ID，跳过消息测试")
        return
    
    # 1. 获取消息列表 - GET /api/v1/chats/{id}/messages
    print(f"\n1️⃣ 获取消息列表 (Chat ID: {chat_id})")
    messages_response = client.get(f"/api/v1/chats/{chat_id}/messages")
    print_response(messages_response, "获取消息列表")
    
    # 2. 发送消息 - POST /api/v1/chats/{id}/messages
    print(f"\n2️⃣ 发送消息 (Chat ID: {chat_id})")
    send_message_data = {
        "content": "请提供更详细的体育馆设施信息",
        "file_ids": []
    }
    
    send_response = client.post(f"/api/v1/chats/{chat_id}/messages", json=send_message_data)
    print_response(send_response, "发送消息")
    
    message_id = None
    if send_response.status_code == 200:
        result = send_response.json()
        if result.get("success"):
            message_id = result["data"]["user_message"]["id"]
            print(f"✅ 发送消息成功，ID: {message_id}")
    
    # 3. 编辑消息 - PUT /api/v1/messages/{id}
    if message_id:
        print(f"\n3️⃣ 编辑消息 (Message ID: {message_id})")
        edit_data = {
            "content": "请提供体育馆的详细开放时间和设施信息"
        }
        edit_response = client.put(f"/api/v1/messages/{message_id}", json=edit_data)
        print_response(edit_response, "编辑消息")
    
    # 获取最新消息ID用于删除测试
    messages_response = client.get(f"/api/v1/chats/{chat_id}/messages")
    if messages_response.status_code == 200:
        result = messages_response.json()
        if result.get("success") and result["data"]["messages"]:
            # 找到最后一条用户消息
            for msg in reversed(result["data"]["messages"]):
                if msg["role"] == "user":
                    message_id = msg["id"]
                    break
    
    # 4. 删除消息 - DELETE /api/v1/messages/{id}
    if message_id:
        print(f"\n4️⃣ 删除消息 (Message ID: {message_id})")
        delete_response = client.delete(f"/api/v1/messages/{message_id}")
        print_response(delete_response, "删除消息")

def test_rag_functionality():
    """测试RAG功能和聊天类型"""
    print("\n🧠 RAG功能测试")
    print("=" * 50)
    print("📝 注意: 如果没有配置OpenAI API密钥，系统将使用Mock模式")
    print("   Mock模式下的RAG结果是预设的模拟数据")
    print("   要测试真实RAG功能，需要配置有效的OpenAI API密钥")
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 动态获取课程ID用于课程聊天测试
    courses_response = client.get("/api/v1/courses")
    course_id = None
    if courses_response.status_code == 200:
        result = courses_response.json()
        if result.get("success") and result["data"]["courses"]:
            course_id = result["data"]["courses"][0]["id"]
            print(f"✅ 使用课程ID: {course_id} 用于课程聊天测试")
        else:
            print("⚠️ 没有可用课程，将仅测试通用聊天")
    
    # 测试通用聊天的全局检索
    print("\n1️⃣ 测试通用聊天 - 全局知识库检索")
    general_chat_data = {
        "chat_type": "general",
        "first_message": "学校的图书馆开放时间是什么",
        "course_id": None,
        "custom_prompt": None,
        "file_ids": []
    }
    
    general_response = client.post("/api/v1/chats", json=general_chat_data)
    print_response(general_response, "通用聊天RAG测试")
    
    # 测试课程聊天的课程特定检索
    print("\n2️⃣ 测试课程聊天 - 课程+全局知识库检索")
    course_chat_data = {
        "chat_type": "course" if course_id else "general",
        "first_message": "这门课程的主要学习目标是什么" if course_id else "RAG功能测试",
        "course_id": course_id,
        "custom_prompt": None,
        "file_ids": []
    }
    
    # RAG处理可能需要更长时间，增加超时
    print("⏳ 创建课程聊天（RAG处理可能需要较长时间）...")
    course_response = client.post("/api/v1/chats", json=course_chat_data, timeout=120)  # 2分钟超时
    print_response(course_response, "课程聊天RAG测试")

def test_chat_deletion():
    """测试聊天删除功能"""
    print("\n🗑️ 聊天删除测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 创建一个测试聊天用于删除
    print("\n1️⃣ 创建测试聊天")
    create_data = {
        "chat_type": "general",
        "first_message": "这是一个测试聊天",
        "course_id": None,
        "custom_prompt": None,
        "file_ids": []
    }
    
    create_response = client.post("/api/v1/chats", json=create_data)
    print_response(create_response, "创建测试聊天")
    
    chat_id = None
    if create_response.status_code == 200:
        result = create_response.json()
        if result.get("success"):
            chat_id = result["data"]["chat"]["id"]
            print(f"✅ 创建测试聊天成功，ID: {chat_id}")
    
    # 删除聊天 - DELETE /api/v1/chats/{id}
    if chat_id:
        print(f"\n2️⃣ 删除聊天 (ID: {chat_id})")
        delete_response = client.delete(f"/api/v1/chats/{chat_id}")
        print_response(delete_response, "删除聊天")

if __name__ == "__main__":
    print("⚠️  请确保已执行: source venv/bin/activate")
    print("⚠️  请确保服务正在运行: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("⚠️  建议先运行: python prepare_test_documents.py 上传测试文档")
    print("📋 基于 api_chat_message_rag.md 文档的测试")
    
    # 询问是否需要准备测试文档
    prepare_docs = input("是否需要先上传测试文档用于RAG测试？(y/N): ")
    if prepare_docs.lower() == 'y':
        print("请先运行: python prepare_test_documents.py")
        print("然后重新运行此测试")
        sys.exit(0)
    
    input("按回车键继续...")
    
    try:
        # 测试聊天管理
        chat_id, course_chat_id = test_chat_management()
        
        # 测试消息管理
        if chat_id:
            test_message_management(chat_id)
        
        # 测试RAG功能
        test_rag_functionality()
        
        # 测试聊天删除
        test_chat_deletion()
        
        print(f"\n🎉 聊天和消息功能测试完成！")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()