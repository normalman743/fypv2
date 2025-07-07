"""
测试管理员登录
"""
from utils import APIClient, print_response, check_response, extract_data
from config import ADMIN_USER, TEST_USER

def test_admin_login():
    """测试管理员登录"""
    client = APIClient()
    
    print("🔐 测试管理员登录")
    login_data = {
        "username": ADMIN_USER["username"],
        "password": ADMIN_USER["password"]   
    }
    
    response = client.post("/auth/login", login_data)
    print_response(response, "管理员登录")
    
    if check_response(response):
        data = extract_data(response)
        if data and "access_token" in data:
            print("✅ 管理员登录成功")
            return data["access_token"]
        else:
            print("❌ 登录响应中没有access_token")
    else:
        print("❌ 管理员登录失败")
    return None

def test_user_login():
    """测试普通用户登录"""
    client = APIClient()
    
    print("\n👤 测试普通用户登录")
    login_data = {
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]   
    }
    
    response = client.post("/auth/login", login_data)
    print_response(response, "普通用户登录")
    
    if check_response(response):
        data = extract_data(response)
        if data and "access_token" in data:
            print("✅ 普通用户登录成功")
            return data["access_token"]
        else:
            print("❌ 登录响应中没有access_token")
    else:
        print("❌ 普通用户登录失败")
    return None

if __name__ == "__main__":
    admin_token = test_admin_login()
    user_token = test_user_login()
    
    print(f"\n📊 登录测试结果:")
    print(f"管理员token: {'✅ 有效' if admin_token else '❌ 无效'}")
    print(f"用户token: {'✅ 有效' if user_token else '❌ 无效'}")
