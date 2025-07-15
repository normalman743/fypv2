#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统重置API测试工具
V3.0 模块化版本 - Reset功能
"""

import sys
import os
import time
from database import full_reset, DatabaseManager
from utils import APIClient, wait_for_service, print_response, extract_token_from_response
from config import test_config

def test_reset_system():
    """测试系统重置功能"""
    print("🔄 开始系统重置测试...")
    
    # 执行完整重置
    if not full_reset():
        print("❌ 系统重置失败")
        return False
    
    print("✅ 系统重置成功")
    return True

def verify_reset_result():
    """验证重置结果"""
    print("\n🔍 验证重置结果...")
    
    client = APIClient()
    
    # 等待服务启动
    if not wait_for_service(client):
        print("❌ 服务未启动，无法验证")
        return False
    
    # 验证健康检查
    try:
        health_response = client.get("/health")
        print_response(health_response, "健康检查")
        
        if health_response.status_code != 200:
            print("❌ 健康检查失败")
            return False
        
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False
    
    # 验证默认用户登录
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
                            expected_role = user_data["role"]
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
    print(f"\n📊 数据库状态验证...")
    db_manager = DatabaseManager()
    
    if db_manager.connect():
        try:
            # 检查用户数量
            users = db_manager.fetch_all("SELECT * FROM users")
            print(f"用户数量: {len(users)}")
            
            # 检查邀请码数量
            invite_codes = db_manager.fetch_all("SELECT * FROM invite_codes")
            print(f"邀请码数量: {len(invite_codes)}")
            
            # 检查学期数量
            semesters = db_manager.fetch_all("SELECT * FROM semesters")
            print(f"学期数量: {len(semesters)}")
            
            # 检查其他表是否为空
            other_tables = ["files", "chats", "messages", "courses", "folders"]
            for table in other_tables:
                rows = db_manager.fetch_all(f"SELECT COUNT(*) as count FROM {table}")
                count = rows[0]["count"] if rows else 0
                print(f"{table}表记录数: {count}")
            
        finally:
            db_manager.disconnect()
    
    print(f"\n✅ 验证完成，成功登录用户数: {success_count}/{len(test_config.default_users)}")
    return success_count == len(test_config.default_users)

def main():
    """主函数"""
    print("🚀 V3.0 系统重置工具")
    print("=" * 50)
    
    # 确认重置操作
    confirm = input("⚠️ 确认要重置整个系统吗？这将删除所有数据！(y/N): ")
    if confirm.lower() != 'y':
        print("❌ 操作已取消")
        return
    
    start_time = time.time()
    
    # 执行重置
    if not test_reset_system():
        print("❌ 系统重置失败")
        sys.exit(1)
    
    # 验证结果
    if verify_reset_result():
        print("✅ 系统重置验证成功")
    else:
        print("⚠️ 系统重置验证部分失败")
    
    end_time = time.time()
    print(f"\n⏱️ 总耗时: {end_time - start_time:.2f}秒")
    print("🎉 重置完成！")

if __name__ == "__main__":
    main()