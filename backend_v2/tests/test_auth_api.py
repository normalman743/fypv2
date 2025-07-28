"""
Auth模块API集成测试 - 完整HTTP请求流程测试

基于真实环境测试策略，测试完整的API端点行为
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.auth.models import User, InviteCode
from conftest import assert_success_response, assert_error_response


class TestAuthRegisterAPI:
    """用户注册API测试"""
    
    def test_register_success(self, client: TestClient, valid_invite_code: InviteCode, mock_email_service):
        """测试用户注册 - 成功路径"""
        response = client.post("/api/v1/auth/register", json={
            "username": "newuser123",
            "email": "newuser@test.local",
            "password": "NewUser123!",
            "invite_code": valid_invite_code.code
        })
        
        assert_success_response(response, ["user", "message"])
        
        data = response.json()["data"]
        assert data["user"]["username"] == "newuser123"
        assert data["user"]["email"] == "newuser@test.local"
        assert data["user"]["is_active"] is True
        assert data["user"]["email_verified"] is False
        assert "password_hash" not in data["user"]  # 不应返回密码哈希
        
        # 验证邮件服务被调用
        assert mock_email_service.called
    
    def test_register_invalid_invite_code(self, client: TestClient):
        """测试无效邀请码注册"""
        response = client.post("/api/v1/auth/register", json={
            "username": "newuser123", 
            "email": "newuser@test.local",
            "password": "NewUser123!",
            "invite_code": "INVALID123"
        })
        
        assert_error_response(response, 400, "INVALID_INVITE_CODE")
    
    def test_register_expired_invite_code(self, client: TestClient, expired_invite_code: InviteCode):
        """测试过期邀请码注册"""
        response = client.post("/api/v1/auth/register", json={
            "username": "newuser123",
            "email": "newuser@test.local", 
            "password": "NewUser123!",
            "invite_code": expired_invite_code.code
        })
        
        assert_error_response(response, 400, "INVITE_CODE_EXPIRED")
    
    def test_register_used_invite_code(self, client: TestClient, used_invite_code: InviteCode):
        """测试已使用邀请码注册"""
        response = client.post("/api/v1/auth/register", json={
            "username": "newuser123",
            "email": "newuser@test.local",
            "password": "NewUser123!",
            "invite_code": used_invite_code.code
        })
        
        assert_error_response(response, 400, "INVALID_INVITE_CODE")
    
    def test_register_duplicate_username(self, client: TestClient, regular_user: User, valid_invite_code: InviteCode):
        """测试用户名重复注册"""
        response = client.post("/api/v1/auth/register", json={
            "username": regular_user.username,
            "email": "newemail@test.local",
            "password": "NewUser123!",
            "invite_code": valid_invite_code.code
        })
        
        assert_error_response(response, 409, "USERNAME_EXISTS")
    
    def test_register_duplicate_email(self, client: TestClient, regular_user: User, valid_invite_code: InviteCode):
        """测试邮箱重复注册"""
        response = client.post("/api/v1/auth/register", json={
            "username": "newusername",
            "email": regular_user.email,
            "password": "NewUser123!",
            "invite_code": valid_invite_code.code
        })
        
        assert_error_response(response, 409, "EMAIL_EXISTS")
    
    def test_register_validation_errors(self, client: TestClient, valid_invite_code: InviteCode):
        """测试注册数据验证错误"""
        # 用户名太短
        response = client.post("/api/v1/auth/register", json={
            "username": "ab",  # 少于3个字符
            "email": "test@test.local",
            "password": "ValidPassword123!",
            "invite_code": valid_invite_code.code
        })
        assert response.status_code == 422
        
        # 密码太短
        response = client.post("/api/v1/auth/register", json={
            "username": "validuser",
            "email": "test@test.local",
            "password": "short",  # 少于8个字符
            "invite_code": valid_invite_code.code
        })
        assert response.status_code == 422
        
        # 无效邮箱格式
        response = client.post("/api/v1/auth/register", json={
            "username": "validuser",
            "email": "invalid-email",  # 无效邮箱格式
            "password": "ValidPassword123!",
            "invite_code": valid_invite_code.code
        })
        assert response.status_code == 422


class TestAuthLoginAPI:
    """用户登录API测试"""
    
    def test_login_success_with_username(self, client: TestClient, regular_user: User):
        """测试用户名登录成功"""
        response = client.post("/api/v1/auth/login", json={
            "username": regular_user.username,
            "password": "UserTest123!"
        })
        
        assert_success_response(response, ["access_token", "token_type", "expires_in", "user"])
        
        data = response.json()["data"]
        assert data["token_type"] == "bearer"
        assert isinstance(data["expires_in"], int)
        assert data["user"]["id"] == regular_user.id
        assert data["user"]["username"] == regular_user.username
        assert "password_hash" not in data["user"]
    
    def test_login_success_with_email(self, client: TestClient, regular_user: User):
        """测试邮箱登录成功"""
        response = client.post("/api/v1/auth/login", json={
            "username": regular_user.email,  # 使用邮箱登录
            "password": "UserTest123!"
        })
        
        assert_success_response(response, ["access_token", "user"])
        
        data = response.json()["data"]
        assert data["user"]["id"] == regular_user.id
    
    def test_login_invalid_credentials_username(self, client: TestClient):
        """测试无效用户名登录"""
        response = client.post("/api/v1/auth/login", json={
            "username": "nonexistent_user",
            "password": "AnyPassword123!"
        })
        
        assert_error_response(response, 401, "INVALID_CREDENTIALS")
    
    def test_login_invalid_credentials_password(self, client: TestClient, regular_user: User):
        """测试无效密码登录"""
        response = client.post("/api/v1/auth/login", json={
            "username": regular_user.username,
            "password": "WrongPassword123!"
        })
        
        assert_error_response(response, 401, "INVALID_CREDENTIALS")
    
    def test_login_validation_errors(self, client: TestClient):
        """测试登录数据验证错误"""
        # 缺少用户名
        response = client.post("/api/v1/auth/login", json={
            "password": "ValidPassword123!"
        })
        assert response.status_code == 422
        
        # 缺少密码
        response = client.post("/api/v1/auth/login", json={
            "username": "validuser"
        })
        assert response.status_code == 422


class TestAuthUserInfoAPI:
    """用户信息API测试"""
    
    def test_get_current_user_success(self, client: TestClient, user_headers: dict, regular_user: User):
        """测试获取当前用户信息成功"""
        response = client.get("/api/v1/auth/me", headers=user_headers)
        
        assert_success_response(response, ["user"])
        
        data = response.json()["data"]
        assert data["user"]["id"] == regular_user.id
        assert data["user"]["username"] == regular_user.username
        assert data["user"]["email"] == regular_user.email
        assert "password_hash" not in data["user"]
    
    def test_get_current_user_unauthorized(self, client: TestClient):
        """测试未认证获取用户信息"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
    
    def test_get_current_user_invalid_token(self, client: TestClient):
        """测试无效令牌获取用户信息"""
        response = client.get("/api/v1/auth/me", headers={
            "Authorization": "Bearer invalid_token_here"
        })
        assert response.status_code == 401


