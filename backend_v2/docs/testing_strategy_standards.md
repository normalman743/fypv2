# Backend v2 测试策略标准

> 基于真实环境测试的最佳实践，确保生产环境一致性

## 🎯 核心测试理念

### 1. 真实环境优先
- **数据库**：使用真实 MySQL 数据库，与生产环境完全一致
- **配置**：使用实际的 Alembic 迁移和环境配置
- **依赖**：尽可能使用真实服务，必要时才 Mock

### 2. 数据清洁策略
- **事务回滚**：每个测试在独立事务中运行，自动回滚
- **无副作用**：测试间完全隔离，不产生数据残留
- **快速重置**：无需重建数据库，保持高效执行

### 3. 分层测试覆盖
```
API 集成测试 (70%) - 完整HTTP请求流程
     ▲
Service 单元测试 (20%) - 业务逻辑验证  
     ▲
Schema 验证测试 (10%) - 数据验证规则
```

### 4. FastAPI 2024 最佳实践测试
- **Service API 装饰器测试**: 验证 @service_api 装饰器正确生成OpenAPI文档
- **依赖注入测试**: 确保返回正确的User对象而非字典
- **响应格式测试**: 验证 BaseResponse[T] 结构的 message/data 分离
- **异常处理测试**: 验证Service层异常正确映射到HTTP响应

### 5. 未实现功能处理策略
- **原则**: 不使用Mock，不测试未实现的功能
- **跳过测试**: 未实现的服务功能直接不编写测试
- **配置禁用**: 通过配置禁用未实现功能，确保核心流程可测试

## 📁 测试项目结构

```
backend_v2/tests/
├── conftest.py              # 全局测试配置
├── test_{module}_unit.py    # 单元测试（Service层）
├── test_{module}_api.py     # API集成测试 
├── fixtures/               # 测试数据fixtures
│   ├── users.py
│   └── {module}_data.py
└── .env.test              # 测试环境配置
```

## ⚙️ 测试环境配置

### 1. 数据库配置
```python
# .env.test
DATABASE_URL=mysql+pymysql://root:Root@123456@localhost:3306/campus_llm_db_v2

# 测试用户配置
TEST_ADMIN_USERNAME=admin_test
TEST_ADMIN_PASSWORD=AdminTest123!
TEST_USER_USERNAME=user_test  
TEST_USER_PASSWORD=UserTest123!

# 功能开关配置
ENABLE_EMAIL_VERIFICATION=false  # 禁用邮件验证功能

# FastAPI 2024 最佳实践测试配置
TEST_SERVICE_API_DECORATOR=true   # 启用 Service API 装饰器测试
TEST_DEPENDENCY_INJECTION=true    # 启用依赖注入类型测试
TEST_RESPONSE_FORMAT=true         # 启用响应格式测试
```

### 2. conftest.py 标准配置
```python
"""
全局测试配置 - 真实环境事务回滚策略
"""
import pytest
import os
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

from src.main import app
from src.shared.dependencies import get_db
from src.shared.database import Base
from src.auth.models import User, InviteCode

# 加载测试环境配置
test_env_path = Path(__file__).parent / ".env.test"
if test_env_path.exists():
    load_dotenv(test_env_path)

# 真实 MySQL 数据库配置
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/campus_llm_db_v2")

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
```

## 👤 用户管理策略

### 1. 测试用户 Fixtures
```python
# fixtures/users.py
@pytest.fixture(scope="function")
def admin_user(db_session: Session) -> User:
    """管理员用户 - 每个测试独立创建"""
    admin = User(
        username=os.getenv("TEST_ADMIN_USERNAME", "admin_test"),
        email="admin@test.local",
        password_hash=get_password_hash(os.getenv("TEST_ADMIN_PASSWORD", "AdminTest123!")),
        role="admin",
        is_active=True,
        email_verified=True  # 绕过邮箱验证
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin

@pytest.fixture(scope="function")
def regular_user(db_session: Session) -> User:
    """普通用户 - 用于权限测试"""
    user = User(
        username=os.getenv("TEST_USER_USERNAME", "user_test"),
        email="user@test.local", 
        password_hash=get_password_hash(os.getenv("TEST_USER_PASSWORD", "UserTest123!")),
        role="user",
        is_active=True,
        email_verified=True
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
        email="unverified@test.local",
        password_hash=get_password_hash("UnverifiedTest123!"),
        role="user",
        is_active=True,
        email_verified=False  # 用于测试邮箱验证流程
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
```

