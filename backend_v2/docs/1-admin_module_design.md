# Admin 模块技术设计文档

## 概述

Admin 模块是 Campus LLM System v2 的管理功能模块，负责系统管理员的核心管理功能。基于 Auth 模块建立的 FastAPI 2024 最佳实践模式，提供邀请码管理、系统配置、审计日志和全局文件管理等功能。

## 架构设计

### 模块结构
```
src/admin/
├── __init__.py
├── models.py          # SQLAlchemy 数据模型
├── schemas.py         # Pydantic 请求/响应模型
├── service.py         # 业务逻辑层
├── router.py          # FastAPI 路由定义
├── dependencies.py    # 依赖注入（管理员权限）
└── exceptions.py      # 模块特定异常
```

### 依赖关系
```
Admin Module Dependencies:
├── src/shared/ (基础设施)
│   ├── database.py
│   ├── config.py
│   ├── exceptions.py
│   ├── schemas.py (BaseResponse)
│   ├── dependencies.py (DbDep, UserDep)
│   └── api_decorator.py (Service API 装饰器)
└── src/auth/ (用户认证)
    ├── models.py (User, InviteCode)
    └── dependencies.py (get_current_user)
```

## 数据模型设计

### 核心模型

#### 1. InviteCode (使用 Auth 模块模型)
Admin模块通过导入使用Auth模块中的InviteCode模型：
```python
# Admin模块导入InviteCode
from src.auth.models import InviteCode

# InviteCode模型定义在src/auth/models.py中：
class InviteCode(Base):
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
```

#### 2. AuditLog 
```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    # 兼容v1版本字段名
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(Integer, nullable=True, index=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    # 兼容v1版本字段名
    created_at = Column(DateTime, server_default=func.now(), index=True)
```

### 数据库索引策略
```sql
-- 邀请码查询优化
CREATE INDEX idx_invite_codes_status ON invite_codes(is_used, is_active);
CREATE INDEX idx_invite_codes_creator ON invite_codes(created_by, created_at);

-- 审计日志查询优化
CREATE INDEX idx_audit_logs_user_time ON audit_logs(user_id, created_at);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_action_time ON audit_logs(action, created_at);
```

## API 接口设计

### 路由前缀和标签
- **前缀**: `/admin`
- **标签**: `["管理"]` (在 main.py 中设置)
- **权限**: 所有端点都需要管理员权限

### API 端点规范

#### 1. 邀请码管理
```python
# 创建邀请码
POST /api/v1/admin/invite-codes
Request: CreateInviteCodeRequest
Response: CreateInviteCodeResponse

# 获取邀请码列表
GET /api/v1/admin/invite-codes?skip=0&limit=100
Response: InviteCodeListResponse

# 更新邀请码
PUT /api/v1/admin/invite-codes/{invite_code_id}
Request: UpdateInviteCodeRequest
Response: UpdateInviteCodeResponse

# 删除邀请码
DELETE /api/v1/admin/invite-codes/{invite_code_id}
Response: MessageResponse
```

#### 2. 系统配置
```python
# 获取系统配置
GET /api/v1/admin/system/config
Response: SystemConfigResponse
```

#### 3. 审计日志
```python
# 获取审计日志
GET /api/v1/admin/audit-logs?user_id=1&start_date=2025-01-01&end_date=2025-01-31&skip=0&limit=100
Response: AuditLogsResponse
```

#### 4. 全局文件管理
```python
# 上传全局文件
POST /api/v1/admin/global-files/upload
Request: FormData (file, description, tags, visibility)
Response: GlobalFileUploadResponse
```

## 请求/响应模型设计

### 基于 BaseResponse 的统一响应格式