class TestAuthUpdateUserAPI:
    """用户更新API测试"""
    
    def test_update_user_success(self, client: TestClient, user_headers: dict, regular_user: User):
        """测试更新用户信息成功"""
        response = client.put("/api/v1/auth/me", 
            headers=user_headers,
            json={
                "username": "updated_username",
                "display_name": "Updated Display Name"
            }
        )
        
        assert_success_response(response, ["user"])
        
        data = response.json()["data"]
        assert data["user"]["username"] == "updated_username"
        assert data["user"]["display_name"] == "Updated Display Name"
        assert data["user"]["email"] == regular_user.email  # 邮箱不变
    
    def test_update_user_duplicate_username(self, client: TestClient, user_headers: dict, admin_user: User):
        """测试更新用户名重复"""
        response = client.put("/api/v1/auth/me",
            headers=user_headers,
            json={"username": admin_user.username}
        )
        
        assert_error_response(response, 409, "USERNAME_EXISTS")
    
    def test_update_user_unauthorized(self, client: TestClient):
        """测试未认证更新用户信息"""
        response = client.put("/api/v1/auth/me", json={
            "username": "new_username"
        })
        assert response.status_code == 401
    
    def test_update_user_validation_errors(self, client: TestClient, user_headers: dict):
        """测试更新用户信息验证错误"""
        # 用户名太短
        response = client.put("/api/v1/auth/me",
            headers=user_headers,
            json={"username": "ab"}  # 少于3个字符
        )
        assert response.status_code == 422


