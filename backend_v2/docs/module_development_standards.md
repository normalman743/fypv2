# Backend v2 模块重构标准

> 注意和之前的api兼容,model要兼容可以增加 

> 基于 Auth 模块的成功实践，建立后续模块开发的标准规范

## 🎯 核心设计原则

### 1. 模块化架构
- **按业务领域组织**：每个模块围绕一个业务领域（auth, admin, course等）
- **高内聚低耦合**：模块内部功能紧密相关，模块间依赖最小化
- **标准化结构**：所有模块遵循相同的文件组织和命名约定

### 2. FastAPI 2024 最佳实践
- **现代依赖注入**：使用 `Annotated[Type, Depends()]` 语法
- **统一错误处理**：使用 `BaseAPIException` 和 `ErrorResponse`
- **完整文档生成**：确保 OpenAPI 文档自动生成质量
- **分层架构**：Router → Service → Models 清晰分离
- **自动化响应文档**：使用 `@service_api` 装饰器基于Service异常生成OpenAPI文档
- **统一响应格式**：使用 `BaseResponse[T]` 泛型分离 message 和 data

## 📁 标准模块结构

```
src/{module_name}/
├── __init__.py         # 模块导出
├── router.py           # FastAPI 路由定义
├── schemas.py          # Pydantic 请求/响应模型  
├── models.py           # SQLAlchemy 数据库模型
├── service.py          # 业务逻辑实现
├── dependencies.py     # 模块特定依赖（可选）
├── exceptions.py       # 模块特定异常（可选）
└── utils.py           # 工具函数（可选）
```

## 🔧 文件实现标准

### 1. schemas.py 规范

#### 统一验证规则
```python
# 复用验证函数，保持一致性
def _validate_username(username: str) -> str:
    if not re.match(USERNAME_PATTERN, username):
        raise ValueError('用户名格式错误')
    return username.lower()

class BaseRequest(BaseModel):
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        return _validate_username(v)
```

#### 响应模型标准（FastAPI 2024最佳实践）
```python
# 使用泛型基类 - message 和 data 分离
class BaseResponse(BaseModel, Generic[T]):
    success: bool = Field(default=True, description="操作是否成功")
    data: T = Field(..., description="响应数据")
    message: Optional[str] = Field(None, description="操作消息")

# 数据载荷类
class ItemData(BaseModel):
    """项目数据载荷"""
    item: ItemResponse = Field(..., description="项目信息")

# 具体响应模型 - 包含完整示例
class CreateItemResponse(BaseResponse[ItemData]):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "success": True,
                "data": {
                    "item": {
                        "id": 1,
                        "name": "示例项目",
                        "created_at": "2024-01-01T00:00:00Z"
                    }
                },
                "message": "项目创建成功"
            }]
        }
    )
```

#### 字段文档标准
```python
class UserCreate(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=20,
        description="用户名 (3-20位，仅支持字母、数字、下划线)",
        examples=["john_doe"]
    )
```

### 2. models.py 规范

#### 基础模型标准
```python
class StandardModel(Base):
    __tablename__ = "table_name"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 基础字段（根据需要添加）
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True, index=True)
    
    # 业务字段
    name = Column(String(100), nullable=False, index=True)
    
    # 关系定义
    items = relationship("Item", back_populates="owner")
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id}, name='{self.name}')>"
```

#### 索引设计原则
- 主键自动索引
- 外键字段建议索引
- 频繁查询字段建议索引
- 唯一约束字段自动索引

### 3. service.py 规范

#### 异常声明标准（必须实现 - 用于自动生成OpenAPI文档）
```python
class ModuleService:
    # 必须声明每个方法可能抛出的异常 - 用于 @service_api 装饰器
    METHOD_EXCEPTIONS = {
        'create_item': {BadRequestError, ConflictError, ForbiddenError},
        'update_item': {BadRequestError, NotFoundError, ForbiddenError},
        'delete_item': {NotFoundError, ForbiddenError},
        'get_item': {NotFoundError, ForbiddenError},  # 即使是查询也要声明
        'list_items': set(),  # 无特定异常的方法使用空集合
    }
    
    def __init__(self, db: Session):
        self.db = db
        
    # 所有声明的异常必须在实际代码中可能被抛出
    def create_item(self, request: ItemCreate, user_id: int) -> Dict[str, Any]:
        """创建项目 - 返回包含message的字典"""
        if not self._has_create_permission(user_id):
            raise ForbiddenError("无权限创建项目")
            
        if self._item_exists(request.name):
            raise ConflictError("项目名称已存在")
            
        item = self._create_item_record(request, user_id)
        return {
            "item": item,
            "message": "项目创建成功"
        }
```

