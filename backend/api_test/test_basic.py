"""
基础API测试
测试健康检查、根路径等基础功能
"""
import requests
from utils import APIClient, print_response, check_response
from config import BASE_URL

def test_health_check():
    """测试健康检查"""
    response = requests.get(f"{BASE_URL}/health")
    print_response(response, "健康检查")
    return check_response(response)

def test_root():
    """测试根路径"""
    response = requests.get(f"{BASE_URL}/")
    print_response(response, "根路径")
    return check_response(response)

def test_docs():
    """测试API文档"""
    response = requests.get(f"{BASE_URL}/docs")
    print_response(response, "API文档")
    return check_response(response)

def test_openapi_spec():
    """测试OpenAPI规范"""
    response = requests.get(f"{BASE_URL}/openapi.json")
    print_response(response, "OpenAPI规范")
    return check_response(response)

def main():
    """运行基础测试"""
    print("🚀 开始基础API测试")
    
    tests = [
        ("健康检查", test_health_check),
        ("根路径", test_root),
        ("API文档", test_docs),
        ("OpenAPI规范", test_openapi_spec)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
    
    print(f"\n📊 基础测试结果: {passed}/{total} 通过")
    return passed == total

if __name__ == "__main__":
    main()