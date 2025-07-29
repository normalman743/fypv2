"""
用户相关的End-to-End工作流测试
"""
import pytest
from .base import UserE2ETest
from .api_client import CampusLLMClient, APIException
from .factories import create_test_user, create_test_invite_code


@pytest.mark.auth
class TestUserRegistrationWorkflow(UserE2ETest):
    """用户注册工作流测试"""
    
    @pytest.mark.smoke
    def test_complete_user_registration_flow(self, client: CampusLLMClient, 
                                           admin_client: CampusLLMClient):
        """完整的用户注册流程测试"""
        # 1. 管理员创建邀请码
        invite_data = create_test_invite_code()
        invite_response = admin_client.create_invite_code(**invite_data)
        self.assert_success_response(invite_response)
        self.assert_invite_code_response(invite_response)
        
        invite_code = invite_response["data"]["invite_code"]["code"]
        
        # 2. 用户使用邀请码注册
        user_data = create_test_user()
        user_data["invite_code"] = invite_code
        
        register_response = client.register(**user_data)
        self.assert_success_response(register_response)
        self.assert_user_response(register_response)
        
        # 验证用户信息
        user_info = register_response["data"]["user"]
        assert user_info["username"] == user_data["username"]
        assert user_info["email"] == user_data["email"]
        assert user_info["role"] == "user"  # 默认角色
        
        # 3. 验证邮箱（在测试环境中使用固定验证码）
        try:
            verify_response = client.verify_email(user_data["email"], "123456")
            self.assert_success_response(verify_response)
            email_verified = True
        except APIException:
            # 如果验证失败，继续测试（某些环境可能没有邮件验证）
            email_verified = False
        
        # 4. 用户登录
        login_response = client.login(user_data["username"], user_data["password"])
        self.assert_success_response(login_response)
        self.assert_login_response(login_response)
        
        # 验证登录信息
        login_data = login_response["data"]
        assert "access_token" in login_data
        assert login_data["token_type"] == "bearer"
        assert login_data["user"]["username"] == user_data["username"]
        
        # 5. 获取用户信息（验证登录状态）
        profile_response = client.get_me()
        self.assert_success_response(profile_response)
        self.assert_user_response(profile_response)
        
        profile_data = profile_response["data"]
        assert profile_data["username"] == user_data["username"]
        assert profile_data["email"] == user_data["email"]
        
        # 6. 更新用户信息
        update_data = {
            "real_name": "更新后的姓名",
            "phone": "13800138001"
        }
        
        update_response = client.update_me(**update_data)
        self.assert_success_response(update_response)
        self.assert_user_response(update_response)
        
        updated_user = update_response["data"]
        if "real_name" in updated_user:
            assert updated_user["real_name"] == update_data["real_name"]
        
        # 7. 用户登出
        logout_response = client.logout()
        self.assert_success_response(logout_response)
        
        # 8. 验证登出后无法访问需要认证的接口
        with pytest.raises(APIException) as exc_info:
            client.get_me()
        self.assert_unauthorized_response(exc_info.value)
    
    def test_registration_with_invalid_invite_code(self, client: CampusLLMClient):
        """使用无效邀请码注册"""
        user_data = create_test_user()
        user_data["invite_code"] = "INVALID123"
        
        with pytest.raises(APIException) as exc_info:
            client.register(**user_data)
        
        # 应该返回400或404错误
        assert exc_info.value.status_code in [400, 404]
    
    def test_registration_with_duplicate_username(self, client: CampusLLMClient, 
                                                test_invite_code):
        """重复用户名注册"""
        # 先注册一个用户
        user_data1 = create_test_user()
        user_data1["invite_code"] = test_invite_code["code"]
        
        response1 = client.register(**user_data1)
        self.assert_success_response(response1)
        
        # 尝试使用相同用户名注册
        user_data2 = create_test_user()
        user_data2["username"] = user_data1["username"]  # 相同用户名
        user_data2["invite_code"] = test_invite_code["code"]
        
        with pytest.raises(APIException) as exc_info:
            client.register(**user_data2)
        
        self.assert_conflict_response(exc_info.value)
    
    def test_registration_with_duplicate_email(self, client: CampusLLMClient, 
                                             test_invite_code):
        """重复邮箱注册"""
        # 先注册一个用户
        user_data1 = create_test_user()
        user_data1["invite_code"] = test_invite_code["code"]
        
        response1 = client.register(**user_data1)
        self.assert_success_response(response1)
        
        # 尝试使用相同邮箱注册
        user_data2 = create_test_user()
        user_data2["email"] = user_data1["email"]  # 相同邮箱
        user_data2["invite_code"] = test_invite_code["code"]
        
        with pytest.raises(APIException) as exc_info:
            client.register(**user_data2)
        
        self.assert_conflict_response(exc_info.value)


@pytest.mark.auth
class TestUserLoginWorkflow(UserE2ETest):
    """用户登录工作流测试"""
    
    def test_login_with_username(self, client: CampusLLMClient, registered_user):
        """使用用户名登录"""
        user_data = registered_user["user_data"]
        
        response = client.login(user_data["username"], user_data["password"])
        self.assert_success_response(response)
        self.assert_login_response(response)
        
        # 验证token被正确设置
        assert client.access_token is not None
        assert len(client.access_token) > 20
    
    def test_login_with_email(self, client: CampusLLMClient, registered_user):
        """使用邮箱登录"""
        user_data = registered_user["user_data"]
        
        response = client.login(user_data["email"], user_data["password"])
        self.assert_success_response(response)
        self.assert_login_response(response)
    
    def test_login_with_invalid_credentials(self, client: CampusLLMClient, registered_user):
        """无效凭据登录"""
        user_data = registered_user["user_data"]
        
        # 错误密码
        with pytest.raises(APIException) as exc_info:
            client.login(user_data["username"], "wrong_password")
        
        assert exc_info.value.status_code in [401, 400]
    
    def test_login_with_nonexistent_user(self, client: CampusLLMClient):
        """不存在的用户登录"""
        with pytest.raises(APIException) as exc_info:
            client.login("nonexistent_user", "password")
        
        assert exc_info.value.status_code in [401, 400, 404]


