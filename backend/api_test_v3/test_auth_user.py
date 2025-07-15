#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证和用户信息测试
使用前请先: source venv/bin/activate
运行: python api_test_v3/test_auth_user.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import APIClient, print_response, extract_token_from_response
from config import test_config
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_auth_and_user():
    """测试认证和用户信息功能"""
    print("🔐 认证和用户信息测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 1. 测试用户登录
    print("\n1️⃣ 测试用户登录")
    for user_type in ["admin", "user"]:
        user_data = test_config.default_users[user_type]
        print(f"\n📝 测试 {user_type} 用户登录")
        
        login_response = client.post("/api/v1/auth/login", json={
            "username": user_data["username"],
            "password": user_data["password"]
        })
        
        print_response(login_response, f"{user_type} 登录")
        
        if login_response.status_code == 200:
            token = extract_token_from_response(login_response)
            if token:
                print(f"✅ {user_type} 登录成功，获取到token")
                
                # 设置认证token
                client.set_auth_token(token)
                
                # 2. 测试获取当前用户信息
                print(f"\n2️⃣ 测试获取 {user_type} 用户信息")
                me_response = client.get("/api/v1/auth/me")
                print_response(me_response, f"{user_type} 用户信息")
                
                if me_response.status_code == 200:
                    user_info = me_response.json()
                    if user_info.get("success"):
                        actual_role = user_info["data"]["role"]
                        print(f"✅ 用户角色: {actual_role}")
                        print(f"✅ 用户余额: {user_info['data']['balance']}")
                        
                        # 3. 测试更新用户信息
                        print(f"\n3️⃣ 测试更新 {user_type} 用户信息")
                        update_data = {
                            "preferred_language": "en_US",
                            "preferred_theme": "dark"
                        }
                        update_response = client.put("/api/v1/auth/me", json=update_data)
                        print_response(update_response, f"{user_type} 更新信息")
                        
                        if update_response.status_code == 200:
                            print(f"✅ {user_type} 用户信息更新成功")
                            
                            # 验证更新结果
                            verify_response = client.get("/api/v1/auth/me")
                            if verify_response.status_code == 200:
                                verify_info = verify_response.json()
                                if verify_info.get("success"):
                                    updated_user = verify_info["data"]
                                    print(f"✅ 语言设置: {updated_user['preferred_language']}")
                                    print(f"✅ 主题设置: {updated_user['preferred_theme']}")
                        else:
                            print(f"❌ {user_type} 用户信息更新失败")
                    else:
                        print(f"❌ {user_type} 用户信息获取失败")
                else:
                    print(f"❌ {user_type} 获取用户信息失败: {me_response.status_code}")
                
                # 4. 测试登出
                print(f"\n4️⃣ 测试 {user_type} 用户登出")
                logout_response = client.post("/api/v1/auth/logout")
                print_response(logout_response, f"{user_type} 登出")
                
                if logout_response.status_code == 200:
                    print(f"✅ {user_type} 用户登出成功")
                else:
                    print(f"❌ {user_type} 用户登出失败")
                
                # 清除token
                client.clear_auth_token()
                
            else:
                print(f"❌ {user_type} 登录响应中没有token")
        else:
            print(f"❌ {user_type} 登录失败: {login_response.status_code}")
    
    # 5. 测试无效token访问
    print(f"\n5️⃣ 测试无效token访问")
    client.set_auth_token("invalid_token")
    invalid_response = client.get("/api/v1/auth/me")
    print_response(invalid_response, "无效token访问")
    
    if invalid_response.status_code == 401:
        print("✅ 无效token正确被拒绝")
    else:
        print("❌ 无效token验证失败")
    
    client.clear_auth_token()

def test_user_registration():
    """测试用户注册功能"""
    print(f"\n6️⃣ 测试用户注册功能")
    
    client = APIClient()
    
    # 测试用有效邀请码注册
    register_data = {
        "username": "testuser",
        "email": "testuser@test.com",
        "password": "testpass123",
        "invite_code": "USER2024"
    }
    
    register_response = client.post("/api/v1/auth/register", json=register_data)
    print_response(register_response, "用户注册")
    
    if register_response.status_code == 200:
        print("✅ 用户注册成功")
        
        # 测试新用户登录
        login_response = client.post("/api/v1/auth/login", json={
            "username": register_data["username"],
            "password": register_data["password"]
        })
        
        if login_response.status_code == 200:
            print("✅ 新用户登录成功")
        else:
            print("❌ 新用户登录失败")
    else:
        print("❌ 用户注册失败")
    
    # 测试重复用户名注册
    duplicate_response = client.post("/api/v1/auth/register", json=register_data)
    print_response(duplicate_response, "重复用户名注册")
    
    if duplicate_response.status_code == 400:
        print("✅ 重复用户名正确被拒绝")
    else:
        print("❌ 重复用户名验证失败")

if __name__ == "__main__":
    print("⚠️  请确保已执行: source venv/bin/activate")
    print("⚠️  请确保服务正在运行: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    input("按回车键继续...")
    
    try:
        test_auth_and_user()
        test_user_registration()
        print(f"\n🎉 认证和用户信息测试完成！")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()