#### 邀请码相关
```python
# 请求模型
class CreateInviteCodeRequest(BaseModel):
    description: Optional[str] = Field(None, max_length=200, description="邀请码描述")
    expires_at: Optional[datetime] = Field(None, description="过期时间，不设置则永不过期")

class UpdateInviteCodeRequest(BaseModel):
    description: Optional[str] = Field(None, max_length=200, description="邀请码描述")
    expires_at: Optional[datetime] = Field(None, description="过期时间")

# 数据载荷模型
class InviteCodeData(BaseModel):
    id: int
    code: str
    description: Optional[str]
    is_used: bool
    used_by: Optional[int]
    used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_by: int
    created_at: datetime

class CreateInviteCodeData(BaseModel):
    invite_code: InviteCodeData

class InviteCodeListData(BaseModel):
    invite_codes: List[InviteCodeData]
    total: int
    pagination: PaginationInfo

# 响应模型
class CreateInviteCodeResponse(BaseResponse[CreateInviteCodeData]):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "success": True,
                "data": {
                    "invite_code": {
                        "id": 1,
                        "code": "ABC12345",
                        "description": "测试邀请码",
                        "is_used": False,
                        "used_by": None,
                        "used_at": None,
                        "expires_at": "2025-12-31T23:59:59Z",
                        "created_by": 1,
                        "created_at": "2025-01-27T10:00:00Z"
                    }
                },
                "message": "邀请码创建成功"
            }]
        }
    )

class InviteCodeListResponse(BaseResponse[InviteCodeListData]):
    # 类似的示例配置...
```

#### 系统配置响应
```python
class SystemConfigData(BaseModel):
    # 应用信息
    app_name: str
    app_version: str
    environment: str
    
    # 功能开关
    registration_enabled: bool
    email_verification_enabled: bool
    
    # 系统统计
    total_users: int
    total_files: int
    storage_used_mb: float
    
    # 限制配置
    max_file_size_mb: int
    max_upload_files_per_user: int

class SystemConfigResponse(BaseResponse[SystemConfigData]):
    # OpenAPI 示例...
```

#### 审计日志响应
```python
class AuditLogData(BaseModel):
    id: int
    user_id: Optional[int]
    username: Optional[str]  # 关联查询用户名
    action: str
    entity_type: str  # 兼容v1版本字段名
    entity_id: Optional[int]  # 兼容v1版本字段名
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime  # 兼容v1版本字段名

class AuditLogsData(BaseModel):
    logs: List[AuditLogData]
    total: int
    pagination: PaginationInfo

class AuditLogsResponse(BaseResponse[AuditLogsData]):
    # OpenAPI 示例...
```

## 业务逻辑设计

### AdminService 类设计

#### 异常声明 (METHOD_EXCEPTIONS)
```python
class AdminService:
    METHOD_EXCEPTIONS = {
        # 邀请码管理
        'create_invite_code': {BadRequestError, ConflictError},
        'get_invite_codes': set(),  # 无特定异常
        'update_invite_code': {NotFoundError, BadRequestError},
        'delete_invite_code': {NotFoundError, ConflictError},  # 已使用的不能删除
        
        # 系统配置
        'get_system_config': set(),  # 只读，无异常
        
        # 审计日志
        'get_audit_logs': {BadRequestError},  # 日期格式错误等
        
        # 全局文件管理
        'upload_global_file': {BadRequestError, ForbiddenError},
    }
```

#### 核心业务方法

##### 邀请码管理
```python
# AdminService中需要导入InviteCode
from src.auth.models import InviteCode, User

def create_invite_code(self, request: CreateInviteCodeRequest, created_by: int) -> Dict[str, Any]:
    """创建邀请码"""
    # 1. 生成唯一邀请码
    code = self._generate_unique_invite_code()
    
    # 2. 验证过期时间
    if request.expires_at and request.expires_at <= datetime.utcnow():
        raise BadRequestError("过期时间不能早于当前时间", error_code="INVALID_EXPIRE_TIME")
    
    # 3. 创建邀请码
    invite_code = InviteCode(
        code=code,
        description=request.description,
        expires_at=request.expires_at,
        created_by=created_by
    )
    
    self.db.add(invite_code)
    self.db.commit()
    self.db.refresh(invite_code)
    
    return {
        "invite_code": invite_code,
        "message": "邀请码创建成功"
    }

def get_invite_codes(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    """获取邀请码列表"""
    # 查询总数
    total = self.db.query(InviteCode).count()
    
    # 分页查询
    invite_codes = (
        self.db.query(InviteCode)
        .order_by(InviteCode.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return {
        "invite_codes": invite_codes,
        "total": total,
        "pagination": {
            "skip": skip,
            "limit": limit,
            "has_more": skip + limit < total
        }
    }
```

