# Campus LLM System v2 - End-to-End 测试开发指南

## 📖 概述

本指南专注于 Campus LLM System v2 的 End-to-End (E2E) 测试开发，基于 FastAPI 四层架构设计精确的 API 测试策略。通过完整的业务流程测试，确保系统功能稳定性和用户体验质量。

---

## 🎯 E2E 测试策略

### 为什么选择以 E2E 测试为主

#### 项目特点分析
- ✅ **FastAPI 四层架构完善** - 各层职责清晰，集成度高
- ✅ **业务逻辑相对简单** - 主要是 CRUD 操作和文件管理
- ✅ **API 是核心交互界面** - 前端完全通过 API 与后端交互
- ✅ **用户场景明确** - 注册、课程管理、文件存储等完整流程

#### E2E 测试优势
- 🎯 **验证真实用户场景** - 覆盖完整业务流程
- 🔄 **回归测试效果好** - 快速发现功能退化
- 🛡️ **权限控制验证全面** - 确保数据安全隔离
- ⚡ **维护成本相对较低** - 不需要复杂的 Mock 和层级隔离

### 测试分层设计

```
E2E 测试架构 (主要测试策略)
├── 🔥 冒烟测试 (Smoke Tests)
│   ├── 核心功能快速验证
│   ├── 系统可用性检查
│   └── 关键 API 端点测试
├── 🎯 功能测试 (Feature Tests)  
│   ├── 完整业务流程测试
│   ├── 用户操作路径验证
│   └── 数据流转完整性检查
├── 🛡️ 安全测试 (Security Tests)
│   ├── 权限控制验证
│   ├── 数据隔离检查
│   └── 认证授权测试
├── ⚠️ 边界测试 (Edge Case Tests)
│   ├── 异常情况处理
│   ├── 输入边界条件
│   └── 错误恢复能力
└── 🚀 性能测试 (Performance Tests)
    ├── 文件上传下载性能
    ├── 并发访问处理
    └── 系统响应时间
```

### 关键单元测试 (补充策略)
```
单元测试 (仅测试关键逻辑)
└── 🧮 复杂业务逻辑
    ├── 文件哈希计算
    ├── 权限验证算法
    ├── 数据验证复杂规则
    └── AI 向量化处理
```

---

## 🏗️ 测试架构实现

### 目录结构优化

```
tests/
├── conftest.py                 # pytest 全局配置
├── pytest.ini                 # pytest 配置文件
├── requirements-test.txt       # 测试依赖
│
├── e2e/                        # End-to-End 测试 (主要)
│   ├── __init__.py
│   ├── conftest.py            # E2E 专用配置
│   ├── base.py                # 增强的测试基类和断言
│   ├── api_client.py          # 完善的API客户端封装
│   ├── factories.py           # 智能测试数据工厂
│   ├── fixtures.py            # 测试夹具和数据准备
│   ├── config.py              # 测试环境配置
│   │
│   ├── smoke/                 # 冒烟测试
│   │   ├── test_health_check.py
│   │   ├── test_core_apis.py
│   │   └── test_system_ready.py
│   │
│   ├── workflows/             # 业务流程测试
│   │   ├── test_user_journey.py
│   │   ├── test_course_management.py
│   │   ├── test_file_operations.py
│   │   └── test_ai_integration.py
│   │
│   ├── security/              # 安全和权限测试
│   │   ├── test_authentication.py
│   │   ├── test_authorization.py
│   │   └── test_data_isolation.py
│   │
│   └── edge_cases/            # 边界条件测试
│       ├── test_error_handling.py
│       ├── test_input_validation.py
│       └── test_boundary_conditions.py
│
├── unit/                      # 单元测试 (补充)
│   ├── test_utils.py          # 工具函数测试
│   ├── test_validators.py     # 验证器测试
│   └── test_algorithms.py     # 算法逻辑测试
│
└── reports/                   # 测试报告输出
    ├── html/                  # HTML 报告
    ├── xml/                   # XML 报告
    └── coverage/              # 覆盖率报告
```

---

## 🎯 精确断言系统设计

### 基于四层架构的断言策略

