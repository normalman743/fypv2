"""Auth模块的SQLAlchemy模型定义"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, DECIMAL, ForeignKey, func
from sqlalchemy.orm import relationship
from src.shared.database import Base


class User(Base):
    """用户模型 - 基于现有backend/app/models/user.py扩展"""
    __tablename__ = "users"
    
    # ===== 基本信息 =====
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), default="user", index=True)  # user, admin
    
    # ===== 用户余额和消费 =====
    balance = Column(DECIMAL(10, 2), default=1.00)
    total_spent = Column(DECIMAL(10, 2), default=0.00)
    
    # ===== 用户偏好设置 =====
    preferred_language = Column(String(20), default="zh_CN")
    preferred_theme = Column(String(20), default="light")
    last_opened_semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=True)
    
    # ===== 状态字段 =====
    is_active = Column(Boolean, default=True)
    
    # ===== 新增安全字段 =====
    email_verified = Column(Boolean, default=False, index=True)
    last_login_at = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True, index=True)
    password_changed_at = Column(DateTime, nullable=True)
    
    # ===== 时间戳 =====
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # ===== 关系（保持与现有backend兼容） =====
    courses = relationship("Course", back_populates="user")
    files = relationship("File", back_populates="user")
    chats = relationship("Chat", back_populates="user")
    created_invite_codes = relationship("InviteCode", foreign_keys="InviteCode.created_by", back_populates="creator")
    used_invite_codes = relationship("InviteCode", foreign_keys="InviteCode.used_by", back_populates="user")
    
    # ===== 新增关系 =====
    email_verifications = relationship("EmailVerification", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordReset", back_populates="user", cascade="all, delete-orphan")
    last_opened_semester = relationship("Semester", foreign_keys=[last_opened_semester_id])
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class EmailVerification(Base):
    """邮箱验证模型"""
    __tablename__ = "email_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email = Column(String(100), nullable=False)
    verification_code = Column(String(6), nullable=False, index=True)
    verification_type = Column(String(20), nullable=False)  # registration, email_change
    expires_at = Column(DateTime, nullable=False, index=True)
    is_used = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    user = relationship("User", back_populates="email_verifications")
    
    def __repr__(self):
        return f"<EmailVerification(id={self.id}, email='{self.email}', type='{self.verification_type}')>"


class PasswordReset(Base):
    """密码重置模型"""
    __tablename__ = "password_resets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reset_token = Column(String(36), nullable=False, unique=True, index=True)  # UUID格式
    expires_at = Column(DateTime, nullable=False, index=True)  # 1小时过期
    is_used = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    user = relationship("User", back_populates="password_resets")
    
    def __repr__(self):
        return f"<PasswordReset(id={self.id}, user_id={self.user_id}, token='{self.reset_token[:8]}...')>"


# 为了向后兼容，可能需要的其他模型引用
# 这些模型将在对应模块开发时实现

class InviteCode(Base):
    """邀请码模型 - 临时定义，用于Auth模块依赖"""
    __tablename__ = "invite_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), nullable=False, unique=True, index=True)
    description = Column(String(200), nullable=True)
    is_used = Column(Boolean, default=False, index=True)
    used_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    user = relationship("User", foreign_keys=[used_by])
    
    def __repr__(self):
        return f"<InviteCode(id={self.id}, code='{self.code}', is_used={self.is_used})>"