##### 系统配置
```python
def get_system_config(self) -> Dict[str, Any]:
    """获取系统配置 - 过滤敏感信息"""
    # 获取系统统计
    total_users = self.db.query(User).count()
    # total_files = self.db.query(File).count()  # 需要 Storage 模块
    
    config_data = {
        # 应用信息
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "environment": settings.environment,
        
        # 功能开关
        "registration_enabled": settings.enable_registration,
        "email_verification_enabled": settings.enable_email_verification,
        
        # 系统统计
        "total_users": total_users,
        "total_files": 0,  # 暂时硬编码，等 Storage 模块
        "storage_used_mb": 0.0,
        
        # 限制配置
        "max_file_size_mb": 100,  # 从配置获取
        "max_upload_files_per_user": 1000,
    }
    
    return {
        "config": config_data,
        "message": None
    }
```

##### 审计日志
```python
# AdminService中需要导入AuditLog
from src.admin.models import AuditLog

def get_audit_logs(
    self, 
    user_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0, 
    limit: int = 100
) -> Dict[str, Any]:
    """获取审计日志"""
    # 构建查询
    query = self.db.query(AuditLog).join(User, AuditLog.user_id == User.id, isouter=True)
    
    # 应用过滤条件
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)  # 使用v1兼容字段名
    
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)  # 使用v1兼容字段名
    
    # 获取总数和分页数据
    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()  # 使用v1兼容字段名
    
    # 格式化返回数据
    formatted_logs = [
        {
            **log.__dict__,
            "username": log.user.username if log.user else None
        }
        for log in logs
    ]
    
    return {
        "logs": formatted_logs,
        "total": total,
        "pagination": {
            "skip": skip,
            "limit": limit,
            "has_more": skip + limit < total
        }
    }
```

## 权限控制设计

### 管理员依赖注入
```python
# src/admin/dependencies.py
from typing import Annotated
from fastapi import Depends
from src.shared.dependencies import get_current_user
from src.shared.exceptions import ForbiddenError
from src.auth.models import User

def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """获取管理员用户，验证管理员权限"""
    if current_user.role != "admin":
        raise ForbiddenError("需要管理员权限", error_code="ADMIN_REQUIRED")
    return current_user

# 类型别名
AdminDep = Annotated[User, Depends(get_admin_user)]
```

### Router 层权限控制
```python
# src/admin/router.py
from .dependencies import AdminDep

@router.post("/invite-codes", **create_service_route_config(
    AdminService, 'create_invite_code', CreateInviteCodeResponse,
    success_status=201,
    summary="创建邀请码",
    description="管理员创建新的邀请码，可设置描述和过期时间",
    operation_id="create_invite_code"
))
@service_api_handler(AdminService, 'create_invite_code')
async def create_invite_code(
    request: CreateInviteCodeRequest,
    admin_user: AdminDep,  # 自动验证管理员权限
    db: DbDep
):
    """创建邀请码 (管理员专用)"""
    service = AdminService(db)
    result = service.create_invite_code(request, admin_user.id)
    
    return CreateInviteCodeResponse(
        success=True,
        data=CreateInviteCodeData(invite_code=result["invite_code"]),
        message=result["message"]
    )
```

## 测试策略

### 单元测试设计 (test_admin_unit.py)
基于 Auth 模块的测试模式：

```python
class TestAdminServiceInviteCodes:
    """邀请码管理业务逻辑测试"""
    
    def test_create_invite_code_success(self, admin_service: AdminService, admin_user: User):
        """测试创建邀请码成功"""
        
    def test_create_invite_code_invalid_expire_time(self, admin_service: AdminService, admin_user: User):
        """测试无效过期时间"""
        
    def test_get_invite_codes_pagination(self, admin_service: AdminService):
        """测试邀请码分页查询"""

class TestAdminServiceSystemConfig:
    """系统配置业务逻辑测试"""
    
    def test_get_system_config_no_sensitive_data(self, admin_service: AdminService):
        """测试系统配置不包含敏感信息"""

class TestAdminServiceAuditLogs:
    """审计日志业务逻辑测试"""
    
    def test_get_audit_logs_with_filters(self, admin_service: AdminService, sample_audit_logs: List[AuditLog]):
        """测试审计日志过滤查询"""
```