#### 统一响应格式断言
```python
def assert_api_response_structure(response: Dict[str, Any]):
    """断言 API 响应符合统一格式"""
    assert isinstance(response, dict), f"响应应为字典类型，实际为: {type(response)}"
    assert "success" in response, "响应缺少 success 字段"
    assert isinstance(response["success"], bool), "success 字段应为布尔类型"
    
    if response["success"]:
        assert "data" in response, "成功响应应包含 data 字段"
        # message 字段是可选的
    else:
        assert "error" in response, "失败响应应包含 error 字段"
        error = response["error"]
        assert "code" in error, "错误信息应包含 code 字段"
        assert "message" in error, "错误信息应包含 message 字段"

def assert_success_response(response: Dict[str, Any], 
                          expected_data_keys: Optional[List[str]] = None,
                          expected_message: Optional[str] = None):
    """断言成功响应的完整结构"""
    assert_api_response_structure(response)
    assert response["success"] is True, f"应为成功响应，实际响应: {response}"
    
    data = response["data"]
    if expected_data_keys:
        for key in expected_data_keys:
            assert key in data, f"响应数据缺少必需字段 '{key}'，实际字段: {list(data.keys())}"
    
    if expected_message:
        message = response.get("message", "")
        assert expected_message in str(message), f"响应消息应包含 '{expected_message}'，实际消息: '{message}'"

def assert_error_response(response: Dict[str, Any],
                        expected_status: Optional[int] = None,
                        expected_error_code: Optional[str] = None,
                        expected_message: Optional[str] = None):
    """断言错误响应的完整结构"""
    assert_api_response_structure(response)
    assert response["success"] is False, f"应为失败响应，实际响应: {response}"
    
    error = response["error"]
    
    if expected_error_code:
        assert error["code"] == expected_error_code, \
            f"错误码应为 '{expected_error_code}'，实际为 '{error['code']}'"
    
    if expected_message:
        assert expected_message in error["message"], \
            f"错误消息应包含 '{expected_message}'，实际消息: '{error['message']}'"
```

#### 业务实体数据断言

```python
class BusinessEntityAssertions:
    """业务实体数据断言类"""
    
    @staticmethod
    def assert_user_data_structure(user_data: Dict[str, Any], 
                                 check_sensitive: bool = True):
        """断言用户数据结构完整性"""
        required_fields = ["id", "username", "email", "role", "created_at"]
        for field in required_fields:
            assert field in user_data, f"用户数据缺少必需字段 '{field}'"
        
        # 验证数据类型
        assert isinstance(user_data["id"], int), "用户ID应为整数"
        assert isinstance(user_data["username"], str), "用户名应为字符串"
        assert isinstance(user_data["role"], str), "角色应为字符串"
        assert user_data["role"] in ["admin", "user"], f"角色值无效: {user_data['role']}"
        
        # 验证邮箱格式
        email = user_data["email"]
        assert "@" in email and "." in email, f"邮箱格式无效: {email}"
        
        # 验证时间格式
        created_at = user_data["created_at"]
        assert isinstance(created_at, str), "创建时间应为字符串格式"
        
        # 敏感信息检查
        if check_sensitive:
            sensitive_fields = ["password", "password_hash"]
            for field in sensitive_fields:
                assert field not in user_data, f"响应不应包含敏感字段 '{field}'"
    
    @staticmethod
    def assert_user_permissions(user_data: Dict[str, Any], 
                              expected_role: str,
                              can_access_admin: bool = False):
        """断言用户权限正确性"""
        assert user_data["role"] == expected_role, \
            f"用户角色应为 '{expected_role}'，实际为 '{user_data['role']}'"
        
        # 根据角色验证权限
        if expected_role == "admin":
            # 管理员应该有管理权限
            pass  # 这里可以添加具体的管理员权限验证
        elif expected_role == "user":
            # 普通用户不应有管理权限
            assert not can_access_admin, "普通用户不应有管理员权限"
    
    @staticmethod
    def assert_course_data_structure(course_data: Dict[str, Any]):
        """断言课程数据结构完整性"""
        required_fields = ["id", "name", "code", "semester_id", "created_at"]
        for field in required_fields:
            assert field in course_data, f"课程数据缺少必需字段 '{field}'"
        
        # 验证数据类型
        assert isinstance(course_data["id"], int), "课程ID应为整数"
        assert isinstance(course_data["name"], str), "课程名称应为字符串"
        assert isinstance(course_data["code"], str), "课程代码应为字符串"
        assert isinstance(course_data["semester_id"], int), "学期ID应为整数"
        
        # 验证课程代码格式（根据业务规则）
        code = course_data["code"]
        assert len(code) >= 3, f"课程代码长度不应少于3位: {code}"
        assert code.replace("_", "").replace("-", "").isalnum(), f"课程代码格式无效: {code}"
    
    @staticmethod
    def assert_file_data_structure(file_data: Dict[str, Any]):
        """断言文件数据结构完整性"""
        required_fields = ["id", "filename", "file_size", "file_hash", "upload_time"]
        for field in required_fields:
            assert field in file_data, f"文件数据缺少必需字段 '{field}'"
        
        # 验证数据类型
        assert isinstance(file_data["id"], int), "文件ID应为整数"
        assert isinstance(file_data["filename"], str), "文件名应为字符串"
        assert isinstance(file_data["file_size"], int), "文件大小应为整数"
        assert isinstance(file_data["file_hash"], str), "文件哈希应为字符串"
        
        # 验证文件大小合理性
        file_size = file_data["file_size"]
        assert file_size > 0, f"文件大小应大于0: {file_size}"
        assert file_size <= 100 * 1024 * 1024, f"文件大小不应超过100MB: {file_size}"
        
        # 验证哈希格式（SHA256）
        file_hash = file_data["file_hash"]
        assert len(file_hash) == 64, f"SHA256哈希长度应为64位: {len(file_hash)}"
        assert all(c in '0123456789abcdef' for c in file_hash.lower()), f"哈希格式无效: {file_hash}"
```

