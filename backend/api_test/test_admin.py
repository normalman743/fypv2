"""
管理员API测试
测试邀请码管理、系统配置等管理员功能
"""
from utils import APIClient, print_response, check_response, extract_data
from config import ADMIN_USER, TEST_USER
from datetime import datetime, timedelta
import time

def setup_admin_auth(client: APIClient):
    """设置管理员认证"""
    
    account = {
        "username": ADMIN_USER["username"],
        "password": ADMIN_USER["password"]
    }

    response = client.post("/auth/login", account)
    if check_response(response):
        data = extract_data(response)
        if data and "access_token" in data:
            client.set_token(data["access_token"])
            print(f"✅ 管理员登录成功: {account['username']}")
            return True
    
    print("❌ 无法使用管理员账号登录")
    return False

def test_get_invite_codes(client: APIClient):
    """测试获取邀请码列表"""
    response = client.get("/invite-codes")
    print_response(response, "获取邀请码列表")
    
    if check_response(response):
        data = extract_data(response)
        return data.get("invite_codes", []) if data else []
    return []

def test_create_invite_code(client: APIClient):
    """测试创建邀请码"""
    timestamp = str(int(time.time()))
    # 设置过期时间为30天后
    expires_at = (datetime.now() + timedelta(days=30)).isoformat()
    
    invite_data = {
        "description": f"API测试邀请码 - {timestamp}",
        "expires_at": expires_at
    }
    
    response = client.post("/invite-codes", invite_data)
    print_response(response, "创建邀请码")
    
    if check_response(response):
        data = extract_data(response)
        return data.get("invite_code") if data else None
    return None

def test_update_invite_code(client: APIClient, invite_code_id: int):
    """测试更新邀请码"""
    update_data = {
        "description": "更新后的邀请码描述",
        "is_active": True
    }
    
    response = client.put(f"/invite-codes/{invite_code_id}", update_data)
    print_response(response, "更新邀请码")
    return check_response(response)

def test_delete_invite_code(client: APIClient, invite_code_id: int):
    """测试删除邀请码"""
    response = client.delete(f"/invite-codes/{invite_code_id}")
    print_response(response, "删除邀请码")
    return check_response(response)

def test_get_system_config(client: APIClient):
    """测试获取系统配置"""
    response = client.get("/system/config")
    print_response(response, "获取系统配置")
    return check_response(response)

def test_update_system_config(client: APIClient):
    """测试更新系统配置"""
    config_data = {
        "max_file_size": 10485760,  # 10MB
        "allowed_file_types": [".pdf", ".txt", ".docx"],
        "ai_model": "gpt-3.5-turbo",
        "max_tokens": 4000
    }
    
    response = client.put("/system/config", config_data)
    print_response(response, "更新系统配置")
    return check_response(response)

def test_get_audit_logs(client: APIClient):
    """测试获取审计日志"""
    params = {
        "limit": 10,
        "skip": 0
    }
    
    response = client.get("/audit-logs", params)
    print_response(response, "获取审计日志")
    return check_response(response)

def test_get_filtered_audit_logs(client: APIClient):
    """测试获取过滤后的审计日志"""
    params = {
        "action": "login",
        "limit": 5,
        "skip": 0
    }
    
    response = client.get("/audit-logs", params)
    print_response(response, "获取过滤审计日志")
    return check_response(response)

def main():
    """运行管理员API测试"""
    print("👑 开始管理员API测试")
    
    client = APIClient()
    
    # 尝试管理员认证
    if not setup_admin_auth(client):
        print("❌ 无法获取管理员认证，跳过管理员测试")
        return False
    
    passed = 0
    total = 0
    
    # 测试邀请码管理
    print("\n--- 测试邀请码管理功能 ---")
    total += 1
    invite_codes = test_get_invite_codes(client)
    if invite_codes is not None:
        passed += 1
        print("✅ 获取邀请码列表 - 通过")
        print(f"🎫 当前有 {len(invite_codes)} 个邀请码")
    else:
        print("❌ 获取邀请码列表 - 失败")
    
    # 测试创建邀请码
    total += 1
    new_invite_code = test_create_invite_code(client)
    if new_invite_code:
        passed += 1
        print("✅ 创建邀请码 - 通过")
        print(f"🆕 新邀请码: {new_invite_code.get('code', 'N/A')}")
        
        invite_code_id = new_invite_code.get("id")
        if invite_code_id:
            # 测试更新邀请码
            total += 1
            if test_update_invite_code(client, invite_code_id):
                passed += 1
                print("✅ 更新邀请码 - 通过")
            else:
                print("❌ 更新邀请码 - 失败")
            
            # 测试删除邀请码
            total += 1
            if test_delete_invite_code(client, invite_code_id):
                passed += 1
                print("✅ 删除邀请码 - 通过")
            else:
                print("❌ 删除邀请码 - 失败")
    else:
        print("❌ 创建邀请码 - 失败")
    
    # 测试系统配置管理
    print("\n--- 测试系统配置功能 ---")
    total += 1
    if test_get_system_config(client):
        passed += 1
        print("✅ 获取系统配置 - 通过")
    else:
        print("❌ 获取系统配置 - 失败")
    
    total += 1
    if test_update_system_config(client):
        passed += 1
        print("✅ 更新系统配置 - 通过")
    else:
        print("❌ 更新系统配置 - 失败")
    
    # 测试审计日志
    print("\n--- 测试审计日志功能 ---")
    total += 1
    if test_get_audit_logs(client):
        passed += 1
        print("✅ 获取审计日志 - 通过")
    else:
        print("❌ 获取审计日志 - 失败")
    
    total += 1
    if test_get_filtered_audit_logs(client):
        passed += 1
        print("✅ 获取过滤审计日志 - 通过")
    else:
        print("❌ 获取过滤审计日志 - 失败")
    
    print(f"\n📊 管理员API测试结果: {passed}/{total} 通过")
    return passed == total if total > 0 else False

if __name__ == "__main__":
    main()