### API 集成测试设计 (test_admin_api.py)
```python
class TestAdminInviteCodesAPI:
    """邀请码管理API测试"""
    
    def test_create_invite_code_success(self, client: TestClient, admin_headers: dict):
        """测试创建邀请码成功"""
        
    def test_create_invite_code_forbidden(self, client: TestClient, user_headers: dict):
        """测试非管理员无法创建邀请码"""

class TestAdminPermissions:
    """管理员权限测试"""
    
    def test_all_admin_endpoints_require_admin_role(self, client: TestClient, user_headers: dict):
        """测试所有管理员端点都需要管理员角色"""
```

## 安全考虑

### 1. 权限控制
- 所有 Admin API 端点都需要管理员权限验证
- 使用 `AdminDep` 依赖注入确保权限检查一致性
- 非管理员访问返回 `403 Forbidden`

### 2. 敏感信息过滤
- 系统配置接口不返回敏感信息（数据库连接、密钥等）
- 审计日志中的敏感字段进行脱敏处理
- 邀请码生成使用加密安全的随机生成器

### 3. 操作审计
- 所有管理员操作都记录到审计日志
- 记录操作者、操作类型、资源信息、时间戳
- 包含 IP 地址和 User Agent 信息

### 4. 输入验证
- 所有请求参数都有完整的 Pydantic 验证
- 日期范围查询防止过大的时间范围
- 分页参数限制防止大量数据查询

## 性能优化

### 1. 数据库查询优化
- 邀请码列表查询使用分页和索引
- 审计日志查询使用时间范围索引
- 关联查询优化，避免 N+1 问题

### 2. 缓存策略
- 系统配置可以缓存一定时间
- 用户统计信息可以使用缓存
- 邀请码验证可以使用短期缓存

### 3. 资源限制
- 分页查询限制最大页面大小
- 审计日志查询限制时间范围
- 文件上传大小限制

## 错误处理

### 异常类型定义
```python
# src/admin/exceptions.py
from src.shared.exceptions import BaseAPIException

class InviteCodeNotFoundError(BaseAPIException):
    def __init__(self, invite_code_id: int):
        super().__init__(
            message=f"邀请码 {invite_code_id} 不存在",
            error_code="INVITE_CODE_NOT_FOUND",
            status_code=404
        )

class InviteCodeAlreadyUsedError(BaseAPIException):
    def __init__(self, code: str):
        super().__init__(
            message=f"邀请码 {code} 已被使用，无法删除",
            error_code="INVITE_CODE_ALREADY_USED",
            status_code=409
        )
```

## 部署考虑

### 1. 环境配置
- 管理员功能在生产环境需要特殊配置
- 系统配置接口的信息范围可配置
- 审计日志保留期限可配置

### 2. 监控和告警
- 管理员操作的监控和告警
- 异常操作的实时通知
- 系统资源使用情况监控

### 3. 备份和恢复
- 邀请码数据的定期备份
- 审计日志的归档策略
- 系统配置的版本管理

## 总结

Admin 模块严格遵循 Auth 模块建立的 FastAPI 2024 最佳实践模式：

- ✅ **Service API 装饰器**：自动生成 OpenAPI 文档
- ✅ **统一响应格式**：BaseResponse[T] 泛型设计
- ✅ **现代依赖注入**：AdminDep 类型安全的权限控制
- ✅ **异常处理自动化**：METHOD_EXCEPTIONS 声明
- ✅ **完整测试覆盖**：单元测试 + API 集成测试
- ✅ **安全性考虑**：权限控制、敏感信息过滤、操作审计

这个设计确保了 Admin 模块与整个系统架构的一致性，同时提供了强大的管理功能和优秀的开发体验。