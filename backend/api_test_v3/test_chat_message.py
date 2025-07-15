#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天和消息功能测试
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
    """测试聊天管理"""
    print("💬 聊天管理测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return None
    
    client.set_auth_token(user_token)
    
    # 1. 获取所有聊天会话
    print("\n1️⃣ 获取所有聊天会话")
    chats_response = client.get("/api/v1/chats")
    print_response(chats_response, "获取聊天列表")
    
    # 2. 创建新聊天会话
    print("\n2️⃣ 创建新聊天会话")
    chat_data = {
        "title": "测试聊天会话",
        "description": "用于测试的聊天会话",
        "scope": "personal"
    }
    
    create_chat_response = client.post("/api/v1/chats", json=chat_data)
    print_response(create_chat_response, "创建聊天")
    
    chat_id = None
    if create_chat_response.status_code == 200:
        result = create_chat_response.json()
        if result.get("success"):
            chat_id = result["data"]["id"]
            print(f"✅ 创建聊天会话成功，ID: {chat_id}")
    
    # 3. 获取特定聊天会话信息
    if chat_id:
        print(f"\n3️⃣ 获取聊天会话信息 (ID: {chat_id})")
        chat_detail_response = client.get(f"/api/v1/chats/{chat_id}")
        print_response(chat_detail_response, "聊天详情")
    
    # 4. 更新聊天会话信息
    if chat_id:
        print(f"\n4️⃣ 更新聊天会话信息")
        update_data = {
            "title": "更新后的聊天标题",
            "description": "更新后的聊天描述"
        }
        update_response = client.put(f"/api/v1/chats/{chat_id}", json=update_data)
        print_response(update_response, "更新聊天")
    
    return chat_id

def test_message_management():
    """测试消息管理"""
    print("\n📨 消息管理测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return None
    
    client.set_auth_token(user_token)
    
    # 创建聊天会话
    chat_id = test_chat_management()
    if not chat_id:
        print("❌ 无法创建聊天会话，跳过消息测试")
        return
    
    # 1. 获取聊天会话的消息
    print(f"\n1️⃣ 获取聊天会话消息 (Chat ID: {chat_id})")
    messages_response = client.get(f"/api/v1/chats/{chat_id}/messages")
    print_response(messages_response, "获取消息列表")
    
    # 2. 发送用户消息
    print(f"\n2️⃣ 发送用户消息")
    message_data = {
        "content": "你好，这是一条测试消息",
        "message_type": "user"
    }
    
    send_message_response = client.post(f"/api/v1/chats/{chat_id}/messages", json=message_data)
    print_response(send_message_response, "发送消息")
    
    message_id = None
    if send_message_response.status_code == 200:
        result = send_message_response.json()
        if result.get("success"):
            message_id = result["data"]["id"]
            print(f"✅ 发送消息成功，ID: {message_id}")
    
    # 3. 获取特定消息信息
    if message_id:
        print(f"\n3️⃣ 获取消息信息 (ID: {message_id})")
        message_detail_response = client.get(f"/api/v1/messages/{message_id}")
        print_response(message_detail_response, "消息详情")
    
    # 4. 发送AI回复消息
    print(f"\n4️⃣ 发送AI回复消息")
    ai_message_data = {
        "content": "这是一条AI回复消息，回复用户的问题",
        "message_type": "assistant"
    }
    
    ai_message_response = client.post(f"/api/v1/chats/{chat_id}/messages", json=ai_message_data)
    print_response(ai_message_response, "AI回复消息")
    
    # 5. 分页获取消息
    print(f"\n5️⃣ 分页获取消息")
    paginated_messages_response = client.get(f"/api/v1/chats/{chat_id}/messages", params={
        "page": 1,
        "size": 10
    })
    print_response(paginated_messages_response, "分页获取消息")
    
    # 6. 编辑消息
    if message_id:
        print(f"\n6️⃣ 编辑消息")
        edit_data = {
            "content": "这是编辑后的消息内容"
        }
        edit_response = client.put(f"/api/v1/messages/{message_id}", json=edit_data)
        print_response(edit_response, "编辑消息")
    
    return message_id

def test_rag_functionality():
    """测试RAG功能"""
    print("\n🔍 RAG功能测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 获取消息ID
    message_id = test_message_management()
    if not message_id:
        print("❌ 无法获取消息ID，跳过RAG测试")
        return
    
    # 1. 执行RAG搜索
    print(f"\n1️⃣ 执行RAG搜索")
    rag_data = {
        "query": "软件工程",
        "scope": "personal",
        "limit": 5
    }
    
    rag_response = client.post(f"/api/v1/messages/{message_id}/rag", json=rag_data)
    print_response(rag_response, "RAG搜索")
    
    # 2. 获取消息的RAG源
    print(f"\n2️⃣ 获取消息的RAG源")
    rag_sources_response = client.get(f"/api/v1/messages/{message_id}/rag-sources")
    print_response(rag_sources_response, "RAG源列表")
    
    # 3. 测试不同范围的RAG搜索
    print(f"\n3️⃣ 测试全局范围RAG搜索")
    global_rag_data = {
        "query": "测试文档",
        "scope": "global",
        "limit": 3
    }
    
    global_rag_response = client.post(f"/api/v1/messages/{message_id}/rag", json=global_rag_data)
    print_response(global_rag_response, "全局RAG搜索")

def test_chat_ai_integration():
    """测试聊天AI集成"""
    print("\n🤖 聊天AI集成测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 1. 创建聊天会话
    chat_data = {
        "title": "AI对话测试",
        "description": "测试AI对话功能",
        "scope": "personal"
    }
    
    create_chat_response = client.post("/api/v1/chats", json=chat_data)
    if create_chat_response.status_code != 200:
        print("❌ 创建聊天会话失败")
        return
    
    chat_id = create_chat_response.json()["data"]["id"]
    
    # 2. 发送问题并获取AI回复
    print(f"\n1️⃣ 发送问题并获取AI回复")
    user_question = {
        "content": "请介绍一下软件工程的基本概念",
        "message_type": "user"
    }
    
    question_response = client.post(f"/api/v1/chats/{chat_id}/messages", json=user_question)
    print_response(question_response, "发送问题")
    
    if question_response.status_code == 200:
        # 等待AI处理
        print("⏳ 等待AI处理...")
        time.sleep(2)
        
        # 获取AI回复
        messages_response = client.get(f"/api/v1/chats/{chat_id}/messages")
        if messages_response.status_code == 200:
            messages = messages_response.json()["data"]
            ai_messages = [msg for msg in messages if msg.get("message_type") == "assistant"]
            if ai_messages:
                print(f"✅ 获取到AI回复: {len(ai_messages)} 条")
                print(f"回复内容预览: {ai_messages[0]['content'][:100]}...")
            else:
                print("⚠️ 暂未获取到AI回复")

def test_message_search():
    """测试消息搜索"""
    print("\n🔎 消息搜索测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 1. 搜索消息
    print(f"\n1️⃣ 搜索消息")
    search_response = client.get("/api/v1/messages/search", params={
        "query": "测试",
        "limit": 10
    })
    print_response(search_response, "搜索消息")
    
    # 2. 按消息类型搜索
    print(f"\n2️⃣ 按消息类型搜索")
    type_search_response = client.get("/api/v1/messages/search", params={
        "query": "测试",
        "message_type": "user",
        "limit": 5
    })
    print_response(type_search_response, "按类型搜索")

if __name__ == "__main__":
    print("⚠️  请确保已执行: source venv/bin/activate")
    print("⚠️  请确保服务正在运行: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    input("按回车键继续...")
    
    try:
        test_chat_management()
        test_message_management()
        test_rag_functionality()
        test_chat_ai_integration()
        test_message_search()
        print(f"\n🎉 聊天和消息功能测试完成！")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()