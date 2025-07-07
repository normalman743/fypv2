"""
运行所有API测试的主脚本
"""
import sys
import importlib
import time
from datetime import datetime

# 测试模块列表
TEST_MODULES = [
    ("基础API测试", "test_basic"),
    ("认证API测试", "test_auth"),
    ("课程管理API测试", "test_courses"),
    ("文件管理API测试", "test_files"),
    ("聊天API测试", "test_chats"),
    ("管理员API测试", "test_admin")
]

def run_single_test(module_name: str, test_name: str):
    """运行单个测试模块"""
    try:
        print(f"🚀 开始运行: {test_name}")
        print(f"{'='*60}")
        
        # 动态导入测试模块
        module = importlib.import_module(module_name)
        
        # 运行测试
        result = module.main()
        
        print(f"\n{'='*60}")
        if result:
            print(f"✅ {test_name} - 全部通过")
        else:
            print(f"❌ {test_name} - 部分失败")
        print(f"{'='*60}")
        
        return result
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"💥 {test_name} - 运行异常: {e}")
        print(f"{'='*60}")
        return False

def main():
    """运行所有测试"""
    print("🎯 API自动化测试套件")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 API地址: http://127.0.0.1:8000")
    
    results = {}
    total_passed = 0
    total_tests = len(TEST_MODULES)
    
    # 运行所有测试
    for test_name, module_name in TEST_MODULES:
        success = run_single_test(module_name, test_name)
        results[test_name] = success
        if success:
            total_passed += 1
    
    # 打印总结
    print(f"\n{'🎊' if total_passed == total_tests else '📊'} 测试总结报告")
    print(f"{'='*60}")
    print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📈 总体结果: {total_passed}/{total_tests} 测试套件通过")
    print(f"{'='*60}")
    
    # 详细结果
    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} {test_name}")
    
    print(f"{'='*60}")
    
    if total_passed == total_tests:
        print("🎉 恭喜！所有API测试都通过了！")
        return 0
    else:
        print(f"⚠️  有 {total_tests - total_passed} 个测试套件失败，请检查API实现")
        return 1

if __name__ == "__main__":
    sys.exit(main())