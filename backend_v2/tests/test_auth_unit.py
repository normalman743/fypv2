"""
Auth模块单元测试 - Service层业务逻辑测试

基于真实环境测试策略，专注于业务逻辑验证，不涉及HTTP请求
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.auth.service import AuthService
from src.auth.schemas import UserRegister, UserLogin, UserUpdate, PasswordChangeRequest
from src.auth.models import User, InviteCode
from src.shared.exceptions import (
    BadRequestError, ConflictError, ForbiddenError, UnauthorizedError
)


class TestAuthServiceRegister:
    """用户注册业务逻辑测试"""
    
    def test_register_success(self, auth_service: AuthService, valid_invite_code: InviteCode, mock_email_service):
        """测试注册成功路径"""
        user_data = UserRegister(
            username="testuser123",
            email="testuser@584743.xyz",
            password="TestPassword123!",
            invite_code=valid_invite_code.code
        )
        
        result = auth_service.register(user_data)
        
        # 验证返回结果
        assert "user" in result
        assert "message" in result
        assert result["user"].username == "testuser123"
        assert result["user"].email == "testuser@584743.xyz"
        assert result["user"].is_active is True
        assert result["user"].email_verified is False  # 初始状态
        
        # 验证密码已加密
        assert result["user"].password_hash != "TestPassword123!"
        assert result["user"].password_changed_at is not None
        
        # 验证邀请码被标记为已使用
        assert valid_invite_code.is_used is True
        assert valid_invite_code.used_by == result["user"].id
        assert valid_invite_code.used_at is not None
        
        # 验证验证邮件被发送（仅在启用邮箱验证时）
        from src.shared.config import settings
        if settings.enable_email_verification:
            assert mock_email_service.called
        else:
            # 邮箱验证已禁用，不应该发送邮件
            assert not mock_email_service.called
    
    def test_register_duplicate_username(self, auth_service: AuthService, regular_user: User, valid_invite_code: InviteCode):
        """测试用户名重复错误"""
        user_data = UserRegister(
            username=regular_user.username,  # 使用已存在的用户名
            email="newemail@584743.xyz",
            password="TestPassword123!",
            invite_code=valid_invite_code.code
        )
        
        with pytest.raises(ConflictError) as exc_info:
            auth_service.register(user_data)
        
        assert exc_info.value.error_code == "USERNAME_EXISTS"
        assert "用户名已存在" in str(exc_info.value)
    
    def test_register_duplicate_email(self, auth_service: AuthService, regular_user: User, valid_invite_code: InviteCode):
        """测试邮箱重复错误"""
        user_data = UserRegister(
            username="newusername",
            email=regular_user.email,  # 使用已存在的邮箱
            password="TestPassword123!",
            invite_code=valid_invite_code.code
        )
        
        with pytest.raises(ConflictError) as exc_info:
            auth_service.register(user_data)
        
        assert exc_info.value.error_code == "EMAIL_EXISTS"
        assert "邮箱已注册" in str(exc_info.value)
    
    def test_register_invalid_invite_code(self, auth_service: AuthService):
        """测试无效邀请码错误"""
        user_data = UserRegister(
            username="testuser123",
            email="testuser@584743.xyz",
            password="TestPassword123!",
            invite_code="INVALID123"
        )
        
        with pytest.raises(BadRequestError) as exc_info:
            auth_service.register(user_data)
        
        assert exc_info.value.error_code == "INVALID_INVITE_CODE"
        assert "邀请码无效或已使用" in str(exc_info.value)
    
    def test_register_expired_invite_code(self, auth_service: AuthService, expired_invite_code: InviteCode):
        """测试过期邀请码错误"""
        user_data = UserRegister(
            username="testuser123",
            email="testuser@584743.xyz",
            password="TestPassword123!",
            invite_code=expired_invite_code.code
        )
        
        with pytest.raises(BadRequestError) as exc_info:
            auth_service.register(user_data)
        
        assert exc_info.value.error_code == "INVITE_CODE_EXPIRED"
        assert "邀请码已过期" in str(exc_info.value)
    
    def test_register_used_invite_code(self, auth_service: AuthService, used_invite_code: InviteCode):
        """测试已使用邀请码错误"""
        user_data = UserRegister(
            username="testuser123",
            email="testuser@584743.xyz",
            password="TestPassword123!",
            invite_code=used_invite_code.code
        )
        
        with pytest.raises(BadRequestError) as exc_info:
            auth_service.register(user_data)
        
        assert exc_info.value.error_code == "INVALID_INVITE_CODE"
        assert "邀请码无效或已使用" in str(exc_info.value)


class TestAuthServiceLogin:
    """用户登录业务逻辑测试"""
    
    def test_login_success_with_username(self, auth_service: AuthService, regular_user: User):
        """测试用户名登录成功"""
        login_data = UserLogin(
            username=regular_user.username,
            password="UserTest123!"
        )
        
        result = auth_service.login(login_data)
        
        # 验证返回结果
        assert "access_token" in result
        assert "token_type" in result
        assert "expires_in" in result
        assert "user" in result
        assert result["token_type"] == "bearer"
        assert isinstance(result["expires_in"], int)
        
        # 验证用户信息
        assert result["user"].id == regular_user.id
        assert result["user"].username == regular_user.username
        
        # 验证登录状态更新
        assert regular_user.last_login_at is not None
        assert regular_user.failed_login_attempts == 0
        assert regular_user.locked_until is None
    
    def test_login_success_with_email(self, auth_service: AuthService, regular_user: User):
        """测试邮箱登录成功"""
        login_data = UserLogin(
            username=regular_user.email,  # 使用邮箱登录
            password="UserTest123!"
        )
        
        result = auth_service.login(login_data)
        
        assert "access_token" in result
        assert result["user"].id == regular_user.id
    
    def test_login_invalid_credentials_username(self, auth_service: AuthService):
        """测试无效用户名登录"""
        login_data = UserLogin(
            username="nonexistent_user",
            password="AnyPassword123!"
        )
        
        with pytest.raises(UnauthorizedError) as exc_info:
            auth_service.login(login_data)
        
        assert exc_info.value.error_code == "INVALID_CREDENTIALS"
        assert "用户名或密码错误" in str(exc_info.value)
    
    def test_login_invalid_credentials_password(self, auth_service: AuthService, regular_user: User):
        """测试无效密码登录"""
        login_data = UserLogin(
            username=regular_user.username,
            password="WrongPassword123!"
        )
        
        with pytest.raises(UnauthorizedError) as exc_info:
            auth_service.login(login_data)
        
        assert exc_info.value.error_code == "INVALID_CREDENTIALS"
        assert "用户名或密码错误" in str(exc_info.value)
        
        # 验证失败登录次数增加
        assert regular_user.failed_login_attempts == 1
    
    def test_login_inactive_user(self, auth_service: AuthService, db_session: Session):
        """测试禁用用户登录"""
        # 创建禁用用户
        inactive_user = User(
            username="inactive_user",
            email="inactive@584743.xyz",
            password_hash=auth_service._get_password_hash("InactiveTest123!"),
            is_active=False,  # 禁用状态
            email_verified=True,
            password_changed_at=datetime.utcnow()
        )
        db_session.add(inactive_user)
        db_session.commit()
        
        login_data = UserLogin(
            username="inactive_user",
            password="InactiveTest123!"
        )
        
        with pytest.raises(UnauthorizedError) as exc_info:
            auth_service.login(login_data)
        
        assert exc_info.value.error_code == "ACCOUNT_DISABLED"
        assert "账户已被禁用" in str(exc_info.value)
    
    def test_login_locked_user(self, auth_service: AuthService, db_session: Session):
        """测试锁定用户登录"""
        # 创建锁定用户
        locked_user = User(
            username="locked_user",
            email="locked@584743.xyz",
            password_hash=auth_service._get_password_hash("LockedTest123!"),
            is_active=True,
            email_verified=True,
            locked_until=datetime.utcnow() + timedelta(hours=1),  # 锁定1小时
            failed_login_attempts=5,
            password_changed_at=datetime.utcnow()
        )
        db_session.add(locked_user)
        db_session.commit()
        
        login_data = UserLogin(
            username="locked_user",
            password="LockedTest123!"
        )
        
        with pytest.raises(UnauthorizedError) as exc_info:
            auth_service.login(login_data)
        
        assert exc_info.value.error_code == "ACCOUNT_LOCKED"
        assert "账户暂时锁定" in str(exc_info.value)
    
    def test_login_account_lockout_after_failures(self, auth_service: AuthService, db_session: Session):
        """测试连续失败登录后账户锁定"""
        # 创建测试用户
        test_user = User(
            username="lockout_test",
            email="lockout@584743.xyz",
            password_hash=auth_service._get_password_hash("LockoutTest123!"),
            is_active=True,
            email_verified=True,
            failed_login_attempts=4,  # 已经失败4次
            password_changed_at=datetime.utcnow()
        )
        db_session.add(test_user)
        db_session.commit()
        
        login_data = UserLogin(
            username="lockout_test",
            password="WrongPassword123!"
        )
        
        with pytest.raises(UnauthorizedError):
            auth_service.login(login_data)
        
        # 验证账户被锁定
        assert test_user.failed_login_attempts == 5
        assert test_user.locked_until is not None
        assert test_user.locked_until > datetime.utcnow()


class TestAuthServiceUpdateUser:
    """用户更新业务逻辑测试"""
    
    def test_update_user_success(self, auth_service: AuthService, regular_user: User):
        """测试更新用户信息成功"""
        update_data = UserUpdate(
            username="updated_username",
            preferred_language="en_US",
            preferred_theme="dark"
        )
        
        result = auth_service.update_user(regular_user.id, update_data)
        
        # Service方法现在返回字典 {"user": User, "message": str}
        assert isinstance(result, dict)
        assert "user" in result
        assert "message" in result
        
        updated_user = result["user"]
        assert updated_user.username == "updated_username"
        assert updated_user.preferred_language == "en_US"
        assert updated_user.preferred_theme == "dark"
        assert updated_user.email == regular_user.email  # 邮箱不变
    
    def test_update_user_not_found(self, auth_service: AuthService):
        """测试更新不存在的用户"""
        update_data = UserUpdate(username="new_username")
        
        with pytest.raises(BadRequestError) as exc_info:
            auth_service.update_user(99999, update_data)
        
        assert exc_info.value.error_code == "USER_NOT_FOUND"
        assert "用户不存在" in str(exc_info.value)
    
    def test_update_user_duplicate_username(self, auth_service: AuthService, regular_user: User, admin_user: User):
        """测试更新用户名重复"""
        update_data = UserUpdate(username=admin_user.username)  # 使用已存在的用户名
        
        with pytest.raises(ConflictError) as exc_info:
            auth_service.update_user(regular_user.id, update_data)
        
        assert exc_info.value.error_code == "USERNAME_EXISTS"
        assert "用户名已存在" in str(exc_info.value)


class TestAuthServicePasswordManagement:
    """密码管理业务逻辑测试"""
    
    def test_change_password_success(self, auth_service: AuthService, regular_user: User):
        """测试修改密码成功"""
        change_request = PasswordChangeRequest(
            old_password="UserTest123!",
            new_password="NewPassword123!"
        )
        
        result = auth_service.change_password(regular_user.id, change_request)
        
        assert result["message"] == "密码修改成功"
        
        # 验证密码已更新
        assert auth_service._verify_password("NewPassword123!", regular_user.password_hash)
        assert not auth_service._verify_password("UserTest123!", regular_user.password_hash)
        assert regular_user.password_changed_at is not None
    
    def test_change_password_wrong_old_password(self, auth_service: AuthService, regular_user: User):
        """测试旧密码错误"""
        change_request = PasswordChangeRequest(
            old_password="WrongOldPassword123!",
            new_password="NewPassword123!"
        )
        
        with pytest.raises(UnauthorizedError) as exc_info:
            auth_service.change_password(regular_user.id, change_request)
        
        assert exc_info.value.error_code == "INVALID_PASSWORD"
        assert "当前密码错误" in str(exc_info.value)
    
    def test_change_password_user_not_found(self, auth_service: AuthService):
        """测试修改不存在用户的密码"""
        change_request = PasswordChangeRequest(
            old_password="OldPassword123!",
            new_password="NewPassword123!"
        )
        
        with pytest.raises(BadRequestError) as exc_info:
            auth_service.change_password(99999, change_request)
        
        assert exc_info.value.error_code == "USER_NOT_FOUND"
        assert "用户不存在" in str(exc_info.value)


class TestAuthServiceEmailVerification:
    """邮箱验证业务逻辑测试"""
    
    def test_verify_email_success(self, auth_service: AuthService, unverified_user: User, db_session: Session):
        """测试邮箱验证成功"""
        from src.auth.models import EmailVerification
        
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
        
        # 执行验证
        result = auth_service.verify_email(unverified_user.email, "ABC123")
        
        # Service方法现在返回字典 {"user": User, "message": str}
        assert isinstance(result, dict)
        assert "user" in result
        assert "message" in result
        
        verified_user = result["user"]
        assert verified_user.email_verified is True
        assert verification.is_used is True
    
    def test_verify_email_invalid_code(self, auth_service: AuthService, unverified_user: User):
        """测试无效验证码"""
        with pytest.raises(BadRequestError) as exc_info:
            auth_service.verify_email(unverified_user.email, "INVALID123")
        
        assert exc_info.value.error_code == "INVALID_VERIFICATION_CODE"
        assert "验证码无效或已过期" in str(exc_info.value)
    
    def test_resend_verification_success(self, auth_service: AuthService, unverified_user: User, mock_email_service):
        """测试重新发送验证码成功"""
        result = auth_service.resend_verification(unverified_user.email)
        
        # Service方法现在返回字典 {"message": str}
        assert isinstance(result, dict)
        assert "message" in result
        assert unverified_user.email in result["message"]
        assert mock_email_service.called
    
    def test_resend_verification_email_not_found(self, auth_service: AuthService):
        """测试重新发送验证码 - 邮箱不存在"""
        with pytest.raises(BadRequestError) as exc_info:
            auth_service.resend_verification("notfound@584743.xyz")
        
        assert exc_info.value.error_code == "EMAIL_NOT_FOUND"
        assert "邮箱不存在" in str(exc_info.value)
    
    def test_resend_verification_already_verified(self, auth_service: AuthService, regular_user: User):
        """测试重新发送验证码 - 邮箱已验证"""
        with pytest.raises(BadRequestError) as exc_info:
            auth_service.resend_verification(regular_user.email)
        
        assert exc_info.value.error_code == "EMAIL_ALREADY_VERIFIED"
        assert "邮箱已验证" in str(exc_info.value)


class TestAuthServiceHelperMethods:
    """辅助方法测试"""
    
    def test_password_hashing(self, auth_service: AuthService):
        """测试密码哈希功能"""
        password = "TestPassword123!"
        
        # 生成哈希
        hash1 = auth_service._get_password_hash(password)
        hash2 = auth_service._get_password_hash(password)
        
        # 验证哈希不同（包含盐值）
        assert hash1 != hash2
        assert hash1 != password
        assert hash2 != password
        
        # 验证都能验证原密码
        assert auth_service._verify_password(password, hash1)
        assert auth_service._verify_password(password, hash2)
        
        # 验证错误密码不能通过
        assert not auth_service._verify_password("WrongPassword", hash1)
    
    def test_access_token_creation(self, auth_service: AuthService):
        """测试访问令牌创建"""
        token_data = {"sub": "123", "username": "testuser"}
        
        token = auth_service._create_access_token(token_data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # 验证令牌包含正确的数据
        from jose import jwt
        from src.shared.config import settings
        
        decoded = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert decoded["sub"] == "123"
        assert decoded["username"] == "testuser"
        assert "exp" in decoded  # 包含过期时间