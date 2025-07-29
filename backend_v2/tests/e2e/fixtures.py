"""
E2E测试的pytest fixtures
"""
import pytest
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Generator, Optional

from .api_client import CampusLLMClient, APIException
from .config import config
from .factories import (
    create_test_user, create_test_admin, create_test_semester,
    create_test_course, create_test_invite_code, UserDataFactory
)


# ===== 基础设施 Fixtures =====

@pytest.fixture(scope="session")
def api_base_url() -> str:
    """API基础URL"""
    return config.base_url


@pytest.fixture(scope="function")
def client(api_base_url: str) -> CampusLLMClient:
    """普通API客户端"""
    return CampusLLMClient(base_url=api_base_url, debug=config.debug)


@pytest.fixture(scope="function")
def admin_client(api_base_url: str) -> Generator[CampusLLMClient, None, None]:
    """管理员API客户端（自动登录）"""
    client = CampusLLMClient(base_url=api_base_url, debug=config.debug)
    
    # 尝试使用配置中的管理员账户登录
    try:
        client.login(config.admin_username, config.admin_password)
        yield client
    except APIException as e:
        # 如果登录失败，可能需要先创建管理员账户
        if config.debug:
            print(f"Admin login failed: {e}")
        # 这里可以添加创建管理员账户的逻辑
        yield client
    finally:
        if client.access_token:
            try:
                client.logout()
            except:
                pass


