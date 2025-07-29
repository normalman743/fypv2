"""Auth模块的业务逻辑服务"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import secrets
import string

from .models import User, EmailVerification, PasswordReset, InviteCode
from .schemas import (
    UserRegister, UserLogin, UserUpdate, PasswordChangeRequest,
    ForgotPasswordRequest, ResetPasswordRequest, EmailVerificationRequest,
    ResendVerificationRequest
)
from src.shared.exceptions import (
    BadRequestError, ConflictError, ForbiddenError, UnauthorizedError,
    NotFoundServiceException, ConflictServiceException, 
    ValidationServiceException, UnauthorizedServiceException
)
from src.shared.config import settings
from src.shared.email import get_email_service
from src.shared.base_service import BaseService


class AuthService(BaseService):
    """认证服务类 - 继承BaseService，改进数据库会话管理"""
    
    # 声明每个方法可能抛出的异常（使用新的Service异常类）
    METHOD_EXCEPTIONS = {
        'register': {ConflictServiceException, ValidationServiceException},
        'login': {UnauthorizedServiceException, ValidationServiceException},
        'get_user_profile': {UnauthorizedServiceException, NotFoundServiceException},
        'update_user': {ValidationServiceException, UnauthorizedServiceException, NotFoundServiceException},
        'logout': set(),
        'verify_email': {ValidationServiceException, NotFoundServiceException},
        'resend_verification': {ValidationServiceException},
        'change_password': {ValidationServiceException, UnauthorizedServiceException},
        'forgot_password': {ValidationServiceException, NotFoundServiceException},
        'reset_password': {ValidationServiceException, UnauthorizedServiceException},
    }
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.email_service = get_email_service()

    # ===== 现有方法 =====
    
    def register(self, user_data: UserRegister) -> Dict[str, Any]:
        """用户注册流程"""
        # 1. 检查注册是否启用
        self._check_registration_enabled()

        # 2. 验证用户唯一性
        self._validate_user_uniqueness(user_data.username, user_data.email)

        # 3. 验证邮箱域名
        self._validate_email_domain(user_data.email)

        # 4. 验证邀请码
        invite_code_obj = self._validate_and_consume_invite_code(user_data.invite_code)

        # 5. 创建用户
        user = self._create_user(user_data, invite_code_obj)

        # 6. 发送验证邮件
        message = self._send_verification_email_if_enabled(user)

        return {
            "user": user,
            "message": message
        }

    def login(self, user_data: UserLogin) -> Dict[str, Any]:
        """用户登录流程"""
        # 1. 获取用户
        user = self._get_user_by_username_or_email(user_data.username)
        if not user:
            raise UnauthorizedError("用户名或密码错误", error_code="INVALID_CREDENTIALS")

        # 2. 检查账户状态
        self._check_account_status(user)

        # 3. 验证密码
        if not self._verify_password(user_data.password, user.password_hash):
            self._handle_failed_login(user)
            raise UnauthorizedError("用户名或密码错误", error_code="INVALID_CREDENTIALS")

        # 4. 登录成功处理
        self._handle_successful_login(user)

        # 5. 生成访问令牌
        access_token = self._create_access_token({"sub": str(user.id)})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "user": user
        }

    def update_user(self, user_id: int, user_data: UserUpdate) -> Dict[str, Any]:
        """更新用户信息"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise BadRequestError("用户不存在", error_code="USER_NOT_FOUND")

        # 检查用户名唯一性
        if user_data.username and user_data.username != user.username:
            existing = self.db.query(User).filter(
                User.username == user_data.username,
                User.id != user_id
            ).first()
            if existing:
                raise ConflictError("用户名已存在", error_code="USERNAME_EXISTS")

        # 更新字段
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        
        return {
            "user": user,
            "message": "用户信息更新成功"
        }

    def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """获取用户详细信息"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnauthorizedError("用户不存在", error_code="USER_NOT_FOUND")
        
        return {
            "user": user,
            "message": None  # 获取操作通常不需要消息
        }

    def logout(self, user_id: int) -> Dict[str, Any]:
        """用户登出 - 主要用于服务端记录，客户端需要清除Token"""
        # 更新最后登录时间可以作为登出的记录
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            # 这里可以添加登出日志或其他业务逻辑
            pass
        
        return {
            "message": "已成功登出"
        }

    def verify_email(self, email: str, code: str) -> Dict[str, Any]:
        """验证邮箱"""
        verification = self.db.query(EmailVerification).filter(
            EmailVerification.email == email,
            EmailVerification.verification_code == code,
            EmailVerification.is_used == False,
            EmailVerification.expires_at > datetime.utcnow()
        ).first()

        if not verification:
            raise BadRequestError("验证码无效或已过期", error_code="INVALID_VERIFICATION_CODE")

        # 标记验证码为已使用
        verification.is_used = True
        
        # 更新用户邮箱验证状态
        user = verification.user
        user.email_verified = True

        self.db.commit()
        self.db.refresh(user)
        
        return {
            "user": user,
            "message": "邮箱验证成功"
        }

    def resend_verification(self, email: str) -> Dict[str, Any]:
        """重新发送验证码"""
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise BadRequestError("邮箱不存在", error_code="EMAIL_NOT_FOUND")

        if user.email_verified:
            raise BadRequestError("邮箱已验证", error_code="EMAIL_ALREADY_VERIFIED")

        # 检查发送频率限制
        self._check_verification_rate_limit(email)

        # 发送新的验证码
        success = self._send_verification_email_with_service(user)
        
        return {
            "message": f"验证码已发送至 {email}" if success else "发送验证码失败，请稍后重试"
        }

    # ===== 新增方法 =====
    
    def change_password(self, user_id: int, request: PasswordChangeRequest) -> Dict[str, str]:
        """修改密码"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise BadRequestError("用户不存在", error_code="USER_NOT_FOUND")

        # 验证旧密码
        if not self._verify_password(request.old_password, user.password_hash):
            raise UnauthorizedError("当前密码错误", error_code="INVALID_PASSWORD")

        # 更新密码
        user.password_hash = self._get_password_hash(request.new_password)
        user.password_changed_at = datetime.utcnow()
        
        self.db.commit()
        
        return {"message": "密码修改成功"}

    def forgot_password(self, request: ForgotPasswordRequest) -> Dict[str, str]:
        """忘记密码 - 发送重置邮件"""
        user = self.db.query(User).filter(User.email == request.email).first()
        if not user:
            # 安全考虑：不透露邮箱是否存在
            return {"message": "重置邮件已发送，请查收"}

        # 检查发送频率限制
        self._check_password_reset_rate_limit(user.id)

        # 创建重置令牌
        reset_token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=1)

        password_reset = PasswordReset(
            user_id=user.id,
            reset_token=reset_token,
            expires_at=expires_at
        )
        self.db.add(password_reset)
        self.db.commit()

        # 发送重置邮件
        success = self._send_password_reset_email_with_service(user, reset_token)

        return {"message": "重置邮件已发送，请查收" if success else "发送重置邮件失败，请稍后重试"}

    def reset_password(self, request: ResetPasswordRequest) -> Dict[str, str]:
        """重置密码"""
        reset_record = self.db.query(PasswordReset).filter(
            PasswordReset.reset_token == request.reset_token,
            PasswordReset.is_used == False,
            PasswordReset.expires_at > datetime.utcnow()
        ).first()

        if not reset_record:
            raise BadRequestError("重置令牌无效或已过期", error_code="INVALID_RESET_TOKEN")

        # 更新密码
        user = reset_record.user
        user.password_hash = self._get_password_hash(request.new_password)
        user.password_changed_at = datetime.utcnow()
        user.failed_login_attempts = 0  # 重置失败登录次数
        user.locked_until = None  # 解除账户锁定

        # 标记重置令牌为已使用
        reset_record.is_used = True

        self.db.commit()

        return {"message": "密码重置成功"}

    # ===== 私有辅助方法 =====
    
    def _check_registration_enabled(self):
        """检查注册是否启用"""
        if not settings.enable_registration:
            raise ForbiddenError("注册功能已关闭", error_code="REGISTRATION_DISABLED")

    def _validate_user_uniqueness(self, username: str, email: str):
        """验证用户唯一性"""
        existing_user = self.db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                raise ConflictError("用户名已存在", error_code="USERNAME_EXISTS")
            else:
                raise ConflictError("邮箱已注册", error_code="EMAIL_EXISTS")

    def _validate_email_domain(self, email: str):
        """验证邮箱域名"""
        allowed_domains = settings.allowed_email_domains_list
        if allowed_domains:
            domain = email.split('@')[1].lower()
            if domain not in allowed_domains:
                raise BadRequestError(f"不支持的邮箱域名，请使用：{', '.join(allowed_domains)}", error_code="INVALID_EMAIL_DOMAIN")

    def _validate_and_consume_invite_code(self, code: str) -> InviteCode:
        """验证并消费邀请码"""
        invite_code = self.db.query(InviteCode).filter(
            InviteCode.code == code,
            InviteCode.is_active == True,
            InviteCode.is_used == False
        ).first()

        if not invite_code:
            raise BadRequestError("邀请码无效或已使用", error_code="INVALID_INVITE_CODE")

        if invite_code.expires_at and invite_code.expires_at < datetime.utcnow():
            raise BadRequestError("邀请码已过期", error_code="INVITE_CODE_EXPIRED")

        return invite_code

    def _create_user(self, user_data: UserRegister, invite_code: InviteCode) -> User:
        """创建用户"""
        try:
            user = User(
                username=user_data.username,
                email=user_data.email,
                password_hash=self._get_password_hash(user_data.password),
                password_changed_at=datetime.utcnow()
            )
            self.db.add(user)
            self.db.flush()  # 获取用户ID

            # 标记邀请码为已使用
            invite_code.is_used = True
            invite_code.used_by = user.id
            invite_code.used_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(user)
            return user

        except IntegrityError:
            self.db.rollback()
            raise ConflictError("用户名或邮箱已存在", error_code="USER_ALREADY_EXISTS")

    def _send_verification_email_if_enabled(self, user: User) -> str:
        """如果启用了邮箱验证，发送验证邮件"""
        if settings.enable_email_verification:
            success = self._send_verification_email_with_service(user)
            return "验证邮件已发送，请查收您的邮箱" if success else "注册成功，但验证邮件发送失败"
        return "恭喜你，注册成功！"
            

    def _send_verification_email_with_service(self, user: User) -> bool:
        """使用邮件服务发送验证邮件"""
        try:
            # 检查发送频率
            if not self.email_service.can_send_email(self.db, user.email, "verification"):
                return False
            
            # 生成验证码
            verification_code = self.email_service.generate_verification_code()
            
            # 创建验证记录
            verification = EmailVerification(
                user_id=user.id,
                email=user.email,
                verification_code=verification_code,
                verification_type="registration",
                expires_at=datetime.utcnow() + timedelta(minutes=settings.verification_code_expire_minutes)
            )
            self.db.add(verification)
            self.db.commit()
            
            # 发送邮件
            return self.email_service.send_verification_email(
                user.email, 
                user.username, 
                verification_code
            )
            
        except Exception as e:
            print(f"⚠️ 发送验证邮件失败: {e}")
            self.db.rollback()
            return False

    def _send_password_reset_email_with_service(self, user: User, reset_token: str) -> bool:
        """使用邮件服务发送密码重置邮件"""
        try:
            return self.email_service.send_password_reset_email(
                user.email,
                user.username,
                reset_token
            )
        except Exception as e:
            print(f"⚠️ 发送密码重置邮件失败: {e}")
            return False

    def _get_user_by_username_or_email(self, identifier: str) -> Optional[User]:
        """通过用户名或邮箱获取用户"""
        return self.db.query(User).filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

    def _check_account_status(self, user: User):
        """检查账户状态"""
        if not user.is_active:
            raise UnauthorizedError("账户已被禁用", error_code="ACCOUNT_DISABLED")
        
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise UnauthorizedError("账户暂时锁定，请稍后再试", error_code="ACCOUNT_LOCKED")

    def _handle_failed_login(self, user: User):
        """处理登录失败"""
        user.failed_login_attempts += 1
        
        # 达到最大失败次数后锁定账户
        if user.failed_login_attempts >= settings.max_login_attempts:
            user.locked_until = datetime.utcnow() + timedelta(hours=settings.account_lock_duration_hours)
        
        self.db.commit()

    def _handle_successful_login(self, user: User):
        """处理登录成功"""
        user.last_login_at = datetime.utcnow()
        user.failed_login_attempts = 0
        user.locked_until = None
        self.db.commit()

    def _check_verification_rate_limit(self, email: str):
        """检查验证码发送频率限制"""
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        recent_count = self.db.query(EmailVerification).filter(
            EmailVerification.email == email,
            EmailVerification.created_at > one_minute_ago
        ).count()
        
        if recent_count >= 1:
            raise BadRequestError("发送过于频繁，请稍后再试", error_code="RATE_LIMIT_EXCEEDED")

    def _check_password_reset_rate_limit(self, user_id: int):
        """检查密码重置发送频率限制"""
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_count = self.db.query(PasswordReset).filter(
            PasswordReset.user_id == user_id,
            PasswordReset.created_at > one_hour_ago
        ).count()
        
        if recent_count >= 3:
            raise BadRequestError("密码重置请求过于频繁，请稍后再试", error_code="RATE_LIMIT_EXCEEDED")

    # ===== 密码和令牌相关方法 =====
    
    def _get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(plain_password, hashed_password)

    def _create_access_token(self, data: dict) -> str:
        """创建访问令牌"""
        from jose import jwt
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        to_encode = data.copy()
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)