### 2. 认证 Fixtures
```python
@pytest.fixture(scope="function")
def admin_token(admin_user: User) -> str:
    """管理员认证 Token"""
    return create_access_token(data={"sub": str(admin_user.id)})

@pytest.fixture(scope="function")
def admin_headers(admin_token: str) -> dict:
    """管理员认证头"""
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture(scope="function")
def user_headers(regular_user: User) -> dict:
    """普通用户认证头"""
    token = create_access_token(data={"sub": str(regular_user.id)})
    return {"Authorization": f"Bearer {token}"}
```

## 🔧 Mock 服务策略

### 1. 邮件服务 Mock
```python
# mocks/email_mock.py
@pytest.fixture(scope="function")
def mock_email_service():
    """Mock 邮件服务 - 记录调用但不实际发送"""
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
    with patch('src.auth.service.AuthService._send_password_reset_email') as mock_send:
        mock_send.return_value = True
        yield mock_send
```

### 2. 文件存储 Mock（未来模块使用）
```python
@pytest.fixture(scope="function")
def mock_file_storage():
    """Mock 文件存储服务"""
    mock = Mock()
    mock.upload_file.return_value = {
        "file_id": "test_file_123",
        "file_url": "http://test.local/files/test_file_123",
        "file_size": 1024
    }
    yield mock
```

## 📋 测试编写标准

### 1. 单元测试模式 (test_{module}_unit.py)
```python
class TestAuthService:
    """Service 层单元测试"""
    
    def test_password_validation_success(self, db_session):
        """测试密码验证逻辑 - 成功路径"""
        service = AuthService(db_session)
        # 测试纯业务逻辑，不涉及HTTP请求
        
    def test_password_validation_failure(self, db_session):
        """测试密码验证逻辑 - 失败路径"""
        service = AuthService(db_session)
        with pytest.raises(BadRequestError):
            # 测试异常处理逻辑
```

### 2. API 集成测试模式 (test_{module}_api.py)
```python
class TestAuthAPI:
    """Auth API 集成测试"""
    
    def test_register_success(self, client, mock_email_service):
        """测试用户注册 - 成功路径"""
        # 需要真实邀请码
        invite_code = self._create_invite_code(client.app.dependency_overrides[get_db]())
        
        response = client.post("/api/v1/auth/register", json={
            "username": "newuser123",
            "email": "newuser@test.local",
            "password": "NewUser123!",
            "invite_code": invite_code.code
        })
        
        assert response.status_code == 201  # 注意状态码
        data = response.json()
        assert data["success"] is True
        assert "user" in data["data"]
        assert "message" in data  # FastAPI 2024: 验证 message 字段在顶层
        assert data["message"] is not None
        
        # 验证邮件服务被调用
        assert mock_email_service.called
        
    def test_register_invalid_invite_code(self, client):
        """测试无效邀请码注册"""
        response = client.post("/api/v1/auth/register", json={
            "username": "newuser123", 
            "email": "newuser@test.local",
            "password": "NewUser123!",
            "invite_code": "INVALID123"
        })
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        
    def test_login_success(self, client, regular_user):
        """测试用户登录 - 成功路径"""
        response = client.post("/api/v1/auth/login", json={
            "username": regular_user.username,
            "password": os.getenv("TEST_USER_PASSWORD", "UserTest123!")
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "user" in data["data"]
        
        # FastAPI 2024: 验证数据结构
        assert isinstance(data["data"]["user"], dict)
        assert "id" in data["data"]["user"]
        assert "username" in data["data"]["user"]
```

### 3. 权限测试模式
```python
def test_admin_only_endpoint(self, client, user_headers):
    """测试管理员权限端点 - 普通用户无权限"""
    response = client.post("/api/v1/admin/invite-codes", 
                          json={"description": "test"}, 
                          headers=user_headers)
    assert response.status_code == 403

def test_admin_endpoint_success(self, client, admin_headers):
    """测试管理员权限端点 - 管理员有权限"""
    response = client.post("/api/v1/admin/invite-codes",
                          json={"description": "test"},
                          headers=admin_headers)
    assert response.status_code == 200
```

