#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理员功能测试
使用前请先: source venv/bin/activate
运行: python api_test_v3/test_admin_functions.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import APIClient, print_response, extract_token_from_response
from config import test_config
import logging
from datetime import datetime, timedelta

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_admin_token():
    """获取管理员token"""
    client = APIClient()
    admin_data = test_config.default_users["admin"]
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": admin_data["username"],
        "password": admin_data["password"]
    })
    
    if login_response.status_code == 200:
        token = extract_token_from_response(login_response)
        if token:
            return token
    return None

def test_user_management():
    """测试用户管理"""
    print("👥 用户管理测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取管理员权限
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ 无法获取管理员token，跳过测试")
        return
    
    client.set_auth_token(admin_token)
    
    # 1. 获取所有用户
    print("\n1️⃣ 获取所有用户")
    users_response = client.get("/api/v1/admin/users")
    print_response(users_response, "获取用户列表")
    
    user_id = None
    if users_response.status_code == 200:
        users_data = users_response.json()
        if users_data.get("success") and users_data["data"]:
            # 找到一个非管理员用户
            for user in users_data["data"]:
                if user.get("role") != "admin":
                    user_id = user["id"]
                    break
    
    # 2. 获取特定用户信息
    if user_id:
        print(f"\n2️⃣ 获取用户信息 (ID: {user_id})")
        user_detail_response = client.get(f"/api/v1/admin/users/{user_id}")
        print_response(user_detail_response, "用户详情")
    
    # 3. 更新用户信息
    if user_id:
        print(f"\n3️⃣ 更新用户信息")
        update_data = {
            "role": "admin",
            "balance": 200.0,
            "is_active": True
        }
        update_response = client.put(f"/api/v1/admin/users/{user_id}", json=update_data)
        print_response(update_response, "更新用户")
        
        # 恢复用户角色
        restore_data = {
            "role": "user",
            "balance": 50.0
        }
        restore_response = client.put(f"/api/v1/admin/users/{user_id}", json=restore_data)
        print_response(restore_response, "恢复用户角色")
    
    # 4. 搜索用户
    print(f"\n4️⃣ 搜索用户")
    search_response = client.get("/api/v1/admin/users", params={"search": "admin"})
    print_response(search_response, "搜索用户")
    
    # 5. 按角色筛选用户
    print(f"\n5️⃣ 按角色筛选用户")
    filter_response = client.get("/api/v1/admin/users", params={"role": "user"})
    print_response(filter_response, "筛选用户")
    
    # 6. 禁用/启用用户
    if user_id:
        print(f"\n6️⃣ 禁用用户")
        disable_response = client.put(f"/api/v1/admin/users/{user_id}", json={"is_active": False})
        print_response(disable_response, "禁用用户")
        
        print(f"\n7️⃣ 启用用户")
        enable_response = client.put(f"/api/v1/admin/users/{user_id}", json={"is_active": True})
        print_response(enable_response, "启用用户")

def test_invite_code_management():
    """测试邀请码管理"""
    print("\n🎫 邀请码管理测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取管理员权限
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ 无法获取管理员token，跳过测试")
        return
    
    client.set_auth_token(admin_token)
    
    # 1. 获取所有邀请码
    print("\n1️⃣ 获取所有邀请码")
    codes_response = client.get("/api/v1/admin/invite-codes")
    print_response(codes_response, "获取邀请码列表")
    
    # 2. 创建新邀请码
    print("\n2️⃣ 创建新邀请码")
    future_date = datetime.now() + timedelta(days=30)
    code_data = {
        "code": "TEST2024",
        "description": "测试邀请码",
        "expires_at": future_date.isoformat(),
        "is_active": True
    }
    
    create_code_response = client.post("/api/v1/admin/invite-codes", json=code_data)
    print_response(create_code_response, "创建邀请码")
    
    code_id = None
    if create_code_response.status_code == 200:
        result = create_code_response.json()
        if result.get("success"):
            code_id = result["data"]["id"]
            print(f"✅ 创建邀请码成功，ID: {code_id}")
    
    # 3. 获取特定邀请码信息
    if code_id:
        print(f"\n3️⃣ 获取邀请码信息 (ID: {code_id})")
        code_detail_response = client.get(f"/api/v1/admin/invite-codes/{code_id}")
        print_response(code_detail_response, "邀请码详情")
    
    # 4. 更新邀请码信息
    if code_id:
        print(f"\n4️⃣ 更新邀请码信息")
        update_data = {
            "description": "更新后的测试邀请码",
            "is_active": False
        }
        update_response = client.put(f"/api/v1/admin/invite-codes/{code_id}", json=update_data)
        print_response(update_response, "更新邀请码")
    
    # 5. 搜索邀请码
    print(f"\n5️⃣ 搜索邀请码")
    search_response = client.get("/api/v1/admin/invite-codes", params={"search": "TEST"})
    print_response(search_response, "搜索邀请码")
    
    # 6. 按状态筛选邀请码
    print(f"\n6️⃣ 按状态筛选邀请码")
    filter_response = client.get("/api/v1/admin/invite-codes", params={"is_active": True})
    print_response(filter_response, "筛选邀请码")
    
    # 7. 删除邀请码
    if code_id:
        print(f"\n7️⃣ 删除邀请码")
        delete_response = client.delete(f"/api/v1/admin/invite-codes/{code_id}")
        print_response(delete_response, "删除邀请码")

def test_system_management():
    """测试系统管理"""
    print("\n⚙️ 系统管理测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取管理员权限
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ 无法获取管理员token，跳过测试")
        return
    
    client.set_auth_token(admin_token)
    
    # 1. 获取系统统计信息
    print("\n1️⃣ 获取系统统计信息")
    stats_response = client.get("/api/v1/admin/stats")
    print_response(stats_response, "系统统计")
    
    # 2. 获取系统配置
    print("\n2️⃣ 获取系统配置")
    config_response = client.get("/api/v1/system/config")
    print_response(config_response, "系统配置")
    
    # 3. 更新系统配置
    print("\n3️⃣ 更新系统配置")
    config_data = {
        "max_file_size": 100 * 1024 * 1024,  # 100MB
        "allowed_extensions": "pdf,doc,docx,txt,md,py,js,html,json,csv,xlsx",
        "rag_enabled": True
    }
    
    update_config_response = client.put("/api/v1/system/config", json=config_data)
    print_response(update_config_response, "更新系统配置")
    
    # 4. 获取系统日志
    print("\n4️⃣ 获取系统日志")
    logs_response = client.get("/api/v1/admin/system/logs", params={"limit": 10})
    print_response(logs_response, "系统日志")
    
    # 5. 清理系统缓存
    print("\n5️⃣ 清理系统缓存")
    cache_response = client.post("/api/v1/admin/system/clear-cache")
    print_response(cache_response, "清理缓存")

def test_audit_logs():
    """测试审计日志"""
    print("\n📋 审计日志测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取管理员权限
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ 无法获取管理员token，跳过测试")
        return
    
    client.set_auth_token(admin_token)
    
    # 1. 获取审计日志
    print("\n1️⃣ 获取审计日志")
    audit_response = client.get("/api/v1/audit-logs")
    print_response(audit_response, "审计日志")
    
    # 2. 按操作类型筛选
    print("\n2️⃣ 按操作类型筛选")
    filter_response = client.get("/api/v1/admin/audit-logs", params={"action": "login"})
    print_response(filter_response, "筛选审计日志")
    
    # 3. 按用户筛选
    print("\n3️⃣ 按用户筛选")
    user_filter_response = client.get("/api/v1/admin/audit-logs", params={"user_id": 1})
    print_response(user_filter_response, "按用户筛选")
    
    # 4. 按时间范围筛选
    print("\n4️⃣ 按时间范围筛选")
    today = datetime.now().date()
    time_filter_response = client.get("/api/v1/admin/audit-logs", params={
        "start_date": today.isoformat(),
        "end_date": today.isoformat()
    })
    print_response(time_filter_response, "按时间筛选")

def test_database_management():
    """测试数据库管理"""
    print("\n🗄️ 数据库管理测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取管理员权限
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ 无法获取管理员token，跳过测试")
        return
    
    client.set_auth_token(admin_token)
    
    # 1. 获取数据库统计
    print("\n1️⃣ 获取数据库统计")
    db_stats_response = client.get("/api/v1/admin/database/stats")
    print_response(db_stats_response, "数据库统计")
    
    # 2. 数据库健康检查
    print("\n2️⃣ 数据库健康检查")
    health_response = client.get("/api/v1/admin/database/health")
    print_response(health_response, "数据库健康")
    
    # 3. 获取表信息
    print("\n3️⃣ 获取表信息")
    tables_response = client.get("/api/v1/admin/database/tables")
    print_response(tables_response, "数据库表")

def test_file_management():
    """测试文件管理"""
    print("\n📁 文件管理测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取管理员权限
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ 无法获取管理员token，跳过测试")
        return
    
    client.set_auth_token(admin_token)
    
    # 1. 获取所有文件（管理员视图）
    print("\n1️⃣ 获取所有文件（管理员视图）")
    files_response = client.get("/api/v1/admin/files")
    print_response(files_response, "管理员文件列表")
    
    # 2. 获取存储统计
    print("\n2️⃣ 获取存储统计")
    storage_stats_response = client.get("/api/v1/admin/files/storage-stats")
    print_response(storage_stats_response, "存储统计")
    
    # 3. 清理无效文件
    print("\n3️⃣ 清理无效文件")
    cleanup_response = client.post("/api/v1/admin/files/cleanup")
    print_response(cleanup_response, "清理文件")

if __name__ == "__main__":
    print("⚠️  请确保已执行: source venv/bin/activate")
    print("⚠️  请确保服务正在运行: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("⚠️  此测试需要管理员权限")
    input("按回车键继续...")
    
    try:
        test_user_management()
        test_invite_code_management()
        test_system_management()
        test_audit_logs()
        test_database_management()
        test_file_management()
        print(f"\n🎉 管理员功能测试完成！")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()