#### 业务逻辑完整性断言

```python
class BusinessLogicAssertions:
    """业务逻辑完整性断言类"""
    
    @staticmethod
    def assert_user_registration_complete(registration_response: Dict[str, Any],
                                        registration_data: Dict[str, Any]):
        """断言用户注册流程完整性"""
        assert_success_response(registration_response, ["user"])
        
        user = registration_response["data"]["user"]
        BusinessEntityAssertions.assert_user_data_structure(user)
        
        # 验证注册数据一致性
        assert user["username"] == registration_data["username"], "用户名不匹配"
        assert user["email"] == registration_data["email"], "邮箱不匹配"
        assert user["role"] == "user", "新注册用户角色应为普通用户"
        
        # 验证安全性
        assert "password" not in user, "响应不应包含密码信息"
        assert "invite_code" not in user, "响应不应包含邀请码信息"
    
    @staticmethod
    def assert_login_response_complete(login_response: Dict[str, Any],
                                     username: str):
        """断言登录响应完整性"""
        assert_success_response(login_response, ["access_token", "token_type", "user"])
        
        data = login_response["data"]
        
        # 验证令牌
        assert isinstance(data["access_token"], str), "访问令牌应为字符串"
        assert len(data["access_token"]) > 10, "访问令牌长度应足够"
        assert data["token_type"].lower() == "bearer", f"令牌类型应为bearer: {data['token_type']}"
        
        # 验证用户信息
        user = data["user"]
        BusinessEntityAssertions.assert_user_data_structure(user)
        assert user["username"] == username, f"登录用户名不匹配: expected {username}, got {user['username']}"
    
    @staticmethod
    def assert_file_upload_complete(upload_response: Dict[str, Any],
                                  original_file_path: str,
                                  course_id: int,
                                  folder_id: Optional[int] = None):
        """断言文件上传流程完整性"""
        import os
        
        assert_success_response(upload_response, ["file"])
        
        file_data = upload_response["data"]["file"]
        BusinessEntityAssertions.assert_file_data_structure(file_data)
        
        # 验证文件信息
        original_filename = os.path.basename(original_file_path)
        assert file_data["filename"] == original_filename, \
            f"文件名不匹配: expected {original_filename}, got {file_data['filename']}"
        
        original_size = os.path.getsize(original_file_path)
        assert file_data["file_size"] == original_size, \
            f"文件大小不匹配: expected {original_size}, got {file_data['file_size']}"
        
        # 验证关联关系
        assert "course_id" in file_data, "文件数据应包含课程ID"
        assert file_data["course_id"] == course_id, \
            f"课程ID不匹配: expected {course_id}, got {file_data['course_id']}"
        
        if folder_id:
            assert "folder_id" in file_data, "文件数据应包含文件夹ID"
            assert file_data["folder_id"] == folder_id, \
                f"文件夹ID不匹配: expected {folder_id}, got {file_data['folder_id']}"
    
    @staticmethod
    def assert_data_isolation(user1_data: List[Dict], 
                            user2_data: List[Dict],
                            data_type: str = "resource"):
        """断言用户数据隔离正确性"""
        # 提取两个用户的资源ID
        user1_ids = {item["id"] for item in user1_data}
        user2_ids = {item["id"] for item in user2_data}
        
        # 验证没有数据交叉
        common_ids = user1_ids.intersection(user2_ids)
        assert len(common_ids) == 0, \
            f"用户{data_type}数据应该隔离，但发现共同的ID: {common_ids}"
        
        # 验证每个用户的资源归属
        for item in user1_data:
            if "user_id" in item:
                # 如果数据包含user_id，应该匹配用户1
                pass  # 这里需要根据具体业务逻辑实现
        
        for item in user2_data:
            if "user_id" in item:
                # 如果数据包含user_id，应该匹配用户2
                pass  # 这里需要根据具体业务逻辑实现
```

#### 权限控制断言

