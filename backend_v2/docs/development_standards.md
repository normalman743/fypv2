# Campus LLM System v2 开发规范

## 📖 概述

本文档基于 FastAPI 架构审核报告，为 Campus LLM System v2 项目制定了详细的开发规范和最佳实践指南。

---

## 🏗️ 四层架构开发指南

### Model 层开发规范

**核心职责**: 定义数据库表结构、关系映射和数据约束

#### 基本结构模板
```python
"""模块名称的数据库模型定义"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.shared.database import Base

class YourModel(Base):
    """模型说明"""
    __tablename__ = "your_table"
    
    # 主键 (必需)
    id = Column(Integer, primary_key=True, index=True)
    
    # 业务字段
    name = Column(String(100), nullable=False, index=True, comment="名称")
    description = Column(Text, comment="描述")
    status = Column(String(20), default="active", comment="状态")
    
    # 外键关系 (如需要)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 时间戳 (推荐)
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系映射
    user = relationship("User", back_populates="your_models")

    def __repr__(self):
        return f"<YourModel(id={self.id}, name='{self.name}')>"
```

#### 开发规范要点

1. **命名规范**
   - 类名使用 PascalCase: `UserProfile`, `CourseFile`
   - 表名使用 snake_case: `user_profiles`, `course_files`
   - 字段名使用 snake_case: `created_at`, `user_id`

2. **字段定义**
   - 必须指定字段类型和长度限制
   - 添加适当的约束 (`nullable`, `unique`, `default`)
   - 为重要字段添加索引 (`index=True`)
   - 为字段添加注释 (`comment="说明"`)

3. **关系映射**
   - 使用 `ForeignKey` 定义外键约束
   - 使用 `relationship()` 建立双向关联
   - 正确设置 `back_populates` 参数

4. **时间戳字段**
   - 统一使用 `created_at` 和 `updated_at`
   - 使用 `server_default=func.now()` 设置默认值
   - 使用 `onupdate=func.now()` 自动更新时间

### Schema 层开发规范

**核心职责**: API 数据验证、序列化和文档生成

#### 基本结构模板
```python
"""模块名称的数据验证模式"""
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List
from datetime import datetime

# 基础Schema
class YourModelBase(BaseModel):
    """模型基础字段"""
    name: str = Field(..., min_length=1, max_length=100, description="名称")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    
    model_config = ConfigDict(from_attributes=True)

# 创建Schema
class YourModelCreate(YourModelBase):
    """创建模型时的数据结构"""
    # 只包含创建时需要的字段
    pass

# 更新Schema  
class YourModelUpdate(BaseModel):
    """更新模型时的数据结构"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    model_config = ConfigDict(from_attributes=True)

# 响应Schema
class YourModelResponse(YourModelBase):
    """API响应中的模型数据结构"""
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

# 列表响应Schema
class YourModelListResponse(BaseModel):
    """模型列表响应"""
    success: bool = True
    data: List[YourModelResponse]
    message: Optional[str] = None

# 单个响应Schema
class YourModelDetailResponse(BaseModel):
    """模型详情响应"""
    success: bool = True
    data: YourModelResponse
    message: Optional[str] = None
```

#### 开发规范要点

1. **Schema 分类**
   - `Base`: 包含共同字段的基础类
   - `Create`: 创建操作的数据结构
   - `Update`: 更新操作的数据结构 (字段多为 Optional)
   - `Response`: API 响应的数据结构

2. **字段验证**
   - 使用 `Field()` 定义验证规则和文档
   - 设置合适的长度限制 (`min_length`, `max_length`)
   - 使用专用类型 (`EmailStr`, `HttpUrl` 等)
   - 添加字段描述 (`description="说明"`)

3. **配置设置**
   - 设置 `model_config = ConfigDict(from_attributes=True)`
   - 支持从 ORM 对象直接转换

4. **响应包装**
   - 统一使用 `BaseResponse[T]` 包装响应数据
   - 包含 `success`, `data`, `message` 字段

### Service 层开发规范

**核心职责**: 业务逻辑实现、数据库操作和异常处理