#### 业务方法标准
```python
def create_item(self, request: ItemCreate, user_id: int) -> Item:
    """创建项目"""
    # 1. 权限检查
    self._check_create_permission(user_id)
    
    # 2. 业务验证
    self._validate_item_data(request)
    
    # 3. 数据操作
    item = self._create_item_record(request, user_id)
    
    # 4. 后置处理（如需要）
    self._send_creation_notification(item)
    
    return item

def _check_create_permission(self, user_id: int):
    """权限检查 - 私有方法"""
    # 具体权限逻辑

def _validate_item_data(self, request: ItemCreate):
    """业务验证 - 私有方法"""
    # 业务规则验证
```

### 4. router.py 规范

#### 路由配置标准（FastAPI 2024最佳实践）
```python
# 使用 Service API 装饰器 - 自动生成响应文档
@router.post("/items", **create_service_route_config(
    ModuleService, 'create_item', CreateItemResponse,
    success_status=201,
    summary="创建项目",
    description="创建新的项目，需要用户认证",
    tags=["项目管理"],
    operation_id="create_item"
))
@service_api_handler(ModuleService, 'create_item')
async def create_item(
    request: ItemCreate,
    current_user: UserDep,
    db: DbDep
):
    """创建项目"""
    service = ModuleService(db)
    result = service.create_item(request, current_user.id)  # 注意：User对象，不是字典
    
    return CreateItemResponse(
        success=True,
        data=ItemData(item=ItemResponse.model_validate(result["item"])),
        message=result.get("message", "项目创建成功")
    )

# 传统手动配置方式（仅在特殊情况下使用）
@router.get(
    "/items/{item_id}",
    response_model=ItemDetailResponse,
    responses={
        404: {"model": ErrorResponse, "description": "项目不存在"},
        403: {"model": ErrorResponse, "description": "无访问权限"}
    },
    summary="获取项目详情"
)
async def get_item(item_id: int, current_user: UserDep, db: DbDep):
    """获取项目详情 - 特殊逻辑不通过Service"""
    # 直接处理的简单逻辑
    pass
```

#### URL 命名约定
```python
# RESTful 风格
GET    /api/v1/items          # 获取列表
POST   /api/v1/items          # 创建项目
GET    /api/v1/items/{id}     # 获取详情
PUT    /api/v1/items/{id}     # 更新项目
DELETE /api/v1/items/{id}     # 删除项目

# 特殊操作
POST   /api/v1/items/{id}/activate   # 激活
POST   /api/v1/items/{id}/archive    # 归档
```

## 🔗 模块间依赖管理

### 1. 依赖原则
- **最小依赖**：只依赖必需的模块
- **明确接口**：通过定义良好的接口交互
- **避免循环**：通过 shared 模块解决公共依赖

### 2. 依赖层次
```
┌─────────────┐
│ ai (AI功能) │ 
├─────────────┤
│ chat (聊天) │ ← 依赖 auth, course
├─────────────┤  
│ storage (存储)│ ← 依赖 auth, course
├─────────────┤
│ course (课程)│ ← 依赖 auth
├─────────────┤
│ admin (管理)│ ← 依赖 auth  
├─────────────┤
│ auth (认证) │ ← 基础模块，无业务依赖
├─────────────┤
│ shared (共享)│ ← 技术基础设施
└─────────────┘
```

### 3. 跨模块引用
```python
# 正确方式：通过 shared 模块
from src.shared.dependencies import UserDep
from src.shared.exceptions import BadRequestError

# 避免：直接跨业务模块引用
# from src.auth.models import User  # 避免
```

## ⚙️ 配置管理标准

### 1. 环境变量命名
```python
# 模块特定配置使用前缀
AUTH_MAX_LOGIN_ATTEMPTS = 5
COURSE_AUTO_ARCHIVE_DAYS = 365  
STORAGE_MAX_FILE_SIZE = 52428800

# 全局配置不使用前缀
DATABASE_URL = "..."
SECRET_KEY = "..."
```

### 2. 配置验证
```python
class Settings(BaseSettings):
    # 模块特定配置分组
    # Auth 配置
    max_login_attempts: int = Field(5, env="AUTH_MAX_LOGIN_ATTEMPTS")
    
    # Course 配置  
    auto_archive_days: int = Field(365, env="COURSE_AUTO_ARCHIVE_DAYS")
    
    @field_validator('max_login_attempts')
    @classmethod
    def validate_login_attempts(cls, v: int) -> int:
        if v < 1 or v > 10:
            raise ValueError("登录尝试次数必须在1-10之间")
        return v
```

