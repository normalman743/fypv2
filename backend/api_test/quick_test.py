"""
V2.1统一文件系统快速验证测试
验证基础功能和新架构兼容性
"""
import requests
import time
import tempfile
import os
from config import BASE_URL, TEST_USER

def test_api_health():
    """测试API健康状态"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API服务器健康检查通过")
            return True
        else:
            print(f"❌ API健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接API服务器: {e}")
        return False

def test_basic_endpoints():
    """测试基础端点"""
    endpoints = [
        ("/", "根端点"),
        ("/docs", "API文档"),
        ("/api/v1/auth/register", "注册端点")  # 测试POST端点可访问性
    ]
    
    results = []
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            # 200或405(方法不允许)都算正常，说明端点存在
            if response.status_code in [200, 405, 422]:
                print(f"✅ {name}: 端点可访问")
                results.append(True)
            else:
                print(f"❌ {name}: 状态码 {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"❌ {name}: 连接失败 - {e}")
            results.append(False)
    
    return all(results)

def test_user_registration():
    """测试用户注册"""
    register_data = {
        "username": f"test_user_{int(time.time())}",
        "email": f"test_{int(time.time())}@example.com", 
        "password": "testpass123",
        "invite_code": "INVITE2025"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=register_data,
            timeout=10
        )
        
        print(f"📋 注册响应状态: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 用户注册成功")
            return True, register_data
        elif response.status_code == 400:
            print("⚠️  注册失败 - 可能是邀请码问题或用户已存在")
            return False, None
        else:
            print(f"❌ 注册失败: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ 注册请求失败: {e}")
        return False, None

def test_user_login():
    """测试用户登录"""
    login_data = {
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=login_data,
            timeout=10
        )
        
        print(f"📋 登录响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "access_token" in data.get("data", {}):
                token = data["data"]["access_token"]
                print("✅ 用户登录成功")
                return True, token
        
        print(f"❌ 登录失败: {response.text}")
        return False, None
        
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return False, None

def test_authenticated_request(token):
    """测试认证请求"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # 测试获取课程列表
        response = requests.get(
            f"{BASE_URL}/api/v1/courses",
            headers=headers,
            timeout=10
        )
        
        print(f"📋 认证请求状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                courses = data.get("data", {}).get("courses", [])
                print(f"✅ 认证请求成功，找到 {len(courses)} 个课程")
                return True, courses
        
        print(f"❌ 认证请求失败: {response.text}")
        return False, None
        
    except Exception as e:
        print(f"❌ 认证请求异常: {e}")
        return False, None

def test_file_upload(token, course_id=None):
    """测试文件上传"""
    if not course_id:
        print("⏭️  跳过文件上传测试（无课程ID）")
        return False
    
    # 创建测试文件
    content = "# V2.1统一文件系统测试\n\n这是一个测试文档，用于验证新的统一文件架构。\n\n## 特性\n- 统一文件表\n- 多scope支持\n- RAG集成"
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
    temp_file.write(content)
    temp_file.close()
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        with open(temp_file.name, 'rb') as f:
            files = {'file': ('test_v2_unified.md', f, 'text/markdown')}
            data = {
                'scope': 'course',
                'course_id': course_id,
                'folder_id': 1  # 假设存在folder_id=1
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/files/upload",
                data=data,
                files=files,
                headers=headers,
                timeout=30
            )
            
            print(f"📋 文件上传状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    file_data = result.get("data", {}).get("file", {})
                    file_id = file_data.get("id")
                    print(f"✅ 文件上传成功，ID: {file_id}")
                    return True, file_id
            
            print(f"❌ 文件上传失败: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ 文件上传异常: {e}")
        return False, None
    finally:
        # 清理临时文件
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

def main():
    """运行快速验证测试"""
    print("🚀 V2.1统一文件系统快速验证测试")
    print("="*50)
    
    total_tests = 0
    passed_tests = 0
    
    # 1. API健康检查
    total_tests += 1
    if test_api_health():
        passed_tests += 1
    
    # 2. 基础端点测试
    total_tests += 1
    if test_basic_endpoints():
        passed_tests += 1
    
    # 3. 用户登录测试
    total_tests += 1
    login_success, token = test_user_login()
    if login_success:
        passed_tests += 1
    
    # 4. 认证请求测试
    if token:
        total_tests += 1
        auth_success, courses = test_authenticated_request(token)
        if auth_success:
            passed_tests += 1
            
            # 5. 文件上传测试（如果有课程）
            if courses:
                total_tests += 1
                course_id = courses[0].get("id") if courses else None
                upload_success, file_id = test_file_upload(token, course_id)
                if upload_success:
                    passed_tests += 1
    
    print("\n" + "="*50)
    print(f"📊 快速验证结果: {passed_tests}/{total_tests} 测试通过")
    print(f"📈 通过率: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "无测试")
    
    if passed_tests == total_tests:
        print("🎉 恭喜！V2.1架构基础功能验证通过！")
        print("✅ 可以继续运行完整的API测试套件")
        return True
    else:
        print("⚠️  部分测试失败，请检查API实现")
        print("🔍 建议检查服务器日志和数据库连接")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)