```python
class PermissionAssertions:
    """权限控制断言类"""
    
    @staticmethod
    def assert_unauthorized_access_blocked(api_client, endpoint: str, 
                                         method: str = "GET", **kwargs):
        """断言未授权访问被正确阻止"""
        from .api_client import APIException
        
        # 确保客户端处于未登录状态
        api_client.access_token = None
        api_client.session.headers.pop("Authorization", None)
        
        with pytest.raises(APIException) as exc_info:
            if method.upper() == "GET":
                api_client._get(endpoint, **kwargs)
            elif method.upper() == "POST":
                api_client._post(endpoint, **kwargs)
            elif method.upper() == "PUT":
                api_client._put(endpoint, **kwargs)
            elif method.upper() == "DELETE":
                api_client._delete(endpoint, **kwargs)
        
        assert exc_info.value.status_code == 401, \
            f"未授权访问应返回401，实际返回: {exc_info.value.status_code}"
    
    @staticmethod
    def assert_forbidden_access_blocked(api_client, endpoint: str,
                                      method: str = "GET", **kwargs):
        """断言权限不足访问被正确阻止"""
        from .api_client import APIException
        
        with pytest.raises(APIException) as exc_info:
            if method.upper() == "GET":
                api_client._get(endpoint, **kwargs)
            elif method.upper() == "POST":
                api_client._post(endpoint, **kwargs)
            elif method.upper() == "PUT":
                api_client._put(endpoint, **kwargs)
            elif method.upper() == "DELETE":
                api_client._delete(endpoint, **kwargs)
        
        assert exc_info.value.status_code == 403, \
            f"权限不足应返回403，实际返回: {exc_info.value.status_code}"
    
    @staticmethod
    def assert_admin_only_access(regular_client, admin_client, endpoint: str,
                                method: str = "GET", **kwargs):
        """断言管理员专用功能的访问控制"""
        # 普通用户应该被禁止访问
        PermissionAssertions.assert_forbidden_access_blocked(
            regular_client, endpoint, method, **kwargs
        )
        
        # 管理员应该可以正常访问
        if method.upper() == "GET":
            response = admin_client._get(endpoint, **kwargs)
        elif method.upper() == "POST":
            response = admin_client._post(endpoint, **kwargs)
        elif method.upper() == "PUT":
            response = admin_client._put(endpoint, **kwargs)
        elif method.upper() == "DELETE":
            response = admin_client._delete(endpoint, **kwargs)
        
        # 管理员访问应该成功
        assert_success_response(response)
        return response
```

---

## 🧪 智能测试数据管理

### 增强的数据工厂

```python
class SmartTestDataFactory:
    """智能测试数据工厂"""
    
    def __init__(self):
        self.faker = Faker('zh_CN')
        self.used_values = {
            'usernames': set(),
            'emails': set(),
            'course_codes': set(),
            'semester_codes': set()
        }
    
    def create_unique_user_data(self, role: str = "user", **overrides) -> Dict[str, Any]:
        """创建唯一的用户测试数据"""
        # 生成唯一用户名
        username = self._generate_unique_username()
        
        # 生成唯一邮箱
        email = self._generate_unique_email()
        
        user_data = {
            "username": username,
            "email": email,
            "password": "TestPass123!",
            "real_name": self.faker.name(),
            "phone": self._generate_phone(),
            "role": role
        }
        
        # 应用覆盖参数
        user_data.update(overrides)
        return user_data
    
    def create_test_scenario_data(self, scenario: str) -> Dict[str, Any]:
        """根据测试场景创建完整的数据集"""
        scenarios = {
            "user_registration_flow": self._create_registration_scenario,
            "course_management_flow": self._create_course_scenario,
            "file_upload_flow": self._create_file_scenario,
            "complete_user_journey": self._create_complete_journey_scenario
        }
        
        creator = scenarios.get(scenario)
        if not creator:
            raise ValueError(f"未知的测试场景: {scenario}")
        
        return creator()
    
    def _create_registration_scenario(self) -> Dict[str, Any]:
        """创建用户注册场景数据"""
        return {
            "admin_user": self.create_unique_user_data(role="admin"),
            "invite_code": {
                "description": f"测试邀请码 - {self.faker.sentence()}",
                "max_uses": 10,
                "expires_in_days": 30
            },
            "new_user": self.create_unique_user_data(),
            "verification_code": "123456"  # 测试环境固定验证码
        }
    
    def _create_course_scenario(self) -> Dict[str, Any]:
        """创建课程管理场景数据"""
        semester_code = self._generate_unique_semester_code()
        
        return {
            "admin_user": self.create_unique_user_data(role="admin"),
            "semester": {
                "name": f"{self.faker.year()}年{self.faker.random_element(['春', '夏', '秋', '冬'])}季学期",
                "code": semester_code,
                "start_date": self.faker.date_between(start_date='+1d', end_date='+30d').strftime('%Y-%m-%d'),
                "end_date": self.faker.date_between(start_date='+31d', end_date='+150d').strftime('%Y-%m-%d'),
                "description": f"测试学期 - {self.faker.text(max_nb_chars=100)}"
            },
            "courses": [
                {
                    "name": f"{subject} - {self.faker.catch_phrase()}",
                    "code": self._generate_unique_course_code(),
                    "description": self.faker.text(max_nb_chars=200)
                }
                for subject in ["Python编程", "数据结构", "算法分析", "机器学习"]
            ]
        }
    
    def _create_file_scenario(self) -> Dict[str, Any]:
        """创建文件操作场景数据"""
        course_scenario = self._create_course_scenario()
        
        return {
            **course_scenario,
            "folders": [
                {
                    "name": "课件资料",
                    "folder_type": "lecture",
                    "description": "课程讲义和演示文稿"
                },
                {
                    "name": "作业提交",
                    "folder_type": "assignment",
                    "description": "学生作业和项目文件"
                },
                {
                    "name": "参考资料", 
                    "folder_type": "reference",
                    "description": "课程相关的参考文档"
                }
            ],
            "test_files": [
                {
                    "content": f"这是测试文档内容 - {self.faker.text()}",
                    "filename": f"test_document_{self.faker.random_int(1000, 9999)}.txt",
                    "file_type": "text/plain"
                },
                {
                    "content": self.faker.json(),
                    "filename": f"test_data_{self.faker.random_int(1000, 9999)}.json",
                    "file_type": "application/json"
                }
            ]
        }
    
    def _generate_unique_username(self) -> str:
        """生成唯一用户名"""
        attempts = 0
        while attempts < 100:  # 防止无限循环
            username = f"testuser_{self.faker.random_int(1000, 9999)}_{self.faker.random_string(length=4).lower()}"
            if username not in self.used_values['usernames']:
                self.used_values['usernames'].add(username)
                return username
            attempts += 1
        
        # 如果重试100次仍然冲突，使用UUID
        import uuid
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        self.used_values['usernames'].add(username)
        return username
    
    def _generate_unique_email(self) -> str:
        """生成唯一邮箱"""
        username_part = self.faker.random_string(length=8).lower()
        domain = self.faker.random_element(["test.com", "example.org", "demo.net"])
        email = f"{username_part}@{domain}"
        
        if email not in self.used_values['emails']:
            self.used_values['emails'].add(email)
            return email
        
        # 如果冲突，添加时间戳
        import time
        timestamp = int(time.time())
        email = f"{username_part}_{timestamp}@{domain}"
        self.used_values['emails'].add(email)
        return email
```