### 4. FastAPI 2024 最佳实践测试类
```python
class TestFastAPIBestPractices:
    """FastAPI 2024 最佳实践验证测试"""
    
    def test_service_api_decorator_generates_openapi_docs(self, client):
        """测试 Service API 装饰器正确生成 OpenAPI 文档"""
        # 获取 OpenAPI 规范
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        
        # 验证使用 @service_api 装饰器的端点有完整的响应文档
        register_path = openapi_spec["paths"]["/api/v1/auth/register"]["post"]
        
        # 检查成功响应
        assert "201" in register_path["responses"]
        assert register_path["responses"]["201"]["description"]
        
        # 检查错误响应（基于 Service 异常自动生成）
        assert "400" in register_path["responses"]
        assert "403" in register_path["responses"]
        assert "409" in register_path["responses"]
        
        # 验证错误响应结构
        error_response = register_path["responses"]["400"]
        assert "$ref" in error_response["content"]["application/json"]["schema"]
        
    def test_dependency_injection_returns_user_objects(self, client, regular_user):
        """测试依赖注入返回正确的 User 对象（而非字典）"""
        # 获取用户认证令牌
        token_response = client.post("/api/v1/auth/login", json={
            "username": regular_user.username,
            "password": os.getenv("TEST_USER_PASSWORD", "UserTest123!")
        })
        token = token_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 测试需要用户认证的端点
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        # 验证返回的用户数据包含完整的 User 对象信息
        assert "id" in data["data"]
        assert "username" in data["data"]
        assert "email" in data["data"]
        assert isinstance(data["data"]["id"], int)  # 确保是正确的数据类型
        
    def test_response_format_message_data_separation(self, client, mock_email_service):
        """测试响应格式正确分离 message 和 data"""
        # 创建邀请码
        invite_code = self._create_invite_code(client.app.dependency_overrides[get_db]())
        
        # 执行注册请求
        response = client.post("/api/v1/auth/register", json={
            "username": "testuser123",
            "email": "test@test.local",
            "password": "TestUser123!",
            "invite_code": invite_code.code
        })
        
        assert response.status_code == 201
        data = response.json()
        
        # 验证 BaseResponse[T] 结构
        assert "success" in data
        assert "data" in data
        assert "message" in data  # message 在顶层，不在 data 内
        
        # 验证数据结构
        assert isinstance(data["success"], bool)
        assert isinstance(data["data"], dict)
        assert isinstance(data["message"], str) or data["message"] is None
        
        # 验证 data 载荷结构
        assert "user" in data["data"]
        assert isinstance(data["data"]["user"], dict)
        
    def test_service_exceptions_mapping_to_http_responses(self, client):
        """测试 Service 层异常正确映射到 HTTP 响应"""
        # 测试 BadRequestError → 400
        response = client.post("/api/v1/auth/register", json={
            "username": "invalid name with spaces",  # 触发 BadRequestError
            "email": "test@test.local",
            "password": "TestUser123!",
            "invite_code": "INVALID123"
        })
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        assert data["error"]["code"]  # 错误码存在
        assert data["error"]["message"]  # 错误消息存在
        
        # 测试 ConflictError → 409 (用户名冲突)
        # 需要先创建一个用户，然后尝试用相同用户名注册
        # ...
        
    def test_openapi_examples_completeness(self, client):
        """测试 OpenAPI 文档包含完整的请求/响应示例"""
        response = client.get("/openapi.json")
        openapi_spec = response.json()
        
        # 检查响应模型是否包含示例
        components = openapi_spec.get("components", {})
        schemas = components.get("schemas", {})
        
        # 检查关键响应模型有示例
        if "RegisterResponse" in schemas:
            register_schema = schemas["RegisterResponse"]
            # 检查是否有 examples 或 example
            assert "examples" in register_schema or "example" in register_schema
```

## 🧪 测试数据管理

### 1. 测试数据创建原则
```python
def _create_invite_code(self, db_session: Session, **kwargs) -> InviteCode:
    """创建测试邀请码 - 辅助函数"""
    defaults = {
        "code": f"TEST{uuid.uuid4().hex[:6].upper()}",
        "description": "pytest测试邀请码",
        "is_active": True,
        "is_used": False,
        "created_by": 1  # 假设存在管理员用户
    }
    defaults.update(kwargs)
    
    invite_code = InviteCode(**defaults)
    db_session.add(invite_code)
    db_session.commit()
    db_session.refresh(invite_code)
    return invite_code
```

