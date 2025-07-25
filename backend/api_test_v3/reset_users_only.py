#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仅重置用户数据工具
从 reset_system.py 中提取的用户重置功能
只重置 users 表，不影响其他数据
"""

import sys
import os
import time
from database import DatabaseManager
from utils import APIClient, wait_for_service, print_response, extract_token_from_response
from config import test_config

# 导入密码哈希函数
sys.path.append('/Users/mannormal/Downloads/fyp/backend')
from app.core.security import get_password_hash

def reset_users_only():
    """仅重置用户数据"""
    print("👥 开始重置用户数据...")
    
    db_manager = DatabaseManager()
    if not db_manager.connect():
        print("❌ 数据库连接失败")
        return False
    
    try:
        # 1. 清空 users 表
        print("🗑️  清空用户表...")
        if not db_manager.execute_query("DELETE FROM users"):
            print("❌ 清空用户表失败")
            return False
        
        # 2. 重置 users 表的自增ID
        print("🔄 重置用户表自增ID...")
        if not db_manager.execute_query("ALTER TABLE users AUTO_INCREMENT = 1"):
            print("❌ 重置用户表自增ID失败")
            return False
        
        # 3. 创建默认用户（从配置文件读取）
        print("👤 创建默认用户...")
        for user_key, user_data in test_config.default_users.items():
            username = user_data["username"]
            email = user_data["email"]
            password = user_data["password"]
            # 注意：这里直接创建为配置中指定的角色
            role = user_data.get("role", "user")
            balance = 100.00 if user_key == "admin" else 50.00
            
            # 使用与注册接口相同的密码哈希方法
            hashed_password = get_password_hash(password)
            user_query = """
            INSERT INTO users (username, email, password_hash, role, balance) 
            VALUES (%s, %s, %s, %s, %s)
            """
            if not db_manager.execute_query(user_query, (username, email, hashed_password, role, balance)):
                print(f"❌ 创建用户 {username} 失败")
                return False
            
            print(f"✅ 创建用户 {username} (邮箱: {email}, 角色: {role})")
        
        print(f"✅ 用户重置完成！")
        print(f"   - 总用户数: {len(test_config.default_users)}")
        print(f"   - 管理员: {sum(1 for u in test_config.default_users.values() if u.get('role') == 'admin')}")
        print(f"   - 普通用户: {sum(1 for u in test_config.default_users.values() if u.get('role') == 'user')}")
        return True
        
    except Exception as e:
        print(f"❌ 重置用户数据时出错: {e}")
        return False
    finally:
        db_manager.disconnect()

def verify_users():
    """验证用户重置结果"""
    print("\n🔍 验证用户重置结果...")
    
    client = APIClient()
    
    # 等待服务启动
    if not wait_for_service(client):
        print("❌ 服务未启动，无法验证")
        return False
    
    # 验证所有用户登录
    success_count = 0
    
    for user_type, user_data in test_config.default_users.items():
        print(f"\n📝 测试用户登录: {user_type}")
        
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        
        try:
            login_response = client.post("/api/v1/auth/login", json=login_data)
            print_response(login_response, f"{user_type} 登录")
            
            if login_response.status_code == 200:
                token = extract_token_from_response(login_response)
                if token:
                    success_count += 1
                    print(f"✅ {user_type} 登录成功")
                    
                    # 测试获取用户信息
                    client.set_auth_token(token)
                    me_response = client.get("/api/v1/auth/me")
                    print_response(me_response, f"{user_type} 用户信息")
                    
                    if me_response.status_code == 200:
                        user_info = me_response.json()
                        if user_info.get("success"):
                            actual_role = user_info["data"]["role"]
                            expected_role = user_data.get("role", "user")
                            if actual_role == expected_role:
                                print(f"✅ {user_type} 角色验证成功: {actual_role}")
                            else:
                                print(f"⚠️ {user_type} 角色不匹配: 期望 {expected_role}, 实际 {actual_role}")
                    
                    client.clear_auth_token()
                else:
                    print(f"❌ {user_type} 登录响应中没有token")
            else:
                print(f"❌ {user_type} 登录失败: {login_response.status_code}")
                
        except Exception as e:
            print(f"❌ {user_type} 登录测试异常: {e}")
    
    # 验证数据库状态
    print(f"\n📊 数据库用户状态验证...")
    db_manager = DatabaseManager()
    
    if db_manager.connect():
        try:
            # 检查用户数量和角色分布
            users = db_manager.fetch_all("SELECT username, email, role FROM users ORDER BY id")
            print(f"数据库中的用户:")
            admin_count = 0
            user_count = 0
            for user in users:
                role_emoji = "👑" if user["role"] == "admin" else "👤"
                print(f"  {role_emoji} {user['username']} ({user['email']}) - {user['role']}")
                if user["role"] == "admin":
                    admin_count += 1
                else:
                    user_count += 1
            
            print(f"\n📈 统计:")
            print(f"  总用户数: {len(users)}")
            print(f"  管理员: {admin_count}")
            print(f"  普通用户: {user_count}")
            
        finally:
            db_manager.disconnect()
    
    print(f"\n✅ 验证完成，成功登录用户数: {success_count}/{len(test_config.default_users)}")
    return success_count == len(test_config.default_users)

def main():
    """主函数"""
    print("👥 仅重置用户数据工具")
    print("=" * 50)
    
    # 显示操作说明
    print("⚠️  此操作将:")
    print("   - 删除所有用户数据")
    print("   - 重新创建配置文件中的默认用户")
    print("   - 不影响课程、文件、聊天等其他数据")
    print("\n🚀 开始执行（无需确认）...")
    
    start_time = time.time()
    
    # 执行重置
    if not reset_users_only():
        print("❌ 用户数据重置失败")
        sys.exit(1)
    
    # 检查后端服务是否运行
    client = APIClient()
    if wait_for_service(client, max_attempts=1):
        print("\n🔍 检测到后端服务运行，进行验证...")
        if verify_users():
            print("✅ 用户数据重置验证成功")
        else:
            print("⚠️ 用户数据重置验证部分失败")
    else:
        print("\n⚠️  后端服务未运行，跳过API验证")
        print("   如需完整验证，请启动后端服务后重新运行")
    
    end_time = time.time()
    print(f"\n⏱️ 总耗时: {end_time - start_time:.2f}秒")
    print("🎉 用户重置完成！")

if __name__ == "__main__":
    main()