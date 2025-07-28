"""
Backend v2 全局测试配置 - 真实环境事务回滚策略

基于 testing_strategy_standards.md 实现的真实 MySQL 环境测试配置
"""
import pytest
import os
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from datetime import datetime
import uuid

from src.main import app
from src.shared.dependencies import get_db
from src.shared.database import Base

# 导入所有模型以确保关系正确建立
from src.auth.models import User, InviteCode, EmailVerification, PasswordReset
from src.course.models import Semester, Course
from src.storage.models import (
    PhysicalFile, Folder, File, DocumentChunk, FileShare, 
    FileAccessLog, FileGroup, FileGroupMember, TemporaryFile
)
from src.chat.models import Chat, Message, MessageFileReference, MessageRAGSource
from src.admin.models import AuditLog
from src.auth.service import AuthService

# 加载测试环境配置
test_env_path = Path(__file__).parent / ".env.test"
if test_env_path.exists():
    load_dotenv(test_env_path)

# 真实 MySQL 数据库配置 - 使用环境变量
TEST_DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ========== 数据库 Fixtures ==========

@pytest.fixture(scope="session")
def db_engine():
    """创建测试数据库引擎 - 确保表结构存在"""
    # 不创建表，依赖 Alembic 迁移
    yield engine

@pytest.fixture(scope="function")
def db_session(db_engine):
    """创建数据库会话 - 事务回滚策略"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()  # 关键：自动回滚所有更改
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI 测试客户端"""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

# ========== 辅助函数 ==========

def get_password_hash(password: str) -> str:
    """获取密码哈希 - 用于测试用户创建"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    """创建访问令牌 - 用于认证测试"""
    from jose import jwt
    from datetime import datetime, timedelta
    from src.shared.config import settings
    
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

# ========== 用户管理 Fixtures ==========

@pytest.fixture(scope="function")
def admin_user(db_session: Session) -> User:
    """管理员用户 - 每个测试独立创建"""
    admin = User(
        username=os.getenv("TEST_ADMIN_USERNAME", "admin_test"),
        email="admin@584743.xyz",
        password_hash=get_password_hash(os.getenv("TEST_ADMIN_PASSWORD", "AdminTest123!")),
        role="admin",
        is_active=True,
        email_verified=True,  # 绕过邮箱验证
        password_changed_at=datetime.utcnow()
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin

@pytest.fixture(scope="function")
def regular_user(db_session: Session) -> User:
    """普通用户 - 用于权限测试"""
    user = User(
        username="user_test",
        email="user@584743.xyz", 
        password_hash=get_password_hash("UserTest123!"),
        role="user",
        is_active=True,
        email_verified=True,
        password_changed_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def unverified_user(db_session: Session) -> User:
    """未验证用户 - 用于邮箱验证测试"""
    user = User(
        username="unverified_test",
        email="unverified@584743.xyz",
        password_hash=get_password_hash("UnverifiedTest123!"),
        role="user",
        is_active=True,
        email_verified=False,  # 用于测试邮箱验证流程
        password_changed_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

# ========== 认证 Fixtures ==========

@pytest.fixture(scope="function")
def admin_token(admin_user: User) -> str:
    """管理员认证 Token"""
    return create_access_token(data={"sub": str(admin_user.id)})

@pytest.fixture(scope="function")
def admin_headers(admin_token: str) -> dict:
    """管理员认证头"""
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture(scope="function")
def user_token(regular_user: User) -> str:
    """普通用户认证 Token"""
    return create_access_token(data={"sub": str(regular_user.id)})

@pytest.fixture(scope="function")
def user_headers(user_token: str) -> dict:
    """普通用户认证头"""
    return {"Authorization": f"Bearer {user_token}"}

# ========== 测试数据 Fixtures ==========

@pytest.fixture(scope="function")
def valid_invite_code(db_session: Session, admin_user: User) -> InviteCode:
    """有效的邀请码 - 用于注册测试"""
    invite_code = InviteCode(
        code=f"TEST{uuid.uuid4().hex[:6].upper()}",
        description="pytest测试邀请码",
        is_active=True,
        is_used=False,
        created_by=admin_user.id
    )
    db_session.add(invite_code)
    db_session.commit()
    db_session.refresh(invite_code)
    return invite_code

@pytest.fixture(scope="function")
def expired_invite_code(db_session: Session, admin_user: User) -> InviteCode:
    """过期的邀请码 - 用于错误测试"""
    from datetime import datetime, timedelta
    
    invite_code = InviteCode(
        code=f"EXPIRED{uuid.uuid4().hex[:6].upper()}",
        description="pytest过期邀请码",
        is_active=True,
        is_used=False,
        expires_at=datetime.utcnow() - timedelta(days=1),  # 过期
        created_by=admin_user.id
    )
    db_session.add(invite_code)
    db_session.commit()
    db_session.refresh(invite_code)
    return invite_code

@pytest.fixture(scope="function")
def used_invite_code(db_session: Session, admin_user: User, regular_user: User) -> InviteCode:
    """已使用的邀请码 - 用于错误测试"""
    invite_code = InviteCode(
        code=f"USED{uuid.uuid4().hex[:6].upper()}",
        description="pytest已使用邀请码",
        is_active=True,
        is_used=True,
        used_by=regular_user.id,
        used_at=datetime.utcnow(),
        created_by=admin_user.id
    )
    db_session.add(invite_code)
    db_session.commit()
    db_session.refresh(invite_code)
    return invite_code

# ========== Mock服务 Fixtures ==========

@pytest.fixture(scope="function")
def mock_email_service():
    """Mock 邮件服务 - 记录调用但不实际发送"""
    from unittest.mock import patch
    
    with patch('src.auth.service.AuthService._send_verification_email') as mock_send:
        mock_send.return_value = True
        
        # 记录调用参数用于验证
        mock_send.call_history = []
        
        def side_effect(*args, **kwargs):
            mock_send.call_history.append((args, kwargs))
            return True
            
        mock_send.side_effect = side_effect
        yield mock_send

@pytest.fixture(scope="function") 
def mock_password_reset_email():
    """Mock 密码重置邮件"""
    from unittest.mock import patch
    
    with patch('src.auth.service.AuthService._send_password_reset_email') as mock_send:
        mock_send.return_value = True
        yield mock_send

# ========== 辅助测试函数 ==========

def assert_success_response(response, expected_data_keys=None, expected_status=200):
    """标准成功响应断言"""
    assert response.status_code == expected_status
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    
    if expected_data_keys:
        for key in expected_data_keys:
            assert key in data["data"]

def assert_error_response(response, expected_status=400, expected_error_code=None):
    """标准错误响应断言"""
    assert response.status_code == expected_status
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    
    if expected_error_code:
        assert data["error"]["code"] == expected_error_code

# ========== Service 测试辅助 ==========

@pytest.fixture(scope="function")
def auth_service(db_session: Session) -> AuthService:
    """Auth服务实例 - 用于单元测试"""
    return AuthService(db_session)