#### 基本结构模板
```python
"""模块名称的业务逻辑服务"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import Dict, Any, List, Optional
from datetime import datetime

from .models import YourModel
from .schemas import YourModelCreate, YourModelUpdate
from src.shared.base_service import BaseService
from src.shared.exceptions import (
    NotFoundServiceException, ConflictServiceException,
    ValidationServiceException, AccessDeniedServiceException
)

class YourModelService(BaseService):
    """模型业务逻辑服务"""
    
    # 异常声明 (必需)
    METHOD_EXCEPTIONS = {
        'create_item': {ValidationServiceException, ConflictServiceException},
        'get_item': {NotFoundServiceException},
        'get_items': set(),
        'update_item': {NotFoundServiceException, ValidationServiceException},
        'delete_item': {NotFoundServiceException, AccessDeniedServiceException},
    }
    
    def create_item(self, data: YourModelCreate, user_id: int) -> Dict[str, Any]:
        """创建新项目"""
        try:
            # 1. 业务逻辑验证
            self._validate_create_data(data, user_id)
            
            # 2. 创建数据库记录
            item = YourModel(
                **data.model_dump(),
                user_id=user_id
            )
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            
            return {
                "item": item,
                "message": "创建成功"
            }
            
        except IntegrityError:
            self.db.rollback()
            raise ConflictServiceException("数据冲突，请检查唯一性约束")
    
    def get_item(self, item_id: int, user_id: int) -> Dict[str, Any]:
        """获取单个项目"""
        item = self.db.query(YourModel).options(
            joinedload(YourModel.user)  # 预加载关联数据
        ).filter(
            YourModel.id == item_id
        ).first()
        
        if not item:
            raise NotFoundServiceException("项目不存在")
        
        # 权限检查
        self._check_access_permission(item, user_id)
        
        return {
            "item": item,
            "message": None
        }
    
    def get_items(self, user_id: int, skip: int = 0, limit: int = 10) -> Dict[str, Any]:
        """获取项目列表"""
        query = self.db.query(YourModel).options(
            joinedload(YourModel.user)
        ).filter(
            YourModel.user_id == user_id
        )
        
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        
        return {
            "items": items,
            "total": total,
            "message": None
        }
    
    def update_item(self, item_id: int, data: YourModelUpdate, user_id: int) -> Dict[str, Any]:
        """更新项目"""
        item = self.db.query(YourModel).filter(YourModel.id == item_id).first()
        
        if not item:
            raise NotFoundServiceException("项目不存在")
        
        # 权限检查
        self._check_access_permission(item, user_id)
        
        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        
        self.db.commit()
        self.db.refresh(item)
        
        return {
            "item": item,
            "message": "更新成功"
        }
    
    def delete_item(self, item_id: int, user_id: int) -> Dict[str, Any]:
        """删除项目"""
        item = self.db.query(YourModel).filter(YourModel.id == item_id).first()
        
        if not item:
            raise NotFoundServiceException("项目不存在")
        
        # 权限检查
        self._check_access_permission(item, user_id)
        
        self.db.delete(item)
        self.db.commit()
        
        return {
            "message": "删除成功"
        }
    
    # 私有辅助方法
    def _validate_create_data(self, data: YourModelCreate, user_id: int):
        """验证创建数据"""
        # 实现业务逻辑验证
        pass
    
    def _check_access_permission(self, item: YourModel, user_id: int):
        """检查访问权限"""
        if item.user_id != user_id:
            raise AccessDeniedServiceException("无权访问该资源")
```

#### 开发规范要点

1. **基础结构**
   - 继承 `BaseService` 基类
   - 必须声明 `METHOD_EXCEPTIONS` 异常映射
   - 通过构造函数接收数据库会话

2. **方法命名**
   - CRUD操作: `create_*`, `get_*`, `update_*`, `delete_*`
   - 业务操作: 使用动词+名词形式
   - 私有方法: 使用 `_` 前缀

3. **异常处理**
   - 使用统一的 Service 异常类
   - 在 `METHOD_EXCEPTIONS` 中声明可能的异常
   - 使用合适的异常类型和错误消息

4. **数据库操作**
   - 使用 `joinedload()` 预加载关联数据
   - 正确处理事务 (`commit`, `rollback`)
   - 使用 `refresh()` 更新对象状态

5. **返回格式**
   - 统一返回 `Dict[str, Any]` 格式
   - 包含 `data/item/items` 和 `message` 字段

