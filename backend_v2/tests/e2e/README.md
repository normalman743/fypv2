# Campus LLM System v2 - End-to-End测试框架

## 📖 概述

这是Campus LLM System v2的End-to-End(E2E)测试框架，采用**API2Function**的设计理念，为系统的完整业务流程提供自动化测试。

## 🏗️ 架构设计

### API2Function模式
- **API客户端封装**: 将每个REST API端点封装为Python方法
- **测试数据工厂**: 自动生成各种测试数据
- **业务流程测试**: 测试完整的用户操作流程
- **权限隔离验证**: 确保用户数据安全隔离

### 测试分层
```
tests/e2e/
├── api_client.py       # API客户端封装 (核心)
├── factories.py        # 测试数据工厂
├── fixtures.py         # pytest fixtures
├── base.py            # 测试基类和断言
├── config.py          # 测试配置
├── conftest.py        # pytest配置
└── test_*.py          # 具体测试用例
```

## 🚀 快速开始

### 1. 安装依赖
```bash
cd backend_v2
source v2env/bin/activate
pip install pytest requests faker pytest-html pytest-xdist
```

### 2. 启动API服务器
```bash
# 在另一个终端
cd backend_v2
source v2env/bin/activate
uvicorn src.main:app --reload --port 8001
```

### 3. 运行测试

#### 使用测试脚本（推荐）
```bash
# 运行所有E2E测试
python run_e2e_tests.py

# 只运行冒烟测试
python run_e2e_tests.py --smoke-only

# 运行指定模块测试
python run_e2e_tests.py --module auth
python run_e2e_tests.py --module course

# 生成HTML报告
python run_e2e_tests.py --html report.html

# 并行运行
python run_e2e_tests.py --parallel 4

# 调试模式
python run_e2e_tests.py --debug --verbose
```

#### 直接使用pytest
```bash
# 运行所有E2E测试
python -m pytest tests/e2e/ -v

# 运行冒烟测试
python -m pytest tests/e2e/ -m smoke -v

# 运行特定模块
python -m pytest tests/e2e/ -m auth -v
python -m pytest tests/e2e/ -m course -v

# 运行特定测试文件
python -m pytest tests/e2e/test_user_workflows.py -v
```

## 📋 测试分类

### 按功能模块
- `auth`: 认证相关测试（注册、登录、权限）
- `admin`: 管理功能测试（邀请码、审计日志）
- `course`: 课程管理测试（学期、课程）
- `storage`: 存储管理测试（文件、文件夹）
- `chat`: 聊天功能测试（对话、消息）
- `ai`: AI功能测试（向量化、RAG）

### 按测试类型
- `smoke`: 冒烟测试 - 核心功能快速验证
- `integration`: 集成测试 - 跨模块功能验证
- `security`: 安全测试 - 权限控制验证
- `workflow`: 工作流测试 - 完整业务流程

## 🧪 测试用例示例

### 完整用户注册流程
```python
def test_complete_user_registration_flow(self, client, admin_client):
    # 1. 管理员创建邀请码
    invite_response = admin_client.create_invite_code(
        description="E2E测试邀请码"
    )
    
    # 2. 用户注册
    user_response = client.register(
        username="testuser",
        email="test@example.com",
        password="TestPass123!",
        invite_code=invite_response["data"]["invite_code"]["code"]
    )
    
    # 3. 邮箱验证
    client.verify_email("test@example.com", "123456")
    
    # 4. 用户登录
    login_response = client.login("testuser", "TestPass123!")
    
    # 5. 获取用户信息
    profile = client.get_me()
    
    # 断言验证
    assert login_response["success"] == True
    assert profile["data"]["username"] == "testuser"
```

### 文件上传和下载流程
```python
def test_file_upload_download_flow(self, client, test_course, test_folder, temp_file):
    # 1. 上传文件
    upload_response = client.upload_file(
        file_path=temp_file,
        course_id=test_course["course"]["id"],
        folder_id=test_folder["folder"]["id"]
    )
    
    # 2. 下载文件
    file_id = upload_response["data"]["file"]["id"]
    download_response = client.download_file(file_id)
    
    # 3. 验证文件内容
    assert download_response.status_code == 200
    # 验证下载内容与原文件一致
```

## 🔧 API客户端使用

### 基本用法
```python
from tests.e2e.api_client import CampusLLMClient

# 创建客户端
client = CampusLLMClient(base_url="http://localhost:8001", debug=True)

# 用户操作
client.register(username="user", email="user@test.com", password="pass", invite_code="CODE")
client.login("user", "pass")
profile = client.get_me()

# 课程操作
semester = client.create_semester(name="2024春", code="2024S", start_date="2024-02-01", end_date="2024-06-30")
course = client.create_course(name="Python", code="CS101", semester_id=semester["data"]["semester"]["id"])

# 文件操作
folder = client.create_folder(course_id, name="课件", folder_type="lecture")
file_upload = client.upload_file(file_path="test.pdf", course_id=course_id, folder_id=folder_id)
```

