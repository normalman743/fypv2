"""
E2E测试基类
提供通用的测试方法和断言
"""
import pytest
from typing import Dict, Any, Optional, List, Union
from .api_client import CampusLLMClient, APIException
from .config import config


class BaseE2ETest:
    """E2E测试基类"""
    
    # ===== 通用断言方法 =====
    
    @staticmethod
    def assert_success_response(response: Dict[str, Any], message: Optional[str] = None):
        """断言成功响应"""
        assert response is not None, "Response should not be None"
        assert response.get("success") is True, f"Response should be successful. Got: {response}"
        
        if message:
            assert message in str(response.get("message", "")), f"Expected message '{message}' not found in response"
    
    @staticmethod
    def assert_error_response(response: Dict[str, Any], expected_error: Optional[str] = None):
        """断言错误响应"""
        assert response is not None, "Response should not be None"
        assert response.get("success") is False, f"Response should indicate failure. Got: {response}"
        
        if expected_error:
            error_msg = response.get("error", "")
            assert expected_error in error_msg, f"Expected error '{expected_error}' not found in '{error_msg}'"
    
    @staticmethod
    def assert_api_exception(exception: APIException, expected_status: Optional[int] = None,
                           expected_message: Optional[str] = None):
        """断言API异常"""
        assert isinstance(exception, APIException), f"Expected APIException, got {type(exception)}"
        
        if expected_status:
            assert exception.status_code == expected_status, \
                f"Expected status {expected_status}, got {exception.status_code}"
        
        if expected_message:
            assert expected_message in exception.message, \
                f"Expected message '{expected_message}' not found in '{exception.message}'"
    
    @staticmethod
    def assert_data_structure(data: Dict[str, Any], required_fields: List[str]):
        """断言数据结构包含必需字段"""
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"
        
        for field in required_fields:
            assert field in data, f"Required field '{field}' not found in data: {list(data.keys())}"
    
    @staticmethod
    def assert_list_response(response: Dict[str, Any], data_key: str, 
                           expected_count: Optional[int] = None):
        """断言列表响应"""
        BaseE2ETest.assert_success_response(response)
        assert "data" in response, "Response should contain 'data' field"
        assert data_key in response["data"], f"Data should contain '{data_key}' field"
        
        items = response["data"][data_key]
        assert isinstance(items, list), f"Expected list, got {type(items)}"
        
        if expected_count is not None:
            assert len(items) == expected_count, \
                f"Expected {expected_count} items, got {len(items)}"
    
    @staticmethod
    def assert_pagination_info(response: Dict[str, Any]):
        """断言分页信息"""
        BaseE2ETest.assert_success_response(response)
        data = response.get("data", {})
        
        # 检查是否有分页信息
        if "pagination" in data:
            pagination = data["pagination"]
            required_fields = ["skip", "limit", "total", "has_more"]
            BaseE2ETest.assert_data_structure(pagination, required_fields)
            
            assert isinstance(pagination["skip"], int), "skip should be integer"
            assert isinstance(pagination["limit"], int), "limit should be integer"
            assert isinstance(pagination["total"], int), "total should be integer"
            assert isinstance(pagination["has_more"], bool), "has_more should be boolean"
    
    # ===== 用户相关断言 =====
    
    @staticmethod
    def assert_user_response(response: Dict[str, Any]):
        """断言用户响应结构"""
        BaseE2ETest.assert_success_response(response)
        
        if "data" in response:
            if "user" in response["data"]:
                user = response["data"]["user"]
                required_fields = ["id", "username", "email", "role"]
                BaseE2ETest.assert_data_structure(user, required_fields)
    
    @staticmethod
    def assert_login_response(response: Dict[str, Any]):
        """断言登录响应结构"""
        BaseE2ETest.assert_success_response(response)
        
        data = response.get("data", {})
        required_fields = ["access_token", "token_type", "expires_in", "user"]
        BaseE2ETest.assert_data_structure(data, required_fields)
        
        assert data["token_type"] == "bearer", "Token type should be 'bearer'"
        assert isinstance(data["expires_in"], int), "expires_in should be integer"
        assert len(data["access_token"]) > 20, "Access token should be substantial length"
    
    # ===== 管理员相关断言 =====
    
    @staticmethod
    def assert_invite_code_response(response: Dict[str, Any]):
        """断言邀请码响应结构"""
        BaseE2ETest.assert_success_response(response)
        
        data = response.get("data", {})
        if "invite_code" in data:
            invite_code = data["invite_code"]
            required_fields = ["id", "code", "is_used", "is_active", "created_at"]
            BaseE2ETest.assert_data_structure(invite_code, required_fields)
            
            assert len(invite_code["code"]) >= 8, "Invite code should be at least 8 characters"
            assert isinstance(invite_code["is_used"], bool), "is_used should be boolean"
            assert isinstance(invite_code["is_active"], bool), "is_active should be boolean"
    
    # ===== 课程相关断言 =====
    
    @staticmethod
    def assert_semester_response(response: Dict[str, Any]):
        """断言学期响应结构"""
        BaseE2ETest.assert_success_response(response)
        
        data = response.get("data", {})
        if "semester" in data:
            semester = data["semester"]
            required_fields = ["id", "name", "code", "start_date", "end_date"]
            BaseE2ETest.assert_data_structure(semester, required_fields)
        elif "semesters" in data:
            semesters = data["semesters"]
            assert isinstance(semesters, list), "semesters should be a list"
            for semester in semesters:
                required_fields = ["id", "name", "code", "start_date", "end_date"]
                BaseE2ETest.assert_data_structure(semester, required_fields)
    
    @staticmethod
    def assert_course_response(response: Dict[str, Any]):
        """断言课程响应结构"""
        BaseE2ETest.assert_success_response(response)
        
        data = response.get("data", {})
        if "course" in data:
            course = data["course"]
            required_fields = ["id", "name", "code", "semester_id"]
            BaseE2ETest.assert_data_structure(course, required_fields)
        elif "courses" in data:
            courses = data["courses"]
            assert isinstance(courses, list), "courses should be a list"
            for course in courses:
                required_fields = ["id", "name", "code", "semester_id"]
                BaseE2ETest.assert_data_structure(course, required_fields)
    
    # ===== 存储相关断言 =====
    
    @staticmethod
    def assert_folder_response(response: Dict[str, Any]):
        """断言文件夹响应结构"""
        BaseE2ETest.assert_success_response(response)
        
        data = response.get("data", {})
        if "folder" in data:
            folder = data["folder"]
            required_fields = ["id", "created_at"]
            BaseE2ETest.assert_data_structure(folder, required_fields)
        elif "folders" in data:
            folders = data["folders"]
            assert isinstance(folders, list), "folders should be a list"
            for folder in folders:
                required_fields = ["id", "name", "folder_type", "course_id"]
                BaseE2ETest.assert_data_structure(folder, required_fields)
    
    @staticmethod
    def assert_file_response(response: Dict[str, Any]):
        """断言文件响应结构"""
        BaseE2ETest.assert_success_response(response)
        
        data = response.get("data", {})
        if "file" in data:
            file_data = data["file"]
            required_fields = ["id", "original_name", "file_type", "created_at"]
            BaseE2ETest.assert_data_structure(file_data, required_fields)
        elif "files" in data:
            files = data["files"]
            assert isinstance(files, list), "files should be a list"
            for file_data in files:
                required_fields = ["id", "original_name", "file_type", "created_at"]
                BaseE2ETest.assert_data_structure(file_data, required_fields)
    
    # ===== 聊天相关断言 =====
    
    @staticmethod
    def assert_chat_response(response: Dict[str, Any]):
        """断言聊天响应结构"""
        BaseE2ETest.assert_success_response(response)
        
        data = response.get("data", {})
        if "chat" in data:
            chat = data["chat"]
            required_fields = ["id", "title", "chat_type", "ai_model"]
            BaseE2ETest.assert_data_structure(chat, required_fields)
        elif "chats" in data:
            chats = data["chats"]
            assert isinstance(chats, list), "chats should be a list"
            for chat in chats:
                required_fields = ["id", "title", "chat_type", "ai_model"]
                BaseE2ETest.assert_data_structure(chat, required_fields)
    
    @staticmethod
    def assert_message_response(response: Dict[str, Any]):
        """断言消息响应结构"""
        BaseE2ETest.assert_success_response(response)
        
        data = response.get("data", {})
        if "user_message" in data and "ai_message" in data:
            # 发送消息的响应
            user_msg = data["user_message"]
            ai_msg = data["ai_message"]
            
            for msg in [user_msg, ai_msg]:
                required_fields = ["id", "content", "role", "created_at"]
                BaseE2ETest.assert_data_structure(msg, required_fields)
        elif "messages" in data:
            # 消息列表响应
            messages = data["messages"]
            assert isinstance(messages, list), "messages should be a list"
            for msg in messages:
                required_fields = ["id", "content", "role", "created_at"]
                BaseE2ETest.assert_data_structure(msg, required_fields)
    
    # ===== AI相关断言 =====
    
    @staticmethod
    def assert_ai_response(response: Dict[str, Any]):
        """断言AI响应结构"""
        BaseE2ETest.assert_success_response(response)
        
        data = response.get("data", {})
        if "content" in data:
            # AI对话响应
            assert isinstance(data["content"], str), "AI response content should be string"
            assert len(data["content"]) > 0, "AI response should not be empty"
        elif "models" in data:
            # AI模型列表响应
            models = data["models"]
            assert isinstance(models, list), "models should be a list"
        elif "configs" in data:
            # AI配置列表响应
            configs = data["configs"]
            assert isinstance(configs, list), "configs should be a list"
    
    # ===== 权限相关断言 =====
    
    @staticmethod
    def assert_unauthorized_response(exception: APIException):
        """断言未授权响应"""
        BaseE2ETest.assert_api_exception(exception, expected_status=401)
    
    @staticmethod
    def assert_forbidden_response(exception: APIException):
        """断言禁止访问响应"""
        BaseE2ETest.assert_api_exception(exception, expected_status=403)
    
    @staticmethod
    def assert_not_found_response(exception: APIException):
        """断言资源不存在响应"""
        BaseE2ETest.assert_api_exception(exception, expected_status=404)
    
    @staticmethod
    def assert_conflict_response(exception: APIException):
        """断言冲突响应"""
        BaseE2ETest.assert_api_exception(exception, expected_status=409)
    
    @staticmethod
    def assert_validation_error(exception: APIException):
        """断言验证错误响应"""
        BaseE2ETest.assert_api_exception(exception, expected_status=422)
    
    # ===== 工具方法 =====
    
    @staticmethod
    def wait_for_condition(condition_func, timeout: int = 30, interval: float = 0.5):
        """等待条件满足"""
        import time
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(interval)
        
        return False
    
    @staticmethod
    def extract_id_from_response(response: Dict[str, Any], data_key: str) -> int:
        """从响应中提取ID"""
        BaseE2ETest.assert_success_response(response)
        data = response.get("data", {})
        assert data_key in data, f"Data key '{data_key}' not found in response data"
        
        item = data[data_key]
        assert "id" in item, f"ID not found in {data_key}"
        
        return item["id"]
    
    def setup_method(self, method):
        """测试方法设置"""
        if config.debug:
            print(f"\n=== Starting test: {method.__name__} ===")
    
    def teardown_method(self, method):
        """测试方法清理"""
        if config.debug:
            print(f"=== Finished test: {method.__name__} ===")


class AdminE2ETest(BaseE2ETest):
    """管理员E2E测试基类"""
    
    def requires_admin(self, client: CampusLLMClient):
        """验证客户端具有管理员权限"""
        try:
            # 尝试访问管理员接口来验证权限
            client.get_system_config()
        except APIException as e:
            if e.status_code in [401, 403]:
                pytest.skip("Test requires admin privileges")
            raise


class UserE2ETest(BaseE2ETest):
    """普通用户E2E测试基类"""
    
    def requires_login(self, client: CampusLLMClient):
        """验证客户端已登录"""
        try:
            # 尝试获取用户信息来验证登录状态
            client.get_me()
        except APIException as e:
            if e.status_code == 401:
                pytest.skip("Test requires user to be logged in")
            raise