### Router 层开发规范

**核心职责**: HTTP 路由定义、请求处理和响应包装

#### 基本结构模板
```python
"""模块名称的 FastAPI 路由定义"""
from fastapi import APIRouter, Query, Path, status
from typing import List, Optional

from .service import YourModelService
from .schemas import (
    YourModelCreate, YourModelUpdate, YourModelResponse,
    YourModelListResponse, YourModelDetailResponse
)
from src.shared.dependencies import DbDep, UserDep
from src.shared.schemas import BaseResponse, MessageResponse
from src.shared.api_decorator import create_service_route_config, service_api_handler

# 创建路由器
router = APIRouter(prefix="/your-module")

# === CRUD 基础操作 ===

@router.post("/items", **create_service_route_config(
    YourModelService, 'create_item', BaseResponse[YourModelResponse],
    success_status=201,
    summary="创建项目",
    description="创建新的项目实例",
    operation_id="create_your_model_item"
))
@service_api_handler(YourModelService, 'create_item')
async def create_item(
    data: YourModelCreate,
    current_user: UserDep,
    db: DbDep
):
    """创建新项目"""
    service = YourModelService(db)
    result = service.create_item(data, current_user.id)
    
    return BaseResponse[YourModelResponse](
        success=True,
        data=YourModelResponse.model_validate(result["item"]),
        message=result["message"]
    )

@router.get("/items", **create_service_route_config(
    YourModelService, 'get_items', BaseResponse[List[YourModelResponse]],
    summary="获取项目列表",
    description="获取当前用户的项目列表，支持分页",
    operation_id="get_your_model_items"
))
@service_api_handler(YourModelService, 'get_items')
async def get_items(
    current_user: UserDep,
    db: DbDep,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数")
):
    """获取项目列表"""
    service = YourModelService(db)
    result = service.get_items(current_user.id, skip, limit)
    
    return BaseResponse[List[YourModelResponse]](
        success=True,
        data=[YourModelResponse.model_validate(item) for item in result["items"]],
        message=f"共找到 {result['total']} 个项目"
    )

@router.get("/items/{item_id}", **create_service_route_config(
    YourModelService, 'get_item', BaseResponse[YourModelResponse],
    summary="获取项目详情",
    description="根据ID获取项目的详细信息",
    operation_id="get_your_model_item"
))
@service_api_handler(YourModelService, 'get_item')
async def get_item(
    item_id: int = Path(..., gt=0, description="项目ID"),
    current_user: UserDep,
    db: DbDep
):
    """获取项目详情"""
    service = YourModelService(db)
    result = service.get_item(item_id, current_user.id)
    
    return BaseResponse[YourModelResponse](
        success=True,
        data=YourModelResponse.model_validate(result["item"]),
        message=result["message"]
    )

@router.put("/items/{item_id}", **create_service_route_config(
    YourModelService, 'update_item', BaseResponse[YourModelResponse],
    summary="更新项目",
    description="更新指定项目的信息",
    operation_id="update_your_model_item"
))
@service_api_handler(YourModelService, 'update_item')
async def update_item(
    data: YourModelUpdate,
    item_id: int = Path(..., gt=0, description="项目ID"),
    current_user: UserDep,
    db: DbDep
):
    """更新项目"""
    service = YourModelService(db)
    result = service.update_item(item_id, data, current_user.id)
    
    return BaseResponse[YourModelResponse](
        success=True,
        data=YourModelResponse.model_validate(result["item"]),
        message=result["message"]
    )

@router.delete("/items/{item_id}", **create_service_route_config(
    YourModelService, 'delete_item', MessageResponse,
    summary="删除项目",
    description="删除指定的项目",
    operation_id="delete_your_model_item"
))
@service_api_handler(YourModelService, 'delete_item')
async def delete_item(
    item_id: int = Path(..., gt=0, description="项目ID"),
    current_user: UserDep,
    db: DbDep
):
    """删除项目"""
    service = YourModelService(db)
    result = service.delete_item(item_id, current_user.id)
    
    return MessageResponse(
        success=True,
        data={},
        message=result["message"]
    )
```

#### 开发规范要点