class TestAuthPasswordManagementAPI:
    """密码管理API测试"""
    
    def test_change_password_success(self, client: TestClient, user_headers: dict):
        """测试修改密码成功"""
        response = client.post("/api/v1/auth/change-password",
            headers=user_headers,
            json={
                "old_password": "UserTest123!",
                "new_password": "NewPassword123!"
            }
        )
        
        assert_success_response(response, ["message"])
        
        data = response.json()["data"]
        assert data["message"] == "密码修改成功"
    
    def test_change_password_wrong_old_password(self, client: TestClient, user_headers: dict):
        """测试旧密码错误"""
        response = client.post("/api/v1/auth/change-password",
            headers=user_headers,
            json={
                "old_password": "WrongOldPassword123!",
                "new_password": "NewPassword123!"
            }
        )
        
        assert_error_response(response, 401, "INVALID_PASSWORD")
    
    def test_change_password_unauthorized(self, client: TestClient):
        """测试未认证修改密码"""
        response = client.post("/api/v1/auth/change-password", json={
            "old_password": "OldPassword123!",
            "new_password": "NewPassword123!"
        })
        assert response.status_code == 401
    
    def test_change_password_validation_errors(self, client: TestClient, user_headers: dict):
        """测试修改密码验证错误"""
        # 新密码太短
        response = client.post("/api/v1/auth/change-password",
            headers=user_headers,
            json={
                "old_password": "UserTest123!",
                "new_password": "short"  # 少于8个字符
            }
        )
        assert response.status_code == 422