### 2. 断言标准（FastAPI 2024最佳实践）
```python
# API 响应格式断言 - 支持 BaseResponse[T] 结构
def assert_success_response(response, expected_status=200, expected_data_keys=None, has_message=None):
    """标准成功响应断言 - 支持 message/data 分离"""
    assert response.status_code == expected_status
    data = response.json()
    
    # 验证 BaseResponse[T] 结构
    assert data["success"] is True
    assert "data" in data
    assert isinstance(data["data"], dict)
    
    # 验证 message 字段（顶层，可选）
    if has_message is True:
        assert "message" in data
        assert isinstance(data["message"], str)
    elif has_message is False:
        assert data.get("message") is None
    
    # 验证数据载荷
    if expected_data_keys:
        for key in expected_data_keys:
            assert key in data["data"], f"Key '{key}' not found in response data"

def assert_error_response(response, expected_status=400, expected_error_code=None):
    """标准错误响应断言 - 支持 ErrorResponse 结构"""
    assert response.status_code == expected_status
    data = response.json()
    
    # 验证错误响应结构
    assert data["success"] is False
    assert "error" in data
    assert isinstance(data["error"], dict)
    
    # 验证错误详情
    assert "code" in data["error"]
    assert "message" in data["error"]
    assert isinstance(data["error"]["code"], str)
    assert isinstance(data["error"]["message"], str)
    
    if expected_error_code:
        assert data["error"]["code"] == expected_error_code

def assert_openapi_documentation_complete(openapi_spec, endpoint_path, http_method):
    """验证 OpenAPI 文档完整性 - Service API 装饰器生成的文档"""
    paths = openapi_spec.get("paths", {})
    assert endpoint_path in paths, f"Endpoint {endpoint_path} not found in OpenAPI spec"
    
    endpoint = paths[endpoint_path]
    assert http_method.lower() in endpoint, f"Method {http_method} not found for {endpoint_path}"
    
    method_spec = endpoint[http_method.lower()]
    
    # 验证基本信息
    assert "summary" in method_spec
    assert "responses" in method_spec
    assert "200" in method_spec["responses"] or "201" in method_spec["responses"]
    
    # 验证错误响应（通过 Service API 装饰器自动生成）
    error_statuses = ["400", "401", "403", "404", "409", "422"]
    has_error_response = any(status in method_spec["responses"] for status in error_statuses)
    assert has_error_response, f"No error responses found for {endpoint_path}"

def assert_user_object_structure(user_data):
    """验证用户对象结构 - 确保依赖注入返回正确类型"""
    required_fields = ["id", "username", "email", "role", "created_at"]
    
    for field in required_fields:
        assert field in user_data, f"Required field '{field}' missing from user object"
    
    # 验证数据类型
    assert isinstance(user_data["id"], int)
    assert isinstance(user_data["username"], str)
    assert isinstance(user_data["email"], str)
    assert user_data["role"] in ["admin", "user"]
```

## 🚀 测试执行策略

### 1. 本地开发测试
```bash
# 运行所有测试
pytest tests/ -v

# 运行特定模块测试
pytest tests/test_auth_api.py -v

# 运行特定测试类
pytest tests/test_auth_api.py::TestAuthAPI -v

# 运行特定测试方法
pytest tests/test_auth_api.py::TestAuthAPI::test_register_success -v

# 并行测试（小心数据库冲突）
pytest tests/ -n 4  # 需要 pytest-xdist
```

### 2. CI/CD 测试配置
```yaml
# .github/workflows/test.yml 示例
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: Root@123456
          MYSQL_DATABASE: campus_llm_db_v2
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3
    
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r backend_v2/requirements.txt
          pip install pytest pytest-asyncio
      
      - name: Run Alembic migrations
        run: |
          cd backend_v2
          alembic upgrade head
      
      - name: Run tests
        run: |
          cd backend_v2
          pytest tests/ -v --tb=short
```

## 📊 测试覆盖率和质量标准

### 1. 覆盖率目标
- **API 端点覆盖率**: 100%（所有路由都有测试）
- **业务逻辑覆盖率**: 90%（Service 层核心方法）
- **错误处理覆盖率**: 80%（主要异常路径）

### 2. 测试质量检查（FastAPI 2024最佳实践）
```python
# 每个模块测试文件必须包含的测试类型：
class TestModuleUnit:        # Service 层单元测试
class TestModuleAPI:         # API 集成测试
class TestModulePermissions: # 权限和安全测试
class TestModuleErrors:      # 错误处理测试
class TestFastAPIBestPractices:  # FastAPI 2024 最佳实践验证测试

# 每个测试类的必要测试方法：
class TestFastAPIBestPractices:
    def test_service_api_decorator_generates_openapi_docs(self, client): pass
    def test_dependency_injection_returns_user_objects(self, client, regular_user): pass  
    def test_response_format_message_data_separation(self, client): pass
    def test_service_exceptions_mapping_to_http_responses(self, client): pass
    def test_openapi_examples_completeness(self, client): pass
```

### 3. 性能测试（可选）
```python
@pytest.mark.performance
def test_api_response_time(self, client):
    """测试API响应时间"""
    import time
    
    start_time = time.time()
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    end_time = time.time()
    
    assert response.status_code == 200
    assert (end_time - start_time) < 1.0  # 1秒内响应
```

## 🎯 成功标准

一个合格的测试套件应该：

1. **真实环境**：使用真实 MySQL 数据库，模拟生产环境
2. **清洁隔离**：测试间无副作用，数据自动清理
3. **覆盖完整**：API 端点、业务逻辑、错误处理全覆盖
4. **执行稳定**：多次运行结果一致，不依赖外部状态
5. **文档价值**：测试用例本身就是 API 使用文档

---

**Auth 模块测试已按此标准实现，后续模块请严格遵循此测试策略。**