"""
Campus LLM System v2 - 全局测试配置
主要的pytest配置和fixture定义
"""
import os
import sys
import asyncio
import pytest
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def event_loop():
    """为整个测试会话创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_database_url():
    """测试数据库URL配置"""
    # 默认使用SQLite内存数据库进行测试
    return os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture(scope="session") 
def test_config():
    """测试环境配置"""
    return {
        "TESTING": True,
        "DATABASE_URL": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        "UPLOAD_DIR": "/tmp/test_uploads",
        "MAX_FILE_SIZE": 10 * 1024 * 1024,  # 10MB for testing
    }


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """自动清理临时文件"""
    yield
    # 清理测试过程中创建的临时文件
    import tempfile
    import shutil
    temp_dir = Path(tempfile.gettempdir())
    for item in temp_dir.glob("test_*"):
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        except (OSError, PermissionError):
            # 忽略清理失败的文件
            pass


def pytest_configure(config):
    """pytest配置钩子"""
    # 确保测试输出目录存在
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # 设置测试环境变量
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "INFO"


def pytest_collection_modifyitems(config, items):
    """修改测试收集行为"""
    # 为没有标记的测试自动添加标记
    for item in items:
        # 如果没有任何标记，添加默认标记
        if not list(item.iter_markers()):
            item.add_marker(pytest.mark.unmarked)
        
        # 根据文件路径自动添加标记
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # 根据测试名称自动添加标记
        if "smoke" in item.name or "test_complete" in item.name:
            item.add_marker(pytest.mark.smoke)
        if "security" in item.name or "auth" in item.name:
            item.add_marker(pytest.mark.security)


# HTML报告相关的钩子（需要安装pytest-html插件）
# def pytest_html_report_title(report):
#     """自定义HTML报告标题"""
#     report.title = "Campus LLM System v2 - Test Report"
# 
# 
# def pytest_html_results_summary(prefix, summary, postfix):
#     """自定义HTML报告摘要"""
#     prefix.extend([f"<p>Campus LLM System v2 测试报告</p>"])
#     postfix.extend([f"<p>测试环境: {os.getenv('TEST_ENV', 'local')}</p>"])


# 测试失败时的钩子
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """生成测试报告时的钩子"""
    outcome = yield
    rep = outcome.get_result()
    
    # 为失败的测试添加额外信息
    if rep.when == "call" and rep.failed:
        # 可以在这里添加失败测试的诊断信息
        pass
    
    return rep