"""
pytest 配置文件 - 共享的 fixtures 和测试配置
"""
import pytest
import os
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import Mock
from dotenv import load_dotenv

from app.main import app
from app.dependencies import get_db
from app.models.database import Base
from app.models.user import User
from app.core.security import create_access_token, get_password_hash

# 加载测试环境配置
test_env_path = Path(__file__).parent / ".env.test"
if test_env_path.exists():
    load_dotenv(test_env_path)

# 测试数据库配置
TEST_DATABASE_URL = "sqlite:///./test.db"  # 使用内存数据库更快: "sqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ========== 数据库 Fixtures ==========

@pytest.fixture(scope="session")
def db_engine():
    """创建测试数据库引擎"""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """创建数据库会话 - 每个测试后回滚"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
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


# ========== 用户 Fixtures ==========

@pytest.fixture(scope="function")
def default_admin_user(db_session: Session) -> User:
    """获取或创建默认管理员用户 - 使用.env.test配置"""
    # 从环境变量获取测试admin配置
    admin_username = os.getenv("TEST_ADMIN_USERNAME", "admin1")
    admin_password = os.getenv("TEST_ADMIN_PASSWORD", "admin123456")
    
    # 尝试获取现有的admin用户
    admin = db_session.query(User).filter(User.username == admin_username).first()
    
    if not admin:
        # 创建真实的admin用户
        admin = User(
            username=admin_username,
            email=f"{admin_username}@test.com",
            password_hash=get_password_hash(admin_password),  # 真实密码哈希
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
    
    return admin


@pytest.fixture(scope="function")
def admin_token(default_admin_user: User) -> str:
    """生成管理员认证token"""
    return create_access_token(data={"sub": str(default_admin_user.id)})


@pytest.fixture(scope="function")
def admin_headers(admin_token: str) -> dict:
    """管理员认证头"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def regular_user(db_session: Session) -> User:
    """创建普通用户 - 使用.env.test配置"""
    # 从环境变量获取测试用户配置
    user_username = os.getenv("TEST_USER_USERNAME", "user")
    user_password = os.getenv("TEST_USER_PASSWORD", "user123456")
    
    user = User(
        username=user_username,
        email=f"{user_username}@test.com",
        password_hash=get_password_hash(user_password),  # 真实密码哈希
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def regular_token(regular_user: User) -> str:
    """普通用户token"""
    return create_access_token(data={"sub": str(regular_user.id)})


@pytest.fixture(scope="function")
def regular_headers(regular_token: str) -> dict:
    """普通用户认证头"""
    return {"Authorization": f"Bearer {regular_token}"}


# ========== Mock Fixtures ==========

@pytest.fixture
def mock_unified_file_service():
    """Mock UnifiedFileService"""
    mock_service = Mock()
    mock_service.upload_file.return_value = Mock(
        id=1,
        original_name="test.pdf",
        file_type="pdf",
        scope="global",
        visibility="public",
        is_processed=False,
        processing_status="pending",
        created_at="2025-01-27T10:00:00Z",
        file_size=1024,
        description="测试文件",
        tags=["test"]
    )
    return mock_service


# ========== 测试数据 Fixtures ==========

@pytest.fixture
def sample_file_upload_data():
    """文件上传测试数据"""
    return {
        "file": ("test.pdf", b"fake pdf content", "application/pdf"),
        "description": "测试文件上传",
        "tags": '["test", "admin"]',
        "visibility": "public"
    }