@pytest.mark.auth
class TestPasswordManagement(UserE2ETest):
    """密码管理测试"""
    
    def test_change_password_flow(self, client: CampusLLMClient, logged_in_user):
        """密码修改流程"""
        user_data = logged_in_user["user_data"]
        new_password = "NewTestPass123!"
        
        # 修改密码
        change_response = client.change_password(
            current_password=user_data["password"],
            new_password=new_password
        )
        self.assert_success_response(change_response)
        
        # 登出
        client.logout()
        
        # 使用新密码登录
        login_response = client.login(user_data["username"], new_password)
        self.assert_success_response(login_response)
        self.assert_login_response(login_response)
        
        # 验证旧密码不能使用
        client.logout()
        with pytest.raises(APIException) as exc_info:
            client.login(user_data["username"], user_data["password"])
        
        assert exc_info.value.status_code in [401, 400]
    
    def test_change_password_with_wrong_current_password(self, client: CampusLLMClient, 
                                                       logged_in_user):
        """使用错误的当前密码修改"""
        with pytest.raises(APIException) as exc_info:
            client.change_password(
                current_password="wrong_password",
                new_password="NewTestPass123!"
            )
        
        assert exc_info.value.status_code in [401, 400]
    
    def test_forgot_password_flow(self, client: CampusLLMClient, registered_user):
        """忘记密码流程"""
        user_data = registered_user["user_data"]
        
        # 发送重置密码邮件
        forgot_response = client.forgot_password(user_data["email"])
        self.assert_success_response(forgot_response)
        
        # 注意：在实际测试中，我们需要从邮件或其他方式获取重置token
        # 这里只是测试API调用成功
    
    def test_forgot_password_with_invalid_email(self, client: CampusLLMClient):
        """使用无效邮箱重置密码"""
        with pytest.raises(APIException) as exc_info:
            client.forgot_password("nonexistent@test.com")
        
        assert exc_info.value.status_code in [404, 400]


@pytest.mark.auth  
class TestUserProfileManagement(UserE2ETest):
    """用户资料管理测试"""
    
    def test_get_user_profile(self, client: CampusLLMClient, logged_in_user):
        """获取用户资料"""
        response = client.get_me()
        self.assert_success_response(response)
        self.assert_user_response(response)
        
        user_info = response["data"]
        logged_in_data = logged_in_user["user_data"]
        
        assert user_info["username"] == logged_in_data["username"]
        assert user_info["email"] == logged_in_data["email"]
        assert "id" in user_info
        assert "role" in user_info
        assert "created_at" in user_info
    
    def test_update_user_profile(self, client: CampusLLMClient, logged_in_user):
        """更新用户资料"""
        update_data = {
            "real_name": "测试用户真实姓名",
            "phone": "13800138000"
        }
        
        response = client.update_me(**update_data)
        self.assert_success_response(response)
        self.assert_user_response(response)
        
        # 验证更新是否生效
        profile_response = client.get_me()
        profile_data = profile_response["data"]
        
        if "real_name" in profile_data:
            assert profile_data["real_name"] == update_data["real_name"]
    
    def test_update_user_profile_partial(self, client: CampusLLMClient, logged_in_user):
        """部分更新用户资料"""
        # 只更新一个字段
        update_data = {"real_name": "部分更新测试"}
        
        response = client.update_me(**update_data)
        self.assert_success_response(response)
        self.assert_user_response(response)
    
    def test_get_profile_without_login(self, client: CampusLLMClient):
        """未登录获取用户资料"""
        with pytest.raises(APIException) as exc_info:
            client.get_me()
        
        self.assert_unauthorized_response(exc_info.value)
    
    def test_update_profile_without_login(self, client: CampusLLMClient):
        """未登录更新用户资料"""
        with pytest.raises(APIException) as exc_info:
            client.update_me(real_name="测试")
        
        self.assert_unauthorized_response(exc_info.value)


@pytest.mark.auth
class TestEmailVerification(UserE2ETest):
    """邮箱验证测试"""
    
    def test_resend_verification_code(self, client: CampusLLMClient, registered_user):
        """重发验证码"""
        user_data = registered_user["user_data"]
        
        response = client.resend_verification(user_data["email"])
        self.assert_success_response(response)
    
    def test_resend_verification_with_invalid_email(self, client: CampusLLMClient):
        """使用无效邮箱重发验证码"""
        with pytest.raises(APIException) as exc_info:
            client.resend_verification("invalid@test.com")
        
        assert exc_info.value.status_code in [404, 400]
    
    def test_verify_email_with_invalid_code(self, client: CampusLLMClient, registered_user):
        """使用无效验证码验证邮箱"""
        user_data = registered_user["user_data"]
        
        with pytest.raises(APIException) as exc_info:
            client.verify_email(user_data["email"], "INVALID")
        
        assert exc_info.value.status_code in [400, 404]