### 测试数据生命周期管理

```python
class TestDataManager:
    """测试数据生命周期管理器"""
    
    def __init__(self, api_client):
        self.client = api_client
        self.created_entities = []
        self.cleanup_order = [
            'files', 'folders', 'courses', 'semesters', 
            'invite_codes', 'users'
        ]
    
    def register_created_entity(self, entity_type: str, entity_id: int, 
                              cleanup_method: Optional[str] = None):
        """注册已创建的实体，用于后续清理"""
        self.created_entities.append({
            'type': entity_type,
            'id': entity_id,
            'cleanup_method': cleanup_method or f"delete_{entity_type}"
        })
    
    def auto_register_from_response(self, response: Dict[str, Any], 
                                  entity_type: str):
        """从API响应自动注册实体"""
        if response.get("success") and "data" in response:
            data = response["data"]
            
            # 尝试多种可能的数据结构
            entity_data = None
            for key in [entity_type, entity_type.rstrip('s'), f"{entity_type}_data"]:
                if key in data:
                    entity_data = data[key]
                    break
            
            if entity_data and "id" in entity_data:
                self.register_created_entity(entity_type, entity_data["id"])
                return entity_data["id"]
        
        return None
    
    def cleanup_all(self):
        """按依赖关系顺序清理所有实体"""
        # 按cleanup_order的顺序清理
        for entity_type in self.cleanup_order:
            entities_to_clean = [
                e for e in self.created_entities 
                if e['type'] == entity_type
            ]
            
            for entity in entities_to_clean:
                try:
                    self._cleanup_entity(entity)
                except Exception as e:
                    # 记录清理失败，但继续清理其他实体
                    print(f"清理实体失败 {entity}: {e}")
        
        self.created_entities.clear()
    
    def _cleanup_entity(self, entity: Dict[str, Any]):
        """清理单个实体"""
        method_name = entity['cleanup_method']
        
        if hasattr(self.client, method_name):
            cleanup_method = getattr(self.client, method_name)
            cleanup_method(entity['id'])
        else:
            # 尝试通用的删除方法
            generic_method = f"delete_{entity['type'].rstrip('s')}"
            if hasattr(self.client, generic_method):
                method = getattr(self.client, generic_method)
                method(entity['id'])

# 在测试中使用数据管理器
@pytest.fixture
def data_manager(client):
    """测试数据管理器夹具"""
    manager = TestDataManager(client)
    yield manager
    # 测试结束时自动清理
    manager.cleanup_all()
```

