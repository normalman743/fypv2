"""
E2E测试的pytest配置文件
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入fixtures
from .fixtures import *

# 配置pytest
def pytest_configure(config):
    """配置pytest"""
    # 注册自定义标记
    markers = [
        "smoke: 冒烟测试 - 核心功能快速验证",
        "integration: 集成测试 - 跨模块功能测试", 
        "security: 安全测试 - 权限、认证等安全相关测试",
        "performance: 性能测试 - 响应时间、并发等性能相关测试",
        "admin: 管理员测试 - 需要管理员权限的功能测试",
        "auth: 认证测试 - 用户注册、登录、权限验证等",
        "course: 课程测试 - 学期、课程管理相关测试",
        "storage: 存储测试 - 文件、文件夹管理相关测试", 
        "chat: 聊天测试 - 聊天、消息管理相关测试",
        "ai: AI测试 - AI对话、向量化等AI功能测试",
        "workflow: 工作流测试 - 完整业务流程测试"
    ]
    
    for marker in markers:
        config.addinivalue_line("markers", marker)


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    # 为冒烟测试添加特殊处理
    smoke_tests = []
    other_tests = []
    
    for item in items:
        if "smoke" in item.keywords:
            smoke_tests.append(item)
        else:
            other_tests.append(item)
    
    # 如果指定了只运行冒烟测试，则重新排序
    if config.getoption("--smoke-only"):
        items[:] = smoke_tests
    else:
        # 冒烟测试优先运行
        items[:] = smoke_tests + other_tests


def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--smoke-only",
        action="store_true",
        default=False,
        help="只运行冒烟测试"
    )
    parser.addoption(
        "--api-url",
        action="store",
        default="http://localhost:8001",
        help="API服务器地址"
    )
    parser.addoption(
        "--e2e-debug",
        action="store_true", 
        default=False,
        help="启用E2E调试模式"
    )
    parser.addoption(
        "--no-cleanup",
        action="store_true",
        default=False,
        help="测试后不清理数据"
    )


@pytest.fixture(scope="session", autouse=True)
def configure_test_environment(request):
    """配置测试环境"""
    from .config import config
    
    # 从命令行参数更新配置
    if request.config.getoption("--api-url"):
        config.base_url = request.config.getoption("--api-url")
    
    if request.config.getoption("--e2e-debug"):
        config.debug = True
    
    if request.config.getoption("--no-cleanup"):
        config.cleanup_after_test = False
    
    print(f"\n=== E2E Test Configuration ===")
    print(f"API URL: {config.base_url}")
    print(f"Debug mode: {config.debug}")
    print(f"Cleanup after test: {config.cleanup_after_test}")
    print(f"================================\n")


@pytest.fixture(scope="session")
def api_health_check(configure_test_environment):
    """测试开始前检查API健康状态"""
    from .api_client import CampusLLMClient, APIException
    from .config import config
    
    client = CampusLLMClient(base_url=config.base_url, debug=config.debug)
    
    try:
        health_response = client.health_check()
        print(f"✅ API服务器健康检查通过: {health_response}")
        return True
    except APIException as e:
        pytest.exit(f"❌ API服务器不可用: {e.message}", returncode=1)
    except Exception as e:
        pytest.exit(f"❌ 无法连接到API服务器: {str(e)}", returncode=1)


# 确保在所有测试前进行健康检查
@pytest.fixture(autouse=True, scope="session")
def ensure_api_available(api_health_check):
    """确保API可用"""
    pass


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """生成测试报告时的钩子"""
    outcome = yield
    rep = outcome.get_result()
    
    # 为失败的测试添加额外信息
    if rep.when == "call" and rep.failed:
        # 可以在这里添加失败时的调试信息
        pass


def pytest_sessionstart(session):
    """测试会话开始时的钩子"""
    print("\n🚀 Campus LLM System v2 - End-to-End测试开始")


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时的钩子"""
    if exitstatus == 0:
        print("\n✅ 所有E2E测试通过！")
    else:
        print(f"\n❌ 测试失败，退出码: {exitstatus}")


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """终端摘要报告"""
    if hasattr(terminalreporter, 'stats'):
        passed = len(terminalreporter.stats.get('passed', []))
        failed = len(terminalreporter.stats.get('failed', []))
        skipped = len(terminalreporter.stats.get('skipped', []))
        
        print(f"\n📊 E2E测试统计:")
        print(f"   ✅ 通过: {passed}")
        print(f"   ❌ 失败: {failed}")
        print(f"   ⏭️  跳过: {skipped}")
        
        if failed == 0 and passed > 0:
            print(f"\n🎉 恭喜！所有{passed}个E2E测试都通过了！")


# 测试数据清理
@pytest.fixture(autouse=True, scope="function")
def cleanup_test_data(request):
    """测试后清理数据"""
    yield  # 测试运行
    
    from .config import config
    if config.cleanup_after_test and not config.keep_test_data:
        # 这里可以添加清理逻辑
        # 例如删除测试过程中创建的数据
        pass