## 📊 数据库设计标准

### 1. 命名约定
- **表名**：复数形式，下划线分隔（users, invite_codes）
- **字段名**：下划线分隔（created_at, user_id）
- **外键**：{table}_id 格式（user_id, course_id）
- **索引名**：idx_{table}_{field} 格式

### 2. 通用字段
```python
# 每个业务表建议包含
id = Column(Integer, primary_key=True, index=True)
created_at = Column(DateTime, server_default=func.now())
updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

# 需要软删除的表
is_active = Column(Boolean, default=True, index=True)

# 需要审计的表  
created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
```

### 3. 关系设计
```python
# 一对多关系
class User(Base):
    courses = relationship("Course", back_populates="user")

class Course(Base):
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="courses")

# 多对多关系
class User(Base):
    roles = relationship("Role", secondary="user_roles", back_populates="users")
```

## 🛠️ Service API 装饰器使用指南

### 1. 核心组件
```python
# 导入必要组件
from src.shared.api_decorator import create_service_route_config, service_api_handler
```

### 2. 使用步骤
1. **Service层声明异常** → 在 `METHOD_EXCEPTIONS` 中声明所有可能异常
2. **Router层使用装饰器** → 用 `create_service_route_config` 生成路由配置
3. **自动生成文档** → OpenAPI 文档自动包含所有错误响应

### 3. 完整示例
```python
# service.py
class ItemService:
    METHOD_EXCEPTIONS = {
        'create_item': {BadRequestError, ConflictError, ForbiddenError}
    }
    
    def create_item(self, request: ItemCreate, user_id: int) -> Dict[str, Any]:
        # 业务逻辑
        return {"item": item, "message": "创建成功"}

# router.py
@router.post("/items", **create_service_route_config(
    ItemService, 'create_item', CreateItemResponse,
    success_status=201,
    summary="创建项目"
))
@service_api_handler(ItemService, 'create_item')
async def create_item(request: ItemCreate, user: UserDep, db: DbDep):
    service = ItemService(db)
    result = service.create_item(request, user.id)
    return CreateItemResponse(
        success=True,
        data=ItemData(item=ItemResponse.model_validate(result["item"])),
        message=result["message"]
    )
```

### 4. 优势
- **自动化文档生成**：根据Service异常自动生成400/403/409等错误响应
- **类型安全**：确保Router层处理的异常与Service层声明一致
- **开发效率**：无需手动编写 `responses` 配置
- **维护性**：Service层修改异常时，文档自动同步更新

## 🚀 开发流程标准

### 1. 模块开发步骤
1. **需求分析** → 创建 API 设计文档
2. **架构设计** → 设计数据模型和业务流程  
3. **代码实现** → schemas → models → service（含异常声明） → router（使用装饰器）
4. **质量检查** → fastapi-best-practices-expert 审查
5. **测试验证** → 编写完整测试用例
6. **文档完善** → 更新 API 文档和使用说明

### 2. Git 提交标准
```bash
# 第一次提交：基础架构
git commit -m "feat: 建立{Module}模块基础架构
- 创建 schemas/models/service/router 文件
- 实现核心数据模型
- 配置模块依赖和导出"

# 第二次提交：功能实现
git commit -m "feat: 实现{Module}模块完整功能
- {具体功能列表}
- 符合 FastAPI 最佳实践
- 通过代码质量审查"
```

### 3. 质量检查标准
- ✅ FastAPI Expert 评分 4+ 星
- ✅ 所有 API 有完整文档（通过 @service_api 装饰器自动生成）
- ✅ 错误响应格式统一（使用 BaseResponse[T] 和 ErrorResponse）
- ✅ Service层完整的 METHOD_EXCEPTIONS 声明
- ✅ 依赖注入返回正确的对象类型（User对象而非字典）
- ✅ 响应模型正确分离 message 和 data
- ✅ 测试覆盖核心业务路径
- ✅ 符合本标准规范

## 🎯 成功标准

一个合格的模块应该：

1. **架构清晰**：遵循标准文件组织，职责分离明确
2. **文档完整**：API 自动生成文档，错误响应完整
3. **测试覆盖**：核心业务逻辑有测试验证
4. **代码质量**：通过 FastAPI 专家审查，评分 4+ 星
5. **兼容性好**：与现有模块协作良好，依赖关系清晰

---

**Auth 模块已成功达到以上所有标准，可作为后续模块开发的参考模板。**