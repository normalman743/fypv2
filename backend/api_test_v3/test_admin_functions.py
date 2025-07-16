#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理员功能测试 - 基于api_admin.md文档
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

def test_invite_code_management():
    """测试邀请码管理 - 基于api_admin.md"""
    print("🎫 邀请码管理测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取管理员权限
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ 无法获取管理员token，跳过测试")
        return
    
    client.set_auth_token(admin_token)
    
    # 1. 创建邀请码 - POST /api/v1/invite-codes
    print("\n1️⃣ 创建邀请码")
    future_date = datetime.now() + timedelta(days=30)
    create_data = {
        "description": "学生注册专用",
        "expires_at": future_date.isoformat() + "Z"
    }
    
    create_response = client.post("/api/v1/invite-codes", json=create_data)
    print_response(create_response, "创建邀请码")
    
    invite_code_id = None
    if create_response.status_code == 200:
        result = create_response.json()
        if result.get("success"):
            invite_code_id = result["data"]["invite_code"]["id"]
            print(f"✅ 创建邀请码成功，ID: {invite_code_id}")
    
    # 2. 获取邀请码列表 - GET /api/v1/invite-codes
    print("\n2️⃣ 获取邀请码列表")
    list_response = client.get("/api/v1/invite-codes")
    print_response(list_response, "获取邀请码列表")
    
    # 3. 更新邀请码 - PUT /api/v1/invite-codes/{id}
    if invite_code_id:
        print(f"\n3️⃣ 更新邀请码 (ID: {invite_code_id})")
        update_data = {
            "description": "新描述",
            "expires_at": "2026-01-01T00:00:00Z"
        }
        update_response = client.put(f"/api/v1/invite-codes/{invite_code_id}", json=update_data)
        print_response(update_response, "更新邀请码")
    
    # 4. 删除邀请码 - DELETE /api/v1/invite-codes/{id}
    if invite_code_id:
        print(f"\n4️⃣ 删除邀请码 (ID: {invite_code_id})")
        delete_response = client.delete(f"/api/v1/invite-codes/{invite_code_id}")
        print_response(delete_response, "删除邀请码")

def test_system_config():
    """测试系统配置管理 - 基于api_admin.md"""
    print("\n⚙️ 系统配置测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取管理员权限
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ 无法获取管理员token，跳过测试")
        return
    
    client.set_auth_token(admin_token)
    
    # 1. 获取系统配置 - GET /api/v1/system/config
    print("\n1️⃣ 获取系统配置")
    config_response = client.get("/api/v1/system/config")
    print_response(config_response, "获取系统配置")
    
    # 2. 更新系统配置 - PUT /api/v1/system/config
    print("\n2️⃣ 更新系统配置")
    config_data = {
        "max_file_size": 100 * 1024 * 1024,  # 100MB
        "allowed_extensions": "pdf,doc,docx,txt,md",
        "rag_enabled": True
    }
    
    update_config_response = client.put("/api/v1/system/config", json=config_data)
    print_response(update_config_response, "更新系统配置")

def test_audit_logs():
    """测试审计日志 - 基于api_admin.md"""
    print("\n📋 审计日志测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取管理员权限
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ 无法获取管理员token，跳过测试")
        return
    
    client.set_auth_token(admin_token)
    
    # 1. 获取审计日志 - GET /api/v1/audit-logs
    print("\n1️⃣ 获取审计日志")
    audit_response = client.get("/api/v1/audit-logs")
    print_response(audit_response, "获取审计日志")
    
    # 2. 按操作类型筛选
    print("\n2️⃣ 按操作类型筛选")
    filter_response = client.get("/api/v1/audit-logs", params={"action": "login"})
    print_response(filter_response, "筛选审计日志")
    
    # 3. 按用户筛选
    print("\n3️⃣ 按用户筛选")
    user_filter_response = client.get("/api/v1/audit-logs", params={"user_id": 1})
    print_response(user_filter_response, "按用户筛选")
    
    # 4. 按时间范围筛选
    print("\n4️⃣ 按时间范围筛选")
    today = datetime.now().date()
    time_filter_response = client.get("/api/v1/audit-logs", params={
        "start_date": today.isoformat(),
        "end_date": today.isoformat()
    })
    print_response(time_filter_response, "按时间筛选")

if __name__ == "__main__":
    print("⚠️  请确保已执行: source venv/bin/activate")
    print("⚠️  请确保服务正在运行: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("⚠️  此测试需要管理员权限")
    print("📋 基于 api_admin.md 文档的测试")
    input("按回车键继续...")
    
    try:
        test_invite_code_management()
        test_system_config()
        test_audit_logs()
        print(f"\n🎉 管理员功能测试完成！")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()