@pytest.fixture(scope="function")
def temp_file() -> Generator[Path, None, None]:
    """临时文件fixture"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("这是一个测试文件\n")
        f.write("用于测试文件上传功能\n")
        f.write("包含中文内容测试\n")
        temp_path = Path(f.name)
    
    yield temp_path
    
    # 清理
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture(scope="function")
def temp_image_file() -> Generator[Path, None, None]:
    """临时图片文件fixture"""
    # 创建一个简单的测试图片（1x1像素PNG）
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
        f.write(png_data)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # 清理
    if temp_path.exists():
        temp_path.unlink()


# ===== 用户相关 Fixtures =====

@pytest.fixture(scope="function")
def test_invite_code(admin_client: CampusLLMClient) -> Dict[str, Any]:
    """创建测试邀请码"""
    invite_data = create_test_invite_code()
    
    try:
        response = admin_client.create_invite_code(**invite_data)
        if response.get("success"):
            return response["data"]["invite_code"]
        else:
            pytest.skip("Failed to create test invite code")
    except APIException as e:
        pytest.skip(f"Failed to create test invite code: {e}")


@pytest.fixture(scope="function")
def test_user_data() -> Dict[str, Any]:
    """测试用户数据"""
    return create_test_user()


@pytest.fixture(scope="function")
def registered_user(client: CampusLLMClient, test_invite_code: Dict[str, Any], 
                   test_user_data: Dict[str, Any]) -> Dict[str, Any]:
    """已注册的测试用户"""
    user_data = test_user_data.copy()
    user_data["invite_code"] = test_invite_code["code"]
    
    try:
        response = client.register(**user_data)
        if response.get("success"):
            # 返回用户数据和注册响应
            return {
                "user_data": user_data,
                "response": response,
                "user_info": response["data"]["user"]
            }
        else:
            pytest.skip("Failed to register test user")
    except APIException as e:
        pytest.skip(f"Failed to register test user: {e}")


@pytest.fixture(scope="function")
def verified_user(client: CampusLLMClient, registered_user: Dict[str, Any]) -> Dict[str, Any]:
    """已验证邮箱的测试用户"""
    user_data = registered_user["user_data"]
    
    try:
        # 在测试环境中，我们可能需要使用固定的验证码
        # 或者模拟邮箱验证过程
        verify_response = client.verify_email(user_data["email"], "123456")
        
        if verify_response.get("success"):
            registered_user["verified"] = True
            registered_user["verify_response"] = verify_response
            return registered_user
        else:
            # 如果验证失败，仍然返回未验证的用户
            registered_user["verified"] = False
            return registered_user
    except APIException:
        # 验证失败，返回未验证的用户
        registered_user["verified"] = False
        return registered_user


@pytest.fixture(scope="function")
def logged_in_user(client: CampusLLMClient, verified_user: Dict[str, Any]) -> Dict[str, Any]:
    """已登录的测试用户"""
    user_data = verified_user["user_data"]
    
    try:
        login_response = client.login(user_data["username"], user_data["password"])
        if login_response.get("success"):
            verified_user["logged_in"] = True
            verified_user["login_response"] = login_response
            verified_user["access_token"] = login_response["data"]["access_token"]
            return verified_user
        else:
            pytest.skip("Failed to login test user")
    except APIException as e:
        pytest.skip(f"Failed to login test user: {e}")


@pytest.fixture(scope="function")
def another_user(client: CampusLLMClient, test_invite_code: Dict[str, Any]) -> Dict[str, Any]:
    """另一个测试用户（用于测试权限隔离）"""
    user_data = create_test_user()
    user_data["invite_code"] = test_invite_code["code"]
    
    try:
        response = client.register(**user_data)
        if response.get("success"):
            # 尝试登录
            login_response = client.login(user_data["username"], user_data["password"])
            return {
                "user_data": user_data,
                "register_response": response,
                "login_response": login_response,
                "user_info": response["data"]["user"]
            }
        else:
            pytest.skip("Failed to register another test user")
    except APIException as e:
        pytest.skip(f"Failed to register another test user: {e}")


# ===== 课程相关 Fixtures =====

@pytest.fixture(scope="function")
def test_semester(admin_client: CampusLLMClient) -> Dict[str, Any]:
    """测试学期"""
    semester_data = create_test_semester()
    
    try:
        response = admin_client.create_semester(**semester_data)
        if response.get("success"):
            return {
                "data": semester_data,
                "response": response,
                "semester": {
                    "id": response["data"]["semester"]["id"],
                    **semester_data
                }
            }
        else:
            pytest.skip("Failed to create test semester")
    except APIException as e:
        pytest.skip(f"Failed to create test semester: {e}")


@pytest.fixture(scope="function")
def test_course(client: CampusLLMClient, logged_in_user: Dict[str, Any], 
               test_semester: Dict[str, Any]) -> Dict[str, Any]:
    """测试课程"""
    course_data = create_test_course(test_semester["semester"]["id"])
    
    try:
        response = client.create_course(**course_data)
        if response.get("success"):
            return {
                "data": course_data,
                "response": response,
                "course": {
                    "id": response["data"]["course"]["id"],
                    **course_data
                }
            }
        else:
            pytest.skip("Failed to create test course")
    except APIException as e:
        pytest.skip(f"Failed to create test course: {e}")


@pytest.fixture(scope="function")
def test_folder(client: CampusLLMClient, test_course: Dict[str, Any]) -> Dict[str, Any]:
    """测试文件夹"""
    folder_data = {
        "name": "测试文件夹",
        "folder_type": "lecture"
    }
    
    try:
        response = client.create_folder(test_course["course"]["id"], **folder_data)
        if response.get("success"):
            return {
                "data": folder_data,
                "response": response,
                "folder": {
                    "id": response["data"]["folder"]["id"],
                    **folder_data
                }
            }
        else:
            pytest.skip("Failed to create test folder")
    except APIException as e:
        pytest.skip(f"Failed to create test folder: {e}")


# ===== 聊天相关 Fixtures =====

@pytest.fixture(scope="function")
def test_chat(client: CampusLLMClient, logged_in_user: Dict[str, Any], 
              test_course: Dict[str, Any]) -> Dict[str, Any]:
    """测试聊天"""
    chat_data = {
        "title": "测试聊天",
        "chat_type": "course",
        "course_id": test_course["course"]["id"],
        "ai_model": "gpt-3.5-turbo",
        "rag_enabled": True,
        "context_mode": "default"
    }
    
    try:
        response = client.create_chat(**chat_data)
        if response.get("success"):
            return {
                "data": chat_data,
                "response": response,
                "chat": response["data"]
            }
        else:
            pytest.skip("Failed to create test chat")
    except APIException as e:
        pytest.skip(f"Failed to create test chat: {e}")


# ===== 清理 Fixtures =====

@pytest.fixture(autouse=True)
def cleanup_after_test(request):
    """测试后自动清理"""
    yield
    
    if config.cleanup_after_test:
        # 这里可以添加清理逻辑
        # 例如删除创建的测试数据
        pass


# ===== 辅助函数 =====

def skip_if_api_unavailable(client: CampusLLMClient):
    """如果API不可用则跳过测试"""
    try:
        client.health_check()
    except APIException:
        pytest.skip("API server is not available")


# ===== 标记 =====

# 用于标记不同类型的测试
pytest_plugins = []

# 自定义标记
def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: 冒烟测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "security: 安全测试")
    config.addinivalue_line("markers", "performance: 性能测试")
    config.addinivalue_line("markers", "admin: 需要管理员权限的测试")
    config.addinivalue_line("markers", "auth: 认证相关测试")
    config.addinivalue_line("markers", "course: 课程相关测试")
    config.addinivalue_line("markers", "storage: 存储相关测试")
    config.addinivalue_line("markers", "chat: 聊天相关测试")
    config.addinivalue_line("markers", "ai: AI相关测试")