1. **路由组织**
   - 使用 `APIRouter` 创建模块路由器
   - 设置合适的路由前缀 (`prefix="/module"`)
   - 按 RESTful 规范组织路径

2. **装饰器使用**
   - 使用 `create_service_route_config` 统一配置
   - 使用 `@service_api_handler` 处理异常
   - 设置完整的 OpenAPI 文档信息

3. **参数验证**
   - 使用 `Query()` 定义查询参数
   - 使用 `Path()` 定义路径参数
   - 设置合适的验证规则和描述

4. **异步声明**
   - 统一使用 `async def` 声明路由函数
   - 保持异步模式的一致性

5. **响应包装**
   - 使用统一的响应格式 (`BaseResponse[T]`)
   - 正确设置响应状态码
   - 包含有意义的消息内容

---

## 🔧 最佳实践指南

### 异常处理最佳实践

#### Service 层异常使用规范
```python
# ✅ 正确的异常使用
from src.shared.exceptions import (
    NotFoundServiceException,
    AccessDeniedServiceException,
    ConflictServiceException,
    ValidationServiceException,
    UnauthorizedServiceException,
    BadRequestServiceException
)
from src.shared.error_codes import ErrorCodes

# 声明异常映射
METHOD_EXCEPTIONS = {
    'method_name': {NotFoundServiceException, ValidationServiceException}
}

# 抛出异常 (使用统一错误码)
if not item:
    raise NotFoundServiceException("资源不存在", ErrorCodes.ITEM_NOT_FOUND)

if not has_permission:
    raise AccessDeniedServiceException("权限不足", ErrorCodes.ACCESS_DENIED)

# ❌ 错误：不要在Service层使用API层异常类
# raise UnauthorizedError(...)  # 错误！应使用 UnauthorizedServiceException
```

#### 统一错误码管理规范

**错误码文件**: `src/shared/error_codes.py`

```python
class ErrorCodes:
    """统一错误码定义 - 所有模块必须使用这些预定义常量"""
    
    # === 认证相关错误码 ===
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"        # 登录凭据无效
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"              # 账户被禁用
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"                  # 账户被锁定
    USER_NOT_FOUND = "USER_NOT_FOUND"                  # 用户不存在
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"        # 用户已存在
    USERNAME_EXISTS = "USERNAME_EXISTS"                # 用户名已存在
    INVALID_PASSWORD = "INVALID_PASSWORD"              # 密码错误
    
    # === 邮箱验证相关 ===
    EMAIL_EXISTS = "EMAIL_EXISTS"                      # 邮箱已存在
    EMAIL_NOT_FOUND = "EMAIL_NOT_FOUND"                # 邮箱不存在
    EMAIL_ALREADY_VERIFIED = "EMAIL_ALREADY_VERIFIED"  # 邮箱已验证
    INVALID_VERIFICATION_CODE = "INVALID_VERIFICATION_CODE"  # 验证码无效
    INVALID_EMAIL_DOMAIN = "INVALID_EMAIL_DOMAIN"      # 邮箱域名不支持
    
    # === 邀请码相关 ===
    INVALID_INVITE_CODE = "INVALID_INVITE_CODE"        # 邀请码无效
    INVITE_CODE_EXPIRED = "INVITE_CODE_EXPIRED"        # 邀请码过期
    REGISTRATION_DISABLED = "REGISTRATION_DISABLED"    # 注册功能已关闭
    
    # === 课程管理相关 ===
    COURSE_NOT_FOUND = "COURSE_NOT_FOUND"              # 课程不存在
    COURSE_ACCESS_DENIED = "COURSE_ACCESS_DENIED"      # 课程访问被拒绝
    COURSE_UPDATE_DENIED = "COURSE_UPDATE_DENIED"      # 课程更新被拒绝
    COURSE_DELETE_DENIED = "COURSE_DELETE_DENIED"      # 课程删除被拒绝
    COURSE_CODE_EXISTS = "COURSE_CODE_EXISTS"          # 课程代码已存在
    SEMESTER_NOT_FOUND = "SEMESTER_NOT_FOUND"          # 学期不存在
    SEMESTER_CODE_EXISTS = "SEMESTER_CODE_EXISTS"      # 学期代码已存在
    SEMESTER_HAS_COURSES = "SEMESTER_HAS_COURSES"      # 学期包含课程
    
    # === 系统相关 ===
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"        # 请求频率超限
    INVALID_RESET_TOKEN = "INVALID_RESET_TOKEN"        # 重置令牌无效
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"    # 服务器内部错误
```

