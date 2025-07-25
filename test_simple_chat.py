#!/usr/bin/env python3
import sys
import os
sys.path.append('/Users/mannormal/Downloads/fyp/backend/api_test_v3')

from utils import APIClient
from config import test_config

def test_simple_chat():
    """测试简单的聊天创建（无文件）"""
    # 登录
    client = APIClient()
    user_data = test_config.default_users["user"]
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    
    if login_response.status_code != 200:
        print(f"登录失败: {login_response.status_code}")
        return False
    
    token = login_response.json()['data']['access_token']
    client.set_auth_token(token)
    
    # 创建简单聊天
    chat_data = {
        "chat_type": "general",
        "first_message": "Hello, this is a test message without any files."
    }
    
    response = client.post("/api/v1/chats", json=chat_data)
    
    print(f"创建聊天响应: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ 无文件聊天创建成功")
        print(f"AI回复: {result['data']['ai_message']['content'][:100]}...")
        return True
    else:
        print(f"❌ 创建失败: {response.text}")
        return False

if __name__ == "__main__":
    test_simple_chat()