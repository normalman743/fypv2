"""
认证API测试
测试用户注册、登录、个人信息等功能
"""
from utils import APIClient, print_response, check_response, extract_data
from config import TEST_USER
import time

def test_register(client: APIClient):
    """测试用户注册"""
    # 使用时间戳确保用户名唯一
    user_data = {
        "username": f"{TEST_USER['username']}",
        "email": f"{TEST_USER['email']}",
        "password": TEST_USER["password"],
        "invite_code": TEST_USER["invite_code"]
    }
    
    response = client.post("/auth/register", user_data)
    print_response(response, "用户注册")
    
    if check_response(response):
        return user_data
    return None

def test_login(client: APIClient, user_data: dict):
    """测试用户登录"""
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    
    response = client.post("/auth/login", login_data)
    print_response(response, "用户登录")
    
    if check_response(response):
        data = extract_data(response)
        if data and "access_token" in data:
            client.set_token(data["access_token"])
            return data["access_token"]
    return None

def test_get_me(client: APIClient):
    """测试获取当前用户信息"""
    response = client.get("/auth/me")
    print_response(response, "获取当前用户信息")
    return check_response(response)

def test_update_me(client: APIClient):
    """测试更新用户信息"""
    update_data = {
        "preferred_language": "en",
        "preferred_theme": "dark"
    }
    
    response = client.put("/auth/me", update_data)
    print_response(response, "更新用户信息")
    return check_response(response)

def test_logout(client: APIClient):
    """测试用户登出"""
    response = client.post("/auth/logout")
    print_response(response, "用户登出")
    return check_response(response)

def test_unauthorized_access(client: APIClient):
    """测试未授权访问"""
    # 清除token
    client.set_token("invalid_token")
    response = client.get("/auth/me")
    print_response(response, "未授权访问测试")
    return check_response(response, 401)

def main():
    """运行认证测试"""
    print("🔐 开始认证API测试")
    
    client = APIClient()
    user_data = None
    token = None
    
    tests = [
        ("用户注册", lambda: test_register(client)),
        ("用户登录", lambda: test_login(client, user_data) if user_data else False),
        ("获取用户信息", lambda: test_get_me(client) if token else False),
        ("更新用户信息", lambda: test_update_me(client) if token else False),
        ("用户登出", lambda: test_logout(client) if token else False),
        ("未授权访问", lambda: test_unauthorized_access(client))
    ]
    
    passed = 0
    total = len(tests)
    
    for i, (test_name, test_func) in enumerate(tests):
        try:
            if i == 0:  # 注册测试
                result = test_func()
                if result:
                    user_data = result
                    passed += 1
                    print(f"✅ {test_name} - 通过")
                else:
                    print(f"❌ {test_name} - 失败")
            elif i == 1:  # 登录测试
                result = test_func()
                if result:
                    token = result
                    passed += 1
                    print(f"✅ {test_name} - 通过")
                else:
                    print(f"❌ {test_name} - 失败")
            else:  # 其他测试
                if test_func():
                    passed += 1
                    print(f"✅ {test_name} - 通过")
                else:
                    print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
    
    print(f"\n📊 认证测试结果: {passed}/{total} 通过")
    return passed == total

if __name__ == "__main__":
    main()