**使用规范**:
```python
# ✅ 正确使用
from src.shared.error_codes import ErrorCodes

raise NotFoundServiceException("用户不存在", ErrorCodes.USER_NOT_FOUND)
raise ConflictServiceException("用户名已存在", ErrorCodes.USERNAME_EXISTS)

# ❌ 错误：不要硬编码错误码字符串
raise NotFoundServiceException("用户不存在", "USER_NOT_FOUND")  # 禁止！
```

#### 异常状态码映射
```python
# 自动映射到 HTTP 状态码
NotFoundServiceException     → 404 Not Found
AccessDeniedServiceException → 403 Forbidden  
UnauthorizedServiceException → 401 Unauthorized
ConflictServiceException     → 409 Conflict
ValidationServiceException   → 422 Unprocessable Entity
BadRequestServiceException   → 400 Bad Request
```

#### 异常处理强制要求

1. **Service层异常类使用强制规范**:
   - ✅ **必须使用**: `*ServiceException` 类
   - ❌ **严禁使用**: `*Error` 类 (这些是API层异常)

2. **错误码使用强制规范**:
   - ✅ **必须使用**: `ErrorCodes` 常量
   - ❌ **严禁使用**: 硬编码字符串

3. **METHOD_EXCEPTIONS声明强制规范**:
   - 必须声明所有可能抛出的异常类型
   - 声明的异常类型必须与实际代码一致

### 数据库操作最佳实践

#### 查询优化
```python
# ✅ 预加载关联数据，避免 N+1 问题
users = self.db.query(User).options(
    joinedload(User.profile),
    joinedload(User.courses),
    joinedload(User.files)
).all()

# ✅ 条件查询
active_users = self.db.query(User).filter(
    User.is_active == True,
    User.created_at >= start_date
).all()

# ✅ 分页查询
def get_paginated_items(self, skip: int = 0, limit: int = 10):
    return self.db.query(Model).offset(skip).limit(limit).all()
```

#### 事务管理
```python
def complex_operation(self):
    try:
        # 开始事务
        item1 = Model1(name="test")
        self.db.add(item1)
        self.db.flush()  # 获取 ID 但不提交
        
        # 使用第一个对象的 ID
        item2 = Model2(parent_id=item1.id)
        self.db.add(item2)
        
        # 统一提交事务
        self.db.commit()
        
        return {"item1": item1, "item2": item2}
        
    except Exception as e:
        # 回滚事务
        self.db.rollback()
        raise ConflictServiceException(f"操作失败: {str(e)}")
```

### API 设计最佳实践

#### RESTful 路由设计
```python
# 资源路由规范
GET    /api/v1/users           # 获取用户列表
POST   /api/v1/users           # 创建用户
GET    /api/v1/users/{id}      # 获取用户详情
PUT    /api/v1/users/{id}      # 更新用户
DELETE /api/v1/users/{id}      # 删除用户

# 子资源路由
GET    /api/v1/users/{id}/courses     # 获取用户的课程
POST   /api/v1/users/{id}/courses     # 为用户添加课程

# 操作路由
POST   /api/v1/users/{id}/activate    # 激活用户
POST   /api/v1/users/{id}/deactivate  # 停用用户
```

#### 响应格式标准化
```python
# 成功响应格式
{
    "success": true,
    "data": {...},           # 实际数据
    "message": "操作成功"    # 可选的消息
}

# 列表响应格式
{
    "success": true,
    "data": [...],
    "message": "共找到 10 个结果",
    "pagination": {          # 可选的分页信息
        "total": 100,
        "page": 1,
        "per_page": 10
    }
}

# 错误响应格式
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "数据验证失败",
        "details": {
            "field_errors": ["用户名不能为空"]
        }
    }
}
```

### 性能优化指南

