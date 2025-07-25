#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试创建聊天时支持临时文件的功能
使用前请先: source venv/bin/activate
运行: python api_test_v3/test_chat_with_temp_files.py
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
        return token
    else:
        logger.error(f"登录失败: {login_response.status_code}")
        return None

def upload_temporary_file(client, content="测试文件内容", filename="test_temp.txt"):
    """上传临时文件并返回token"""
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    try:
        # 上传文件
        with open(temp_path, 'rb') as f:
            files = {"file": (filename, f, "text/plain")}
            data = {
                "purpose": "chat_upload",
                "expiry_hours": 1  # 1小时后过期
            }
            
            # 临时移除Content-Type头，让requests自动设置multipart/form-data
            old_headers = client.session.headers.copy()
            if 'Content-Type' in client.session.headers:
                del client.session.headers['Content-Type']
            
            try:
                response = client.post(
                    "/api/v1/files/temporary",
                    files=files,
                    data=data
                )
            finally:
                # 恢复原始头部
                client.session.headers.update(old_headers)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 临时文件上传成功")
                print(f"   响应: {result}")
                # 尝试不同的响应格式
                if 'data' in result and 'file' in result['data'] and 'token' in result['data']['file']:
                    token = result['data']['file']['token']
                elif 'data' in result and 'token' in result['data']:
                    token = result['data']['token']
                elif 'token' in result:
                    token = result['token']
                else:
                    print(f"   无法找到token字段，响应结构: {list(result.keys())}")
                    return None
                print(f"   token: {token[:10]}...")
                return token
            else:
                print(f"❌ 临时文件上传失败: {response.status_code}")
                print_response(response, "上传临时文件")
                return None
    finally:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_create_chat_with_temp_files():
    """测试创建聊天时附带临时文件"""
    print("\n🧪 测试创建聊天时支持临时文件")
    print("=" * 50)
    
    # 1. 获取token
    print("\n1️⃣ 登录获取token")
    token = get_user_token("user")
    if not token:
        print("❌ 获取token失败")
        return False
    
    # 创建客户端并设置token
    client = APIClient()
    client.set_auth_token(token)
    print("✅ 登录成功")
    
    # 2. 上传多个临时文件
    print("\n2️⃣ 上传临时文件")
    temp_tokens = []
    
    # 上传第一个文件
    token1 = upload_temporary_file(
        client, 
        "这是第一个测试文件的内容\n包含一些测试数据\n用于验证AI是否能读取",
        "test_file_1.txt"
    )
    if token1:
        temp_tokens.append(token1)
    
    # 上传第二个文件
    token2 = upload_temporary_file(
        client,
        "这是第二个测试文件的内容\n包含更多测试数据\n测试多文件处理能力",
        "test_file_2.txt"
    )
    if token2:
        temp_tokens.append(token2)
    
    if len(temp_tokens) < 2:
        print("❌ 临时文件上传失败")
        return False
    
    # 3. 创建聊天并附带临时文件
    print("\n3️⃣ 创建聊天并附带临时文件")
    chat_data = {
        "chat_type": "general",
        "first_message": "请帮我分析这些上传的文件内容，告诉我每个文件都包含什么信息",
        "temporary_file_tokens": temp_tokens
    }
    
    response = client.post("/api/v1/chats", json=chat_data)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 聊天创建成功")
        
        # 检查响应中是否包含临时文件信息
        user_message = result['data']['user_message']
        if 'temporary_file_attachments' in user_message:
            print(f"✅ 临时文件已附加到消息: {len(user_message['temporary_file_attachments'])} 个文件")
            for temp_file in user_message['temporary_file_attachments']:
                print(f"  - {temp_file['filename']} (token: {temp_file['token'][:10]}...)")
        else:
            print("❌ 响应中没有临时文件信息")
            
        # 检查AI响应是否包含文件内容
        ai_message = result['data']['ai_message']
        ai_content = ai_message['content']
        if '第一个' in ai_content and '第二个' in ai_content:
            print("✅ AI响应中正确提到了两个文件的内容")
        else:
            print("⚠️  AI响应可能没有正确处理文件内容")
            
        return True
    else:
        print(f"❌ 聊天创建失败: {response.status_code}")
        print_response(response, "创建聊天")
        return False

def test_create_chat_with_expired_temp_file():
    """测试创建聊天时处理过期的临时文件"""
    print("\n\n🧪 测试过期临时文件处理")
    print("=" * 50)
    
    # 获取token
    token = get_user_token("user")
    if not token:
        print("❌ 获取token失败")
        return False
    
    # 创建客户端并设置token
    client = APIClient()
    client.set_auth_token(token)
    
    # 创建一个立即过期的临时文件
    print("\n1️⃣ 上传即将过期的临时文件")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("这是一个即将过期的文件")
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            files = {"file": ("expired_temp.txt", f, "text/plain")}
            data = {
                "purpose": "chat_upload",
                "expiry_hours": 0  # 立即过期
            }
            
            # 临时移除Content-Type头，让requests自动设置multipart/form-data
            old_headers = client.session.headers.copy()
            if 'Content-Type' in client.session.headers:
                del client.session.headers['Content-Type']
            
            try:
                response = client.post(
                    "/api/v1/files/temporary",
                    files=files,
                    data=data
                )
            finally:
                # 恢复原始头部
                client.session.headers.update(old_headers)
            
            if response.status_code == 200:
                result = response.json()
                expired_token = result['data']['file']['token']
                print(f"✅ 文件上传成功: token={expired_token[:10]}...")
                
                # 等待确保文件过期
                import time
                time.sleep(2)
                
                # 尝试创建聊天
                print("\n2️⃣ 使用过期文件创建聊天")
                chat_data = {
                    "chat_type": "general",
                    "first_message": "测试过期文件处理",
                    "temporary_file_tokens": [expired_token]
                }
                
                response = client.post("/api/v1/chats", json=chat_data)
                
                if response.status_code == 200:
                    result = response.json()
                    ai_content = result['data']['ai_message']['content']
                    if '过期' in ai_content:
                        print("✅ AI响应中正确提到了文件过期")
                    else:
                        print("⚠️  AI响应可能没有正确处理过期文件")
                    return True
                else:
                    print(f"❌ 聊天创建失败: {response.status_code}")
                    return False
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def main():
    """运行所有测试"""
    print("=" * 60)
    print("🚀 测试创建聊天时支持临时文件功能")
    print("=" * 60)
    
    # 测试正常的临时文件
    success1 = test_create_chat_with_temp_files()
    
    # 测试过期的临时文件
    success2 = test_create_chat_with_expired_temp_file()
    
    print("\n" + "=" * 60)
    print("📊 测试总结:")
    print(f"  ✅ 正常临时文件测试: {'通过' if success1 else '失败'}")
    print(f"  ✅ 过期临时文件测试: {'通过' if success2 else '失败'}")
    print("=" * 60)

if __name__ == "__main__":
    main()