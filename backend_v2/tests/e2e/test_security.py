"""
安全和权限测试 - 简化版本
"""
import pytest
from .base import UserE2ETest
from .api_client import CampusLLMClient, APIException


@pytest.mark.security
class TestBasicSecurity(UserE2ETest):
    """基础安全测试"""
    
    @pytest.mark.smoke
    def test_unauthorized_access(self, client: CampusLLMClient):
        """未登录访问受保护接口"""
        with pytest.raises(APIException) as exc_info:
            client.get_me()
        
        print(f"🔍 Debug - Unauthorized access status: {exc_info.value.status_code}")
        print(f"🔍 Debug - Unauthorized access message: {exc_info.value.message}")
        print(f"🔍 Debug - Unauthorized access response: {exc_info.value.response_data}")
        assert exc_info.value.status_code == 401
    
    def test_admin_endpoints_require_admin_role(self, client: CampusLLMClient, 
                                               logged_in_user):
        """普通用户访问管理员接口"""
        with pytest.raises(APIException) as exc_info:
            client.get_system_config()
        
        print(f"🔍 Debug - Admin endpoint access status: {exc_info.value.status_code}")
        print(f"🔍 Debug - Admin endpoint access message: {exc_info.value.message}")
        print(f"🔍 Debug - Admin endpoint access response: {exc_info.value.response_data}")
        assert exc_info.value.status_code == 403
    
    def test_user_data_isolation(self, client: CampusLLMClient, logged_in_user, 
                                another_user, test_semester):
        """用户数据隔离测试"""
        # 另一个用户创建课程
        another_client = CampusLLMClient(base_url=client.base_url)
        another_client.login(
            another_user["user_data"]["username"], 
            another_user["user_data"]["password"]
        )
        
        from .factories import create_test_course
        course_data = create_test_course(test_semester["semester"]["id"])
        course_response = another_client.create_course(**course_data)
        other_course_id = course_response["data"]["course"]["id"]
        
        # 当前用户尝试访问其他用户的课程
        with pytest.raises(APIException) as exc_info:
            client.get_course(other_course_id)
        
        assert exc_info.value.status_code == 403