#### 数据库查询优化
```python
# 1. 使用索引
class User(Base):
    username = Column(String(50), index=True)  # 为常查询字段添加索引
    email = Column(String(100), unique=True, index=True)

# 2. 批量操作
def create_multiple_items(self, items_data: List[dict]):
    items = [Model(**data) for data in items_data]
    self.db.add_all(items)  # 批量添加
    self.db.commit()

# 3. 选择性加载
def get_user_summary(self, user_id: int):
    return self.db.query(User.id, User.username, User.email).filter(
        User.id == user_id
    ).first()  # 只查询需要的字段
```

#### 缓存策略
```python
from functools import lru_cache

class ConfigService:
    @lru_cache(maxsize=100)
    def get_system_config(self, key: str):
        """缓存系统配置"""
        return self.db.query(Config).filter(Config.key == key).first()
```

### 安全性最佳实践

#### 权限控制
```python
def check_admin_permission(current_user: User):
    """检查管理员权限"""
    if not current_user.is_admin:
        raise AccessDeniedServiceException("需要管理员权限")

def check_resource_owner(resource, user_id: int):
    """检查资源所有权"""
    if resource.user_id != user_id:
        raise AccessDeniedServiceException("无权访问该资源")
```

#### 输入验证
```python
from pydantic import Field, validator

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, regex=r'^[a-zA-Z0-9_]+$')
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        """密码强度验证"""
        if not re.search(r'[A-Za-z]', v) or not re.search(r'\d', v):
            raise ValueError('密码必须包含字母和数字')
        return v
```

---

## 📝 代码规范

### 命名规范

#### Python 命名约定
```python
# 类名：PascalCase
class UserService:
    pass

class CourseManagementService:
    pass

# 函数和变量：snake_case
def get_user_profile():
    pass

def create_new_course():
    pass

user_name = "john"
course_list = []

# 常量：UPPER_SNAKE_CASE
MAX_FILE_SIZE = 10 * 1024 * 1024
DEFAULT_PAGE_SIZE = 20

# 私有方法：前缀下划线
def _validate_user_input():
    pass

def _calculate_score():
    pass
```

#### 数据库命名约定
```python
# 表名：snake_case 复数形式
class User(Base):
    __tablename__ = "users"

class CourseFile(Base):
    __tablename__ = "course_files"

# 字段名：snake_case
user_name = Column(String(50))
created_at = Column(DateTime)
is_active = Column(Boolean)

# 外键：表名_id
user_id = Column(Integer, ForeignKey("users.id"))
course_id = Column(Integer, ForeignKey("courses.id"))
```

### 类型注解规范

#### 基础类型注解
```python
from typing import Optional, List, Dict, Any, Union, Tuple

# 函数参数和返回值
def get_user(user_id: int) -> Optional[User]:
    pass

def create_users(user_data: List[UserCreate]) -> List[User]:
    pass

def get_user_stats() -> Dict[str, int]:
    pass

# 复杂类型
UserData = Dict[str, Union[str, int, bool]]
QueryResult = Tuple[List[User], int]  # (items, total)

def process_user_data(data: UserData) -> QueryResult:
    pass
```

#### 类属性类型注解
```python
class UserService:
    db: Session
    cache: Optional[Dict[str, Any]] = None
    max_retry: int = 3
    
    def __init__(self, db: Session):
        self.db = db
```

### 文档字符串规范

#### 函数文档格式
```python
def create_user(self, user_data: UserCreate, admin_id: int) -> Dict[str, Any]:
    """创建新用户
    
    创建一个新的用户账户，包括验证用户数据、检查唯一性约束、
    发送欢迎邮件等完整流程。
    
    Args:
        user_data: 用户创建数据，包含用户名、邮箱、密码等信息
        admin_id: 执行创建操作的管理员ID，用于审计日志
        
    Returns:
        包含以下键的字典：
        - user: 创建的用户对象
        - message: 操作结果消息
        
    Raises:
        ConflictServiceException: 用户名或邮箱已存在
        ValidationServiceException: 用户数据验证失败
        AccessDeniedServiceException: 管理员权限不足
        
    Example:
        ```python
        service = UserService(db)
        result = service.create_user(
            UserCreate(username="john", email="john@example.com", password="secret"),
            admin_id=1
        )
        print(f"Created user: {result['user'].username}")
        ```
    """
    pass
```

