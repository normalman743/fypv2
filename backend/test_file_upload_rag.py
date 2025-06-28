#!/usr/bin/env python3
"""
Test File Upload + RAG Integration
测试文件上传和RAG集成的完整流程
"""

import requests
import json
from pathlib import Path

# API Base URL
BASE_URL = "http://localhost:8000/api/v1"

def get_auth_token():
    """登录获取token"""
    login_data = {
        "username": "testuser",
        "password": "testpass"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["data"]["access_token"]
    else:
        print(f"Login failed: {response.text}")
        return None

def create_test_file():
    """创建测试文件"""
    content = """
计算机网络基础教程

第一章：网络协议概述

什么是TCP/IP？
TCP/IP（传输控制协议/网际协议）是互联网的基础协议栈。它包含四个层次：
1. 应用层（Application Layer）- HTTP、HTTPS、FTP等
2. 传输层（Transport Layer）- TCP、UDP
3. 网络层（Network Layer）- IP协议
4. 数据链路层（Data Link Layer）- 以太网协议

HTTP协议详解：
HTTP（超文本传输协议）是应用层协议，用于Web浏览器和服务器之间的通信。
- GET：获取资源
- POST：提交数据
- PUT：更新资源
- DELETE：删除资源

网络安全基础：
- HTTPS：HTTP的安全版本，使用SSL/TLS加密
- 防火墙：网络安全的第一道防线
- VPN：虚拟专用网络，保护网络连接安全
"""
    
    test_file = Path("network_tutorial.txt")
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return test_file

def test_file_upload_general():
    """测试上传到全局文件夹"""
    print("🌍 Testing General File Upload (Global Knowledge)")
    print("=" * 60)
    
    token = get_auth_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 创建测试文件
    test_file = create_test_file()
    
    try:
        # 上传文件到全局文件夹
        with open(test_file, 'rb') as f:
            files = {'file': (test_file.name, f, 'text/plain')}
            data = {
                'course_id': 1,  # 假设课程ID为1
                'folder_id': 1   # 假设文件夹ID为1  
            }
            
            response = requests.post(
                f"{BASE_URL}/files/upload",
                headers=headers,
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                print("✅ File uploaded successfully!")
                file_data = response.json()["data"]
                print(f"📄 File ID: {file_data['id']}")
                print(f"📝 Original Name: {file_data['original_name']}")
                print(f"📊 File Size: {file_data['file_size']} bytes")
                print(f"🔄 Processing Status: {file_data['processing_status']}")
                return file_data['id']
            else:
                print(f"❌ Upload failed: {response.text}")
                return None
    finally:
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()

def test_chat_with_uploaded_file(file_id):
    """测试与上传文件的对话"""
    print(f"\n💬 Testing Chat with Uploaded File (ID: {file_id})")
    print("=" * 60)
    
    token = get_auth_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 创建聊天
    chat_data = {
        "title": "网络协议学习",
        "chat_type": "course",
        "course_id": 1,
        "first_message": "TCP/IP协议包含哪几个层次？请详细解释。"
    }
    
    response = requests.post(
        f"{BASE_URL}/chats",
        headers=headers,
        json=chat_data
    )
    
    if response.status_code == 200:
        chat_data = response.json()["data"]
        print("✅ Chat created successfully!")
        print(f"💬 Chat ID: {chat_data['chat_id']}")
        print(f"📝 AI Response Preview: {chat_data['ai_response']['content'][:200]}...")
        
        # 检查是否使用了RAG源
        rag_sources = chat_data['ai_response'].get('rag_sources', [])
        if rag_sources:
            print(f"📚 RAG Sources Used: {len(rag_sources)}")
            for source in rag_sources:
                print(f"   - {source['source_file']} (chunk {source['chunk_id']})")
        else:
            print("⚠️ No RAG sources used")
            
        return chat_data['chat_id']
    else:
        print(f"❌ Chat creation failed: {response.text}")
        return None

def test_multiple_questions(chat_id):
    """测试多个问题"""
    print(f"\n🔄 Testing Multiple Questions (Chat ID: {chat_id})")
    print("=" * 60)
    
    token = get_auth_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    questions = [
        "HTTP协议有哪些常用方法？",
        "HTTPS和HTTP的区别是什么？",
        "什么是防火墙？它的作用是什么？",
        "VPN是什么意思？"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n❓ Question {i}: {question}")
        
        message_data = {
            "content": question
        }
        
        response = requests.post(
            f"{BASE_URL}/chats/{chat_id}/messages",
            headers=headers,
            json=message_data
        )
        
        if response.status_code == 200:
            data = response.json()["data"]
            ai_response = data["ai_response"]
            print(f"✅ Response: {ai_response['content'][:150]}...")
            print(f"📊 Tokens: {ai_response['tokens_used']}, Cost: ${ai_response['cost']:.6f}")
            
            rag_sources = ai_response.get('rag_sources', [])
            if rag_sources:
                print(f"📚 RAG Sources: {len(rag_sources)} sources used")
            else:
                print("📚 No RAG sources (using general knowledge)")
        else:
            print(f"❌ Message failed: {response.text}")

def main():
    """主测试函数"""
    print("🚀 File Upload + RAG Integration Test")
    print("=" * 80)
    
    # 确保服务器运行
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
        if response.status_code != 200:
            print("❌ Server not running. Please start the FastAPI server first.")
            print("Run: uvicorn app.main:app --reload")
            return
    except requests.ConnectionError:
        print("❌ Cannot connect to server. Please start the FastAPI server first.")
        print("Run: uvicorn app.main:app --reload")
        return
    
    print("✅ Server is running")
    
    # 测试文件上传
    file_id = test_file_upload_general()
    if not file_id:
        print("❌ File upload test failed")
        return
    
    # 测试聊天
    chat_id = test_chat_with_uploaded_file(file_id)
    if not chat_id:
        print("❌ Chat test failed")
        return
    
    # 测试多个问题
    test_multiple_questions(chat_id)
    
    print("\n" + "=" * 80)
    print("🎉 File Upload + RAG Test Complete!")
    print("Check that uploaded files are automatically processed and used in responses.")

if __name__ == "__main__":
    main()