---

## 🔧 测试用例编写模板

### 冒烟测试模板

```python
@pytest.mark.smoke
class TestSystemSmokeTests:
    """系统冒烟测试 - 验证核心功能可用性"""
    
    def test_api_server_health(self, client):
        """测试API服务器健康状态"""
        # 这里假设有健康检查端点
        try:
            response = client._get("/health")
            assert response.get("status") == "healthy"
        except Exception:
            # 如果没有专门的健康检查端点，测试基本端点
            response = client._get("/api/v1/")  # 或其他基本端点
            assert response is not None
    
    def test_database_connectivity(self, admin_client):
        """测试数据库连接"""
        # 通过简单的查询操作验证数据库可用性
        response = admin_client.get_users()
        assert_success_response(response, ["users"])
    
    def test_authentication_flow(self, client, data_manager):
        """测试基本认证流程"""
        factory = SmartTestDataFactory()
        scenario_data = factory.create_test_scenario_data("user_registration_flow")
        
        # 管理员登录
        admin_data = scenario_data["admin_user"]
        admin_login = client.login(admin_data["username"], admin_data["password"])
        assert_success_response(admin_login, ["access_token"])
        
        # 创建邀请码
        invite_data = scenario_data["invite_code"]
        invite_response = client.create_invite_code(**invite_data)
        assert_success_response(invite_response, ["invite_code"])
        data_manager.auto_register_from_response(invite_response, "invite_codes")
        
        # 用户注册
        user_data = scenario_data["new_user"]
        user_data["invite_code"] = invite_response["data"]["invite_code"]["code"]
        
        register_response = client.register(**user_data)
        assert_success_response(register_response, ["user"])
        data_manager.auto_register_from_response(register_response, "users")
        
        # 用户登录
        login_response = client.login(user_data["username"], user_data["password"])
        BusinessLogicAssertions.assert_login_response_complete(
            login_response, user_data["username"]
        )
```

### 完整业务流程测试模板