### 管理员操作
```python
# 管理员客户端会自动处理权限
admin_client = CampusLLMClient()
admin_client.login("admin", "admin_password")

# 邀请码管理
invite_code = admin_client.create_invite_code(description="测试邀请码")
codes_list = admin_client.get_invite_codes()

# 系统配置
system_config = admin_client.get_system_config()
audit_logs = admin_client.get_audit_logs()
```

## 📊 测试数据管理

### 数据工厂
```python
from tests.e2e.factories import create_test_user, create_test_course

# 生成测试用户数据
user_data = create_test_user()
# {'username': 'testuser_abc123', 'email': 'abc123@test.com', 'password': 'TestPass123!', ...}

# 生成测试课程数据
course_data = create_test_course(semester_id=1)
# {'name': 'Python编程', 'code': 'CS101', 'semester_id': 1, ...}
```

### Fixtures使用
```python
def test_with_logged_in_user(self, client, logged_in_user):
    # logged_in_user fixture提供已登录的测试用户
    user_info = logged_in_user["user_data"]
    
    # 可以直接使用已登录的client进行操作
    profile = client.get_me()
    assert profile["data"]["username"] == user_info["username"]
```

## 🛡️ 权限测试

框架自动验证权限隔离：

```python
def test_access_other_user_data(self, client, another_user):
    # 尝试访问其他用户的数据应该失败
    with pytest.raises(APIException) as exc_info:
        client.get_course(other_user_course_id)
    
    # 验证返回403错误
    assert exc_info.value.status_code == 403
```

## 📈 测试报告

### HTML报告
```bash
python run_e2e_tests.py --html report.html
```
生成详细的HTML测试报告，包含：
- 测试用例执行状态
- 失败详情和堆栈跟踪
- 执行时间统计

### JUnit XML报告
```bash
python run_e2e_tests.py --junitxml results.xml
```
适用于CI/CD集成。

### 覆盖率报告
```bash
python run_e2e_tests.py --cov
```
生成代码覆盖率报告。

## 🔍 调试技巧

### 1. 启用调试模式
```bash
python run_e2e_tests.py --debug --verbose
```

### 2. 保留测试数据
```bash
python run_e2e_tests.py --no-cleanup
```

### 3. 运行单个测试
```bash
python -m pytest tests/e2e/test_user_workflows.py::TestUserRegistrationWorkflow::test_complete_user_registration_flow -v -s
```

### 4. 查看API请求详情
```python
# 在测试中启用调试
client = CampusLLMClient(debug=True)
# 会输出所有HTTP请求和响应
```

## 🚧 最佳实践

### 1. 测试隔离
- 每个测试使用独立的数据
- 测试间不相互依赖
- 自动清理测试数据

### 2. 断言策略
- 使用基类提供的断言方法
- 验证响应结构和业务逻辑
- 检查错误情况和边界条件

### 3. 数据生成
- 使用工厂类生成测试数据
- 避免硬编码测试值
- 支持数据变化和随机化

### 4. 错误处理
- 使用pytest.raises捕获预期异常
- 验证具体的错误码和消息
- 测试异常边界情况

## 🔄 CI/CD集成

### GitHub Actions示例
```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          cd backend_v2
          python -m venv v2env
          source v2env/bin/activate
          pip install -r requirements.txt
          pip install pytest requests faker pytest-html
      
      - name: Start API server
        run: |
          cd backend_v2
          source v2env/bin/activate
          uvicorn src.main:app --host 0.0.0.0 --port 8001 &
          sleep 10
      
      - name: Run E2E tests
        run: |
          cd backend_v2
          source v2env/bin/activate
          python run_e2e_tests.py --html e2e_report.html --junitxml e2e_results.xml
      
      - name: Upload test results
        uses: actions/upload-artifact@v2
        if: always()
        with:
          name: e2e-test-results
          path: |
            backend_v2/e2e_report.html
            backend_v2/e2e_results.xml
```

## 📞 获取帮助

如果遇到问题：

1. 查看测试日志和错误信息
2. 检查API服务器是否正常运行
3. 验证测试环境配置
4. 查看具体测试用例的实现

## 🎯 总结

这个E2E测试框架提供了：
- ✨ **完整的API封装** - 每个端点都有对应的Python方法
- 🔄 **业务流程测试** - 验证完整的用户操作路径
- 🛡️ **权限安全验证** - 确保数据隔离和访问控制  
- 📊 **丰富的测试报告** - 多格式报告支持
- 🚀 **易于扩展** - 模块化设计，容易添加新测试

通过这个框架，你可以：
- 快速验证系统核心功能
- 自动化复杂的业务流程测试
- 确保代码变更不会破坏现有功能
- 提供可靠的质量保证