#### 类文档格式
```python
class UserService(BaseService):
    """用户管理服务
    
    提供用户相关的所有业务逻辑操作，包括用户的创建、查询、更新、
    删除以及认证相关功能。
    
    该服务继承自BaseService，自动获得数据库会话管理和异常处理能力。
    所有方法都会自动处理数据库事务和异常转换。
    
    Attributes:
        METHOD_EXCEPTIONS: 声明每个方法可能抛出的异常类型
        
    Example:
        ```python
        service = UserService(db_session)
        user = service.create_user(user_data, admin_id)
        ```
    """
    
    METHOD_EXCEPTIONS = {
        'create_user': {ConflictServiceException, ValidationServiceException},
        # ...
    }
```

### 导入语句规范

#### 导入顺序
```python
# 1. 标准库导入
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 2. 第三方库导入
from fastapi import APIRouter, Depends, Query
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session, relationship
from pydantic import BaseModel, Field

# 3. 本地应用导入
from .models import User, Course
from .schemas import UserCreate, UserUpdate
from .service import UserService
from src.shared.exceptions import NotFoundServiceException
from src.shared.dependencies import DbDep, UserDep
```

#### 导入别名规范
```python
# 避免名称冲突的别名
from datetime import datetime as dt
from .models import User as UserModel
from .schemas import User as UserSchema

# 常用别名
from sqlalchemy.orm import Session as DbSession
from typing import Dict, List, Optional, Any, Union as U
```

---

## 🧪 测试规范

### 单元测试结构

#### 测试文件组织
```
tests/
├── __init__.py
├── conftest.py              # pytest 配置和 fixtures
├── unit/                    # 单元测试
│   ├── test_auth_service.py
│   ├── test_course_service.py
│   └── test_storage_service.py
├── integration/             # 集成测试
│   ├── test_auth_api.py
│   └── test_course_api.py
└── e2e/                     # 端到端测试
    ├── test_user_workflows.py
    └── test_admin_workflows.py
```

#### 测试命名规范
```python
# 测试类命名：Test + 被测试的类名
class TestUserService:
    pass

class TestAuthRouter:
    pass

# 测试方法命名：test_ + 场景描述
def test_create_user_success():
    pass

def test_create_user_with_duplicate_email_should_raise_conflict():
    pass

def test_get_user_with_invalid_id_should_raise_not_found():
    pass
```

#### 测试用例模板
```python
import pytest
from sqlalchemy.orm import Session
from src.auth.service import AuthService
from src.auth.schemas import UserCreate
from src.shared.exceptions import ConflictServiceException

class TestAuthService:
    """认证服务测试类"""
    
    def test_create_user_success(self, db_session: Session, sample_user_data: UserCreate):
        """测试成功创建用户"""
        # Arrange
        service = AuthService(db_session)
        
        # Act
        result = service.create_user(sample_user_data, admin_id=1)
        
        # Assert
        assert result["user"].username == sample_user_data.username
        assert result["user"].email == sample_user_data.email
        assert "创建成功" in result["message"]
    
    def test_create_user_with_duplicate_email_should_raise_conflict(
        self, db_session: Session, existing_user, sample_user_data: UserCreate
    ):
        """测试创建重复邮箱用户应该抛出冲突异常"""
        # Arrange
        service = AuthService(db_session)
        sample_user_data.email = existing_user.email
        
        # Act & Assert
        with pytest.raises(ConflictServiceException) as exc_info:
            service.create_user(sample_user_data, admin_id=1)
        
        assert "邮箱已存在" in str(exc_info.value)
```

### Fixtures 定义

#### 基础 Fixtures
```python
# conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.shared.database import Base

@pytest.fixture(scope="session")
def test_engine():
    """测试数据库引擎"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def db_session(test_engine):
    """数据库会话"""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return UserCreate(
        username="testuser",
        email="test@example.com",
        password="password123",
        invite_code="TEST001"
    )
```

---

## 🚀 部署和环境配置

### 环境变量配置