```python
@pytest.mark.workflows
class TestCompleteUserJourney:
    """完整用户旅程测试"""
    
    def test_new_user_complete_course_interaction_flow(self, client, data_manager):
        """新用户完整的课程交互流程测试"""
        factory = SmartTestDataFactory()
        scenario_data = factory.create_test_scenario_data("complete_user_journey")
        
        # === 第一阶段：环境准备 ===
        self._setup_admin_and_system_data(client, data_manager, scenario_data)
        
        # === 第二阶段：用户注册和认证 ===
        user_data = self._complete_user_registration(client, data_manager, scenario_data)
        
        # === 第三阶段：课程和学习资源访问 ===
        course_data = self._access_and_interact_with_courses(client, data_manager, scenario_data)
        
        # === 第四阶段：文件操作和内容管理 ===
        self._perform_file_operations(client, data_manager, course_data)
        
        # === 第五阶段：AI功能使用 ===
        self._test_ai_integration(client, course_data)
        
        # === 第六阶段：权限和安全验证 ===
        self._verify_security_and_permissions(client, user_data)
    
    def _setup_admin_and_system_data(self, client, data_manager, scenario_data):
        """设置管理员和系统基础数据"""
        # 管理员登录
        admin_data = scenario_data["admin_user"]
        admin_login = client.login(admin_data["username"], admin_data["password"])
        BusinessLogicAssertions.assert_login_response_complete(
            admin_login, admin_data["username"]
        )
        
        # 创建学期
        semester_data = scenario_data["semester"]
        semester_response = client.create_semester(**semester_data)
        assert_success_response(semester_response, ["semester"])
        semester_id = data_manager.auto_register_from_response(semester_response, "semesters")
        
        # 创建课程
        courses_created = []
        for course_data in scenario_data["courses"]:
            course_data["semester_id"] = semester_id
            course_response = client.create_course(**course_data)
            assert_success_response(course_response, ["course"])
            BusinessEntityAssertions.assert_course_data_structure(
                course_response["data"]["course"]
            )
            course_id = data_manager.auto_register_from_response(course_response, "courses")
            courses_created.append(course_id)
        
        scenario_data["created_course_ids"] = courses_created
        return scenario_data
    
    def _complete_user_registration(self, client, data_manager, scenario_data):
        """完成用户注册流程"""
        # 创建邀请码（管理员已登录）
        invite_data = scenario_data["invite_code"]
        invite_response = client.create_invite_code(**invite_data)
        assert_success_response(invite_response, ["invite_code"])
        data_manager.auto_register_from_response(invite_response, "invite_codes")
        
        # 用户注册
        user_data = scenario_data["new_user"]
        user_data["invite_code"] = invite_response["data"]["invite_code"]["code"]
        
        register_response = client.register(**user_data)
        BusinessLogicAssertions.assert_user_registration_complete(
            register_response, user_data
        )
        data_manager.auto_register_from_response(register_response, "users")
        
        # 邮箱验证（如果启用）
        try:
            verify_response = client.verify_email(
                user_data["email"], 
                scenario_data["verification_code"]
            )
            assert_success_response(verify_response)
        except APIException as e:
            if e.status_code != 404:  # 404表示邮箱验证功能未启用
                raise
        
        # 用户登录
        login_response = client.login(user_data["username"], user_data["password"])
        BusinessLogicAssertions.assert_login_response_complete(
            login_response, user_data["username"]
        )
        
        return user_data
    
    def _access_and_interact_with_courses(self, client, data_manager, scenario_data):
        """访问和交互课程"""
        # 获取课程列表
        courses_response = client.get_courses()
        assert_success_response(courses_response, ["courses"])
        
        courses = courses_response["data"]["courses"]
        assert len(courses) >= len(scenario_data["created_course_ids"]), \
            "应该能看到所有已创建的课程"
        
        # 验证每个课程的数据结构
        for course in courses:
            BusinessEntityAssertions.assert_course_data_structure(course)
        
        # 选择第一个课程进行详细测试
        test_course = courses[0]
        course_id = test_course["id"]
        
        # 获取课程详情
        course_detail_response = client.get_course(course_id)
        assert_success_response(course_detail_response, ["course"])
        
        course_detail = course_detail_response["data"]["course"]
        BusinessEntityAssertions.assert_course_data_structure(course_detail)
        
        return test_course
    
    def _perform_file_operations(self, client, data_manager, course_data):
        """执行文件操作"""
        course_id = course_data["id"]
        
        # 创建文件夹
        folder_data = {
            "name": "测试文件夹",
            "folder_type": "lecture",
            "description": "用于测试的文件夹",
            "course_id": course_id
        }
        
        folder_response = client.create_folder(**folder_data)
        assert_success_response(folder_response, ["folder"])
        folder_id = data_manager.auto_register_from_response(folder_response, "folders")
        
        # 创建测试文件并上传
        test_content = "这是一个测试文件的内容\n包含多行文本\n用于验证文件上传功能"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
        
        try:
            # 上传文件
            upload_response = client.upload_file(
                file_path=temp_file_path,
                course_id=course_id,
                folder_id=folder_id
            )
            
            BusinessLogicAssertions.assert_file_upload_complete(
                upload_response, temp_file_path, course_id, folder_id
            )
            
            file_id = data_manager.auto_register_from_response(upload_response, "files")
            
            # 下载文件验证
            download_response = client.download_file(file_id)
            assert download_response.status_code == 200
            
            downloaded_content = download_response.content.decode('utf-8')
            assert downloaded_content == test_content, "下载的文件内容应与原文件一致"
            
        finally:
            # 清理临时文件
            os.unlink(temp_file_path)
    
    def _test_ai_integration(self, client, course_data):
        """测试AI集成功能"""
        course_id = course_data["id"]
        
        # 测试AI对话功能（如果实现）
        try:
            chat_response = client.create_chat_session(course_id=course_id)
            if chat_response.get("success"):
                # AI功能已实现，进行详细测试
                assert_success_response(chat_response, ["session"])
                
                # 发送测试消息
                message_response = client.send_chat_message(
                    session_id=chat_response["data"]["session"]["id"],
                    message="这是一个测试消息"
                )
                assert_success_response(message_response, ["message", "response"])
                
        except APIException as e:
            if e.status_code == 404:
                # AI功能尚未实现，跳过测试
                pytest.skip("AI功能尚未实现")
            else:
                raise
    
    def _verify_security_and_permissions(self, client, user_data):
        """验证安全性和权限控制"""
        # 用户登出
        logout_response = client.logout()
        assert_success_response(logout_response)
        
        # 验证登出后无法访问保护资源
        PermissionAssertions.assert_unauthorized_access_blocked(
            client, "/api/v1/courses"
        )
        
        # 重新登录
        login_response = client.login(user_data["username"], user_data["password"])
        BusinessLogicAssertions.assert_login_response_complete(
            login_response, user_data["username"]
        )
        
        # 验证普通用户无法访问管理功能
        PermissionAssertions.assert_forbidden_access_blocked(
            client, "/api/v1/admin/invite-codes", "POST", 
            json={"description": "测试邀请码"}
        )
```

### 安全测试模板

