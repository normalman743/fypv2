from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.user import User
from app.models.invite_code import InviteCode
from app.schemas.user import UserRegister, UserLogin, UserUpdate
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings
from app.services.email_service import email_service
from app.core.exceptions import (
    BadRequestError, 
    ConflictError, 
    ForbiddenError,
    UnauthorizedError
)

class AuthService:
    # 声明每个方法可能抛出的异常
    METHOD_EXCEPTIONS = {
        'register': {BadRequestError, ConflictError, ForbiddenError},
        'login': {UnauthorizedError},
        'update_user': {BadRequestError, ConflictError, ForbiddenError},
        'verify_email': {BadRequestError},
        'resend_verification': {BadRequestError}
    }
    
    def __init__(self, db: Session):
        self.db = db

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
        self._send_verification_email_if_enabled(user)
        if settings.email_verification_enabled:
            message = "注册成功！验证邮件已发送，如果没有收到，请检查垃圾邮件或稍后再试。"
        else:
            message = "注册成功！"

        return {
            "user": user,
            "message": message
        }


    def login(self, credentials: UserLogin) -> Dict[str, Any]:
        """用户登录流程"""
        # 1. 查找用户
        user = self._find_user_by_credentials(credentials.username)

        # 2. 验证密码
        self._verify_password(credentials.password, user)

        # 3. 检查用户是否激活
        self._check_user_active(user)

        # 4. 创建访问令牌
        access_token = create_access_token(data={"sub": user.id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }

    def update_user(self, user_id: int, update_data: UserUpdate) -> User:
        """更新用户信息"""
        user = self._get_user_by_id(user_id)

        # 检查用户名唯一性
        if update_data.username:
            self._validate_username_unique(update_data.username, user_id)
        
        if update_data.email:
            self._validate_email_change(update_data.email, user)

        # 更新用户字段
        self._update_user_fields(user, update_data)
        
        return user

    def verify_email(self, email: str, code: str) -> User:
        """验证邮箱"""
        user = email_service.verify_code(self.db, email, code)
        if not user:
            raise BadRequestError("验证码无效或已过期", "INVALID_VERIFICATION_CODE")
        return user

    def resend_verification(self, email: str) -> bool:
        """重新发送验证码"""
        if not settings.email_verification_enabled:
            raise BadRequestError("邮箱验证功能未启用", "EMAIL_VERIFICATION_DISABLED")

        return email_service.resend_verification(self.db, email)

    # ===== Private Methods =====

    def _check_registration_enabled(self):
        """检查注册是否启用"""
        if not settings.registration_enabled:
            raise ForbiddenError("注册功能已关闭")

    def _validate_user_uniqueness(self, username: str, email: str):

        if self.db.query(User).filter(User.username == username).first():
            raise ConflictError("用户名已存在")
        
        if self.db.query(User).filter(User.email == email).first():
            raise ConflictError("邮箱已存在")

    def _validate_email_domain(self, email: str):
        """验证邮箱域名"""
        if not settings.email_verification_enabled or not settings.allowed_email_domains_list:
            return
        
        email_domain = email.split('@')[-1] if '@' in email else ""
        email_domain_valid = any(
            email_domain == domain or email_domain.endswith(f".{domain}")
            for domain in settings.allowed_email_domains_list
        )
        
        if not email_domain_valid:
            raise BadRequestError(
                f"邮箱域名必须是: {', '.join(settings.allowed_email_domains_list)}",
                "INVALID_EMAIL_DOMAIN"
            )

    def _validate_and_consume_invite_code(self, invite_code: str) -> Optional[InviteCode]:
        """验证并消耗邀请码"""
        if not settings.registration_invite_code_verification:
            return None
        
        invite_code_obj = self.db.query(InviteCode).filter(
            InviteCode.code == invite_code,
            InviteCode.is_used == False,
            InviteCode.expires_at > datetime.now()
        ).with_for_update().first()
        
        if not invite_code_obj:
            raise BadRequestError("邀请码无效或已过期", "INVALID_INVITE_CODE")

        return invite_code_obj

    def _create_user(self, user_data: UserRegister, invite_code_obj: Optional[InviteCode]) -> User:
        """创建用户"""
        try:
            hashed_password = get_password_hash(user_data.password)
            user = User(
                username=user_data.username,
                email=user_data.email,
                password_hash=hashed_password,
                role="user"
            )
            self.db.add(user)

            # 标记邀请码为已使用
            if invite_code_obj:
                invite_code_obj.is_used = True
                invite_code_obj.used_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(user)

            # 标记邀请码使用者
            if invite_code_obj:
                invite_code_obj.used_by = user.id
                self.db.commit()
            
            return user
            
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("(7�1%��X(�pn")

    def _send_verification_email_if_enabled(self, user: User):
        """发送验证邮件（如果启用）"""
        if settings.email_verification_enabled:
            email_sent = email_service.send_verification_email(self.db, user)
            if not email_sent:
                import logging
                logging.error(f"Failed to send verification email to {user.email}")

    def _find_user_by_credentials(self, username: str) -> User:
        """根据用户名或邮箱查找用户"""
        user = self.db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            raise UnauthorizedError("(用户未找到")

        return user

    def _verify_password(self, password: str, user: User):
        """验证密码"""
        if not verify_password(password, user.password_hash):
            raise UnauthorizedError("(密码错误)")

    def _check_user_active(self, user: User):
        """检查用户是否激活"""
        if not user.is_active:
            raise UnauthorizedError("(用户未激活)")

    def _get_user_by_id(self, user_id: int) -> User:
        """根据ID查找用户"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise BadRequestError("(用户未找到)", "USER_NOT_FOUND")
        return user

    def _validate_username_unique(self, username: str, current_user_id: int):
        """验证用户名唯一性"""
        existing_user = self.db.query(User).filter(
            User.username == username, 
            User.id != current_user_id
        ).first()
        
        if existing_user:
            raise ConflictError("(用户名已存在)")

    def _validate_email_change(self, email: str, current_user: User):
        """验证邮箱更改"""
        if email == current_user.email:
            return

        # 如果启用邮箱验证
        if settings.email_verification_enabled:
            raise ForbiddenError("邮箱验证已启用")

        # 其他逻辑
        existing_user = self.db.query(User).filter(
            User.email == email,
            User.id != current_user.id
        ).first()
        
        if existing_user:
            raise ConflictError("(邮箱已存在)")

    def _update_user_fields(self, user: User, update_data: UserUpdate):
        """更新用户字段"""
        update_fields = update_data.model_dump(exclude_unset=True)
        
        for field, value in update_fields.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)