#### 配置文件结构
```python
# src/shared/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    """应用配置"""
    
    # 基础配置
    app_name: str = "Campus LLM System"
    app_version: str = "2.0.0"
    environment: str = "development"
    debug: bool = True
    
    # 数据库配置
    database_url: str = "mysql://user:pass@localhost/campus_llm"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis 配置
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT 配置
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # 邮件配置
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    
    # CORS 配置
    cors_origins: str = "*"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

#### 环境文件示例
```bash
# .env.development
APP_NAME="Campus LLM System"
ENVIRONMENT="development"
DEBUG=true

DATABASE_URL="mysql://root:password@localhost:3306/campus_llm_dev"
REDIS_URL="redis://localhost:6379/0"

SECRET_KEY="your-super-secret-key-here"
ACCESS_TOKEN_EXPIRE_MINUTES=60

SMTP_SERVER="smtp.gmail.com"
SMTP_PORT=587
SMTP_USERNAME="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"

CORS_ORIGINS="http://localhost:3000,http://localhost:8080"
```

### Docker 配置

#### Dockerfile
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 设置环境变量
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### docker-compose.yml
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql://root:password@db:3306/campus_llm
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data

  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: password
      MYSQL_DATABASE: campus_llm
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  mysql_data:
```

---

## 📊 监控和日志

### 日志配置

#### 日志格式标准
```python
# src/shared/logging.py
import logging
import sys
from datetime import datetime

# 自定义格式器
class CustomFormatter(logging.Formatter):
    """自定义日志格式器"""
    
    def format(self, record):
        # 添加时间戳
        record.timestamp = datetime.utcnow().isoformat()
        
        # 添加模块信息
        if hasattr(record, 'module'):
            record.module_info = f"[{record.module}]"
        else:
            record.module_info = ""
        
        return super().format(record)

def setup_logging():
    """设置应用日志"""
    
    # 创建格式器
    formatter = CustomFormatter(
        fmt='%(timestamp)s - %(name)s - %(levelname)s - %(module_info)s %(message)s'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # 文件处理器
    file_handler = logging.FileHandler('app.log')
    file_handler.setFormatter(formatter)
    
    # 根日志器配置
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
```

#### 业务日志使用
```python
import logging

logger = logging.getLogger(__name__)

class UserService(BaseService):
    def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """创建用户"""
        logger.info(f"开始创建用户: {user_data.username}", extra={'module': 'auth'})
        
        try:
            # 业务逻辑
            user = User(**user_data.model_dump())
            self.db.add(user)
            self.db.commit()
            
            logger.info(f"用户创建成功: ID={user.id}", extra={'module': 'auth'})
            return {"user": user, "message": "创建成功"}
            
        except Exception as e:
            logger.error(f"用户创建失败: {str(e)}", extra={'module': 'auth'})
            raise
```

### 性能监控

#### 请求处理时间监控
```python
# src/shared/middleware.py
import time
import logging
from fastapi import Request, Response

logger = logging.getLogger(__name__)

async def timing_middleware(request: Request, call_next):
    """请求处理时间监控中间件"""
    start_time = time.time()
    
    # 执行请求
    response = await call_next(request)
    
    # 计算处理时间
    process_time = time.time() - start_time
    
    # 记录日志
    logger.info(
        f"请求处理完成: {request.method} {request.url.path} - "
        f"状态码: {response.status_code} - 处理时间: {process_time:.3f}s",
        extra={
            'module': 'middleware',
            'method': request.method,
            'path': request.url.path,
            'status_code': response.status_code,
            'process_time': process_time
        }
    )
    
    # 添加响应头
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
```

---

## 📖 总结

本开发规范文档基于 Campus LLM System v2 的 FastAPI 架构审核结果制定，旨在确保项目的一致性、可维护性和可扩展性。

### 核心原则

1. **严格遵循四层架构** - Model-Schema-Service-Router 分层清晰
2. **统一的开发模式** - 所有模块使用相同的实现模式
3. **完整的类型安全** - 100% 类型注解覆盖
4. **规范的异常处理** - 统一的异常类型和错误响应
5. **优秀的代码质量** - 统一的命名规范和文档标准

### 持续改进

本规范文档会随着项目的发展和 FastAPI 最佳实践的更新而持续改进。建议：

- 每季度回顾和更新规范
- 新功能开发前参考本规范
- 代码审查时严格执行规范要求
- 及时记录和分享最佳实践经验

遵循本规范将有助于构建高质量、易维护的 FastAPI 应用程序。