class TestAuthEmailVerificationAPI:
    """邮箱验证API测试"""
    
    def test_verify_email_success(self, client: TestClient, unverified_user: User, db_session: Session):
        """测试邮箱验证成功"""
        from src.auth.models import EmailVerification
        from datetime import datetime, timedelta
        
        # 创建验证记录
        verification = EmailVerification(
            user_id=unverified_user.id,
            email=unverified_user.email,
            verification_code="ABC123",
            verification_type="registration",
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        db_session.add(verification)
        db_session.commit()
        
        response = client.post("/api/v1/auth/verify-email", json={
            "email": unverified_user.email,
            "verification_code": "ABC123"
        })
        
        assert_success_response(response, ["user", "message"])
        
        data = response.json()["data"]
        assert data["user"]["email_verified"] is True
        assert "邮箱验证成功" in data["message"]
    
    def test_verify_email_invalid_code(self, client: TestClient, unverified_user: User):
        """测试无效验证码"""
        response = client.post("/api/v1/auth/verify-email", json={
            "email": unverified_user.email,
            "verification_code": "INVALID123"
        })
        
        assert_error_response(response, 400, "INVALID_VERIFICATION_CODE")
    
    def test_resend_verification_success(self, client: TestClient, unverified_user: User, mock_email_service):
        """测试重新发送验证码成功"""
        response = client.post("/api/v1/auth/resend-verification", json={
            "email": unverified_user.email
        })
        
        assert_success_response(response, ["message"])
        
        data = response.json()["data"]
        assert "验证码已重新发送" in data["message"]
        assert mock_email_service.called
    
    def test_resend_verification_email_not_found(self, client: TestClient):
        """测试重新发送验证码 - 邮箱不存在"""
        response = client.post("/api/v1/auth/resend-verification", json={
            "email": "notfound@test.local"
        })
        
        assert_error_response(response, 400, "EMAIL_NOT_FOUND")
    
    def test_resend_verification_already_verified(self, client: TestClient, regular_user: User):
        """测试重新发送验证码 - 邮箱已验证"""
        response = client.post("/api/v1/auth/resend-verification", json={
            "email": regular_user.email
        })
        
        assert_error_response(response, 400, "EMAIL_ALREADY_VERIFIED")
    
    def test_email_verification_validation_errors(self, client: TestClient):
        """测试邮箱验证数据验证错误"""
        # 无效邮箱格式
        response = client.post("/api/v1/auth/verify-email", json={
            "email": "invalid-email",
            "verification_code": "ABC123"
        })
        assert response.status_code == 422
        
        # 缺少验证码
        response = client.post("/api/v1/auth/verify-email", json={
            "email": "test@test.local"
        })
        assert response.status_code == 422


class TestAuthPasswordResetAPI:
    """密码重置API测试"""
    
    def test_forgot_password_success(self, client: TestClient, regular_user: User, mock_password_reset_email):
        """测试忘记密码请求成功"""
        response = client.post("/api/v1/auth/forgot-password", json={
            "email": regular_user.email
        })
        
        assert_success_response(response, ["message"])
        
        data = response.json()["data"]
        assert "重置邮件已发送" in data["message"]
        assert mock_password_reset_email.called
    
    def test_forgot_password_email_not_found(self, client: TestClient, mock_password_reset_email):
        """测试忘记密码 - 邮箱不存在（安全考虑，不透露）"""
        response = client.post("/api/v1/auth/forgot-password", json={
            "email": "notfound@test.local"
        })
        
        # 安全考虑：不透露邮箱是否存在
        assert_success_response(response, ["message"])
        
        data = response.json()["data"]
        assert "重置邮件已发送" in data["message"]
        # 但实际上不会发送邮件
        assert not mock_password_reset_email.called
    
    def test_reset_password_success(self, client: TestClient, regular_user: User, db_session: Session):
        """测试密码重置成功"""
        from src.auth.models import PasswordReset
        from datetime import datetime, timedelta
        import uuid
        
        # 创建重置记录
        reset_token = str(uuid.uuid4())
        password_reset = PasswordReset(
            user_id=regular_user.id,
            reset_token=reset_token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db_session.add(password_reset)
        db_session.commit()
        
        response = client.post("/api/v1/auth/reset-password", json={
            "reset_token": reset_token,
            "new_password": "NewResetPassword123!"
        })
        
        assert_success_response(response, ["message"])
        
        data = response.json()["data"]
        assert data["message"] == "密码重置成功"
    
    def test_reset_password_invalid_token(self, client: TestClient):
        """测试无效重置令牌"""
        response = client.post("/api/v1/auth/reset-password", json={
            "reset_token": "invalid_token_here",
            "new_password": "NewPassword123!"
        })
        
        assert_error_response(response, 400, "INVALID_RESET_TOKEN")
    
    def test_password_reset_validation_errors(self, client: TestClient):
        """测试密码重置验证错误"""
        # 新密码太短
        response = client.post("/api/v1/auth/reset-password", json={
            "reset_token": "valid_token",
            "new_password": "short"  # 少于8个字符
        })
        assert response.status_code == 422
        
        # 缺少重置令牌
        response = client.post("/api/v1/auth/reset-password", json={
            "new_password": "NewPassword123!"
        })
        assert response.status_code == 422


class TestAuthPermissionsAPI:
    """权限测试"""
    
    def test_protected_endpoint_requires_auth(self, client: TestClient):
        """测试受保护端点需要认证"""
        protected_endpoints = [
            ("GET", "/api/v1/auth/me"),
            ("PUT", "/api/v1/auth/me"),
            ("POST", "/api/v1/auth/change-password"),
        ]
        
        for method, endpoint in protected_endpoints:
            response = client.request(method, endpoint)
            assert response.status_code == 401, f"Endpoint {method} {endpoint} should require auth"
    
    def test_public_endpoints_no_auth_required(self, client: TestClient):
        """测试公开端点不需要认证"""
        # 注册端点（需要有效数据）
        response = client.post("/api/v1/auth/register", json={
            "username": "test", "email": "invalid", "password": "short", "invite_code": "invalid"
        })
        # 应该是验证错误而不是认证错误
        assert response.status_code in [400, 422]
        
        # 登录端点（需要有效数据）
        response = client.post("/api/v1/auth/login", json={
            "username": "test", "password": "short"
        })
        # 应该是验证错误或凭据错误，而不是认证错误
        assert response.status_code in [401, 422]


class TestAuthResponseFormat:
    """API响应格式测试"""
    
    def test_success_response_format(self, client: TestClient, regular_user: User):
        """测试成功响应格式"""
        response = client.post("/api/v1/auth/login", json={
            "username": regular_user.username,
            "password": "UserTest123!"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应结构
        assert "success" in data
        assert "data" in data
        assert data["success"] is True
        assert isinstance(data["data"], dict)
    
    def test_error_response_format(self, client: TestClient):
        """测试错误响应格式"""
        response = client.post("/api/v1/auth/login", json={
            "username": "nonexistent",
            "password": "password"
        })
        
        assert response.status_code == 401
        data = response.json()
        
        # 验证错误响应结构
        assert "success" in data
        assert "error" in data
        assert data["success"] is False
        assert isinstance(data["error"], dict)
        assert "code" in data["error"]
        assert "message" in data["error"]
    
    def test_validation_error_response_format(self, client: TestClient):
        """测试验证错误响应格式"""
        response = client.post("/api/v1/auth/register", json={
            "username": "ab",  # 太短
            "email": "invalid-email",  # 无效格式
            "password": "short",  # 太短
            "invite_code": ""  # 空值
        })
        
        assert response.status_code == 422
        data = response.json()
        
        # FastAPI 的验证错误格式
        assert "detail" in data
        assert isinstance(data["detail"], list)