```python
@pytest.mark.security
class TestSecurityAndPermissions:
    """安全性和权限控制测试"""
    
    def test_data_isolation_between_users(self, client, data_manager):
        """测试用户间数据隔离"""
        factory = SmartTestDataFactory()
        
        # 创建两个不同的用户
        user1_data = factory.create_unique_user_data()
        user2_data = factory.create_unique_user_data()
        
        # 注册两个用户（这里假设有管理员帮助创建邀请码）
        # ... 注册逻辑 ...
        
        # 用户1登录并创建数据
        client.login(user1_data["username"], user1_data["password"])
        user1_courses = self._create_user_test_data(client, data_manager)
        client.logout()
        
        # 用户2登录并创建数据
        client.login(user2_data["username"], user2_data["password"])
        user2_courses = self._create_user_test_data(client, data_manager)
        
        # 验证用户2无法访问用户1的数据
        for course_id in user1_courses:
            PermissionAssertions.assert_forbidden_access_blocked(
                client, f"/api/v1/courses/{course_id}"
            )
        
        # 验证数据隔离
        user2_course_list = client.get_courses()
        user2_course_ids = [c["id"] for c in user2_course_list["data"]["courses"]]
        
        BusinessLogicAssertions.assert_data_isolation(
            [{"id": cid} for cid in user1_courses],
            [{"id": cid} for cid in user2_course_ids],
            "courses"
        )
    
    def test_admin_privilege_escalation_protection(self, client, admin_client):
        """测试防止权限提升攻击"""
        factory = SmartTestDataFactory()
        user_data = factory.create_unique_user_data()
        
        # 普通用户注册和登录
        # ... 注册逻辑 ...
        client.login(user_data["username"], user_data["password"])
        
        # 尝试访问管理员功能应该被阻止
        admin_endpoints = [
            ("/api/v1/admin/invite-codes", "GET"),
            ("/api/v1/admin/invite-codes", "POST"),
            ("/api/v1/admin/users", "GET"),
            ("/api/v1/admin/system-config", "GET"),
        ]
        
        for endpoint, method in admin_endpoints:
            PermissionAssertions.assert_forbidden_access_blocked(
                client, endpoint, method
            )
        
        # 验证管理员可以正常访问这些功能
        for endpoint, method in admin_endpoints:
            if method == "POST" and "invite-codes" in endpoint:
                # 特殊处理需要请求体的POST请求
                response = admin_client._post(endpoint, json={"description": "测试"})
            else:
                response = getattr(admin_client, f"_{method.lower()}")(endpoint)
            
            assert_success_response(response)
```

这个E2E测试开发指南专注于实用性和可操作性，提供了：

1. **精确的断言系统** - 基于业务逻辑的深度验证
2. **智能数据管理** - 自动化的测试数据生成和清理
3. **完整的测试模板** - 涵盖冒烟、功能、安全等各种场景
4. **实用的测试策略** - 以E2E为主，补充关键单元测试

接下来我们可以开始实施这个指南，从更新pytest配置开始。

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "testing_guide_doc", "content": "\u521b\u5efaE2E\u6d4b\u8bd5\u5f00\u53d1\u6307\u5357\u6587\u6863 (docs/e2e_testing_guide.md)", "status": "completed", "priority": "high"}, {"id": "pytest_config_update", "content": "\u66f4\u65b0pytest.ini\u914d\u7f6e\uff0c\u589e\u52a0\u6d4b\u8bd5\u6807\u8bb0\u548c\u8986\u76d6\u7387\u8981\u6c42", "status": "in_progress", "priority": "high"}, {"id": "enhance_base_assertions", "content": "\u589e\u5f3abase.py\u65ad\u8a00\u7cfb\u7edf\uff0c\u57fa\u4e8e\u56db\u5c42\u67b6\u6784\u8bbe\u8ba1\u7cbe\u786e\u65ad\u8a00", "status": "pending", "priority": "high"}, {"id": "optimize_factories", "content": "\u4f18\u5316factories.py\u6570\u636e\u7ba1\u7406\uff0c\u652f\u6301\u590d\u6742\u5173\u8054\u6570\u636e\u548c\u6e05\u7406\u673a\u5236", "status": "pending", "priority": "medium"}, {"id": "enhance_api_client", "content": "\u5b8c\u5584api_client.py\u9519\u8bef\u5904\u7406\u548cAPI\u8986\u76d6", "status": "pending", "priority": "medium"}, {"id": "create_unit_tests", "content": "\u521b\u5efa\u5355\u5143\u6d4b\u8bd5\u5c42 (tests/unit/)", "status": "pending", "priority": "low"}, {"id": "create_integration_tests", "content": "\u521b\u5efa\u96c6\u6210\u6d4b\u8bd5\u5c42 (tests/integration/)", "status": "pending", "priority": "low"}, {"id": "rewrite_e2e_tests", "content": "\u91cd\u5199E2E\u6d4b\u8bd5\u7528\u4f8b\uff0c\u4f7f\u7528\u65b0\u65ad\u8a00\u7cfb\u7edf", "status": "pending", "priority": "medium"}]