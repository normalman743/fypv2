# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Campus LLM System (校园LLM系统) - a RAG-based intelligent campus assistant that provides unified academic support and campus life information services for university students. The system integrates document processing, vector search, and conversational AI capabilities.

## Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with async support
- **Database**: MySQL + Chroma vector database
- **AI/RAG**: LangChain with OpenAI integration
- **Task Queue**: Celery with Redis
- **File Storage**: Local filesystem with SHA256 deduplication

### Key Components
- **Models**: SQLAlchemy ORM models in `app/models/`
- **API Routes**: REST endpoints in `app/api/v1/`
- **Services**: Business logic in `app/services/`
- **Schemas**: Pydantic models in `app/schemas/`
- **Tasks**: Async file processing in `app/tasks/`

## Development Commands

### Database Management
you can find database info in
/Users/mannormal/Downloads/fyp/campus_llm_database_analysis.md


### Running the Application
```bash
# Start FastAPI server
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 

注意请你不要自己打开 让user 开启 以便user提供错误代码
```

### 注意事项

1. 使用python前注意source venv
2. 如果需要curl或者直接和localhost 8000 注意--noproxy
3. 注意不能修改所有的api文档 可以增加 不能修改 这个是最终对齐方向
4. 目前有的api访问 8000/docx
5. **测试健壮性原则**：写测试文件时不要假设硬编码的ID（如course_id=1），应动态获取或在reset系统中创建所需的基础数据 


## Workflow

### API开发标准流程

1. **API文档设计**: 编写详细的api_*.md文档，定义接口规范
2. **API实现对齐**: 确保实际API实现与文档规范完全对齐
3. **系统化测试**: 使用api_test_v3进行全面测试验证

### 测试流程

#### 使用api_test_v3进行测试
```bash
cd backend/api_test_v3
python -m pytest test_specific_module.py -v
```

#### 测试进度跟踪
按照API文档模块组织：

- ✅ **已完成测试**: 
  - 认证与用户管理 (api_auth.md → test_auth_user.py)
  - 学期与课程管理 (api_semester_course.md → test_semester_course.py, test_course_folders.py)
  - 文件夹与文件管理 (api_folder_file.md → test_file_upload.py) ⚠️ 部分API未实现
  
- ⏳ **待测试**: 
  - 聊天、消息与AI功能 (api_chat_message_rag.md → test_chat_message.py)
  - 系统管理 (api_admin.md → test_admin_functions.py)
  - 删除操作 (跨模块功能 → test_delete_operations.py)

#### 测试注意事项
- 测试前确保数据库已启动并连接正常
- 使用reset_system.py重置测试环境
- 测试时注意--noproxy参数用于本地连接

#### API开发和测试重要原则

⚠️ **编写测试API前的必要步骤**：
1. **查看API文档** - 先阅读对应的`api_*.md`文档了解接口定义
2. **检查真实API** - 访问 `/openapi.json` 或 `/docs` 查看实际API参数和响应格式
3. **对比验证** - 确保文档与实际实现一致，发现不匹配及时更新

⚠️ **编写真实API前的必要步骤**：
1. **查看API文档** - 确保理解业务需求和接口规范
2. **检查数据库结构** - 参考 `/Users/mannormal/Downloads/fyp/campus_llm_database_analysis.md` 了解表结构和字段
3. **验证数据一致性** - 确保API设计与数据库模型匹配

⚠️ **三方对齐原则**：
- **API文档** ↔ **真实API实现** ↔ **数据库结构** 必须保持一致
- 任何修改都要同时更新相关的文档、代码和数据库
- 测试用例要基于最新的API文档编写

🔍 **常见对齐检查点**：
- **字段名称**: 确保API文档、数据库字段、请求参数名称一致
- **数据类型**: 确保string、int、boolean等类型在三方中匹配
- **必填字段**: 确保required字段在API和数据库中都正确标记
- **枚举值**: 确保状态码、类型等枚举值在各处保持一致

📋 **开发检查清单**：
- [ ] 查看现有API文档了解接口规范
- [ ] 检查 `/openapi.json` 确认当前API实现  
- [ ] 查看数据库分析文档确认表结构
- [ ] 对比三者找出不一致之处
- [ ] 优先以数据库结构为准，更新API文档和实现



### 注意 不要再main上开发 每次改bug 测试新功能使用new branch

## Claude Code 使用规范

### 代码质量要求
1. **第一次就写对** - 避免写有bug的代码，宁愿先思考清楚再动手
2. **使用成熟的库** - 优先使用经过验证的库，而不是自己写脚本
3. **不要过度工程** - 简单问题用简单方案解决，不要引入不必要的复杂性

### 测试开发流程
1. **先修复现有bug** - 不要把bug固化到测试快照中
2. **功能测试优先** - 确保API功能正确后，再做格式快照
3. **复用现有代码** - 优先使用和改进 api_test_v3，而不是从头开始

### 重构原则
1. **避免代码重复** - 相同功能应该只有一份实现，通过导入复用
2. **统一管理认证** - 登录相关函数应该集中在 test_auth_user.py
3. **遵循API命名** - 测试函数名应该与API路径和操作对应

### 安装软件原则
1. **避免频繁安装** - 不要连续安装多个类似功能的库
2. **先询问用户** - 安装新库前要说明用途并征得同意
3. **使用现有工具** - 能用已有工具解决的不要引入新依赖

### API 错误响应最佳实践

#### 统一错误响应格式
所有 API 错误响应都应使用 `ErrorResponse` 模型：
```python
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "用户友好的错误信息",
    "details": {  // 可选，用于详细错误信息
      "field": "具体字段错误"
    }
  }
}
```

#### 使用 APIResponses.create_with_examples()
为每个 API 端点配置详细的错误响应示例：
```python
@router.post(
    "/endpoint",
    responses={
        **APIResponses.create_with_examples(**{
            400: [
                {"code": "ERROR_1", "message": "错误1", "summary": "错误1描述"},
                {"code": "ERROR_2", "message": "错误2", "summary": "错误2描述"}
            ],
            401: {"code": "UNAUTHORIZED", "message": "未认证"}
        })
    }
)
```

#### Service 层异常声明
每个 Service 类应声明 METHOD_EXCEPTIONS：
```python
class Service:
    METHOD_EXCEPTIONS = {
        'method_name': {ExceptionClass1, ExceptionClass2}
    }
```

## 技术债和待改进事项

### 1. API 响应格式标准化
**当前问题**：
- OpenAPI 文档中的错误响应格式不符合 FastAPI 最佳实践
- 缺少统一的响应格式装饰器或中间件
- 422 验证错误使用了自定义格式，但 OpenAPI 文档显示的是 FastAPI 默认格式

**建议方案**：
- 研究 FastAPI 官方推荐的响应文档配置方式
- 使用 `responses` 参数时遵循 OpenAPI 3.0 规范
- 考虑使用 FastAPI 的 `response_model` 和 `responses` 组合

### 2. 代码架构层次问题
**当前状态**：
- ✅ **Controller层 (API Routes)**: auth.py 已重构完成，业务逻辑迁移到 AuthService
- ✅ **Service层**: AuthService 完善，包含异常声明和统一错误处理
- ⏳ **Repository层**: 待实现，数据库操作仍在 service 层
- ✅ **异常处理**: 统一使用 BaseAPIException，OpenAPI 文档完整展示错误响应

**已完成优化**：
- ✅ `app/api/v1/auth.py` - 业务逻辑已迁移到 AuthService，路由精简至15行/端点
- ✅ `app/core/api_decorator.py` - 实现 APIResponses.create_with_examples() 统一错误文档
- ✅ `app/schemas/common.py` - ErrorResponse 使用 ErrorDetail 结构，支持详细错误信息
- ✅ `app/services/auth_service.py` - 完整的 METHOD_EXCEPTIONS 声明

**需要 Code Review 的关键文件**：
- `app/api/v1/files.py` - 文件处理逻辑应该在 service 层
- `app/services/*` - 需要统一其他 service 层的职责边界
- `app/models/*` - 考虑添加 repository 层来封装数据访问

### 3. Celery 异步任务队列
**当前状态**：
- 已安装 Celery 和 Redis 依赖
- 存在 `app/tasks/` 目录但未实现
- 文件处理等耗时操作仍在同步执行

**待实现功能**：
- 文件向量化处理
- 邮件发送队列
- 定时清理任务
- RAG 索引更新

### 4. Alembic 数据库迁移
**当前状态**：
- 已初始化 alembic（存在 alembic.ini）
- 但实际使用 `Base.metadata.create_all()` 直接创建表
- 没有版本化的数据库迁移记录

**风险**：
- 生产环境数据库升级困难
- 无法回滚数据库变更
- 团队协作时数据库同步问题

**建议**：
```bash
# 生成初始迁移
alembic revision --autogenerate -m "Initial migration"
# 应用迁移
alembic upgrade head
```

### 5. 其他技术债
- **测试覆盖率**: api_test_v3 需要继续完善
- **API 文档**: 部分 API 实现与文档不一致
- **配置管理**: 环境变量过多，考虑分组管理
- **日志系统**: 需要结构化日志和日志聚合
- **监控告警**: 缺少 APM 和错误追踪
- **安全加固**: 需要添加 API 限流、SQL 注入防护等
- **性能优化**: 缺少缓存层、数据库查询优化

## API 响应文档最佳实践

### 问题背景
FastAPI 默认只显示 200 成功响应和 422 验证错误，不会显示 Service 层可能抛出的业务异常（如 400, 401, 403, 409 等），导致 API 文档不完整。

### 解决方案：Service API 装饰器

#### 1. 在 Service 类中声明异常
```python
class AuthService:
    # 声明每个方法可能抛出的异常
    METHOD_EXCEPTIONS = {
        'register': {BadRequestError, ConflictError, ForbiddenError},
        'login': {UnauthorizedError},
        'update_user': {BadRequestError, ConflictError, ForbiddenError},
        'verify_email': {BadRequestError},
        'resend_verification': {BadRequestError}
    }
```

#### 2. 使用装饰器简化路由
```python
from app.core.api_decorator import service_api

@router.post("/register")
@service_api(AuthService, 'register', SuccessResponse, summary="用户注册")
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    service = AuthService(db)
    result = service.register(user_data)
    return SuccessResponse(...)
```

#### 3. 自动化的好处
- **自动生成 OpenAPI 响应文档**：根据 Service 异常自动生成 400, 403, 409 等响应
- **类型安全**：确保路由层捕获的异常与 Service 声明一致
- **文档同步**：Service 层修改异常时，API 文档自动更新
- **代码简化**：无需手动写 try-catch 和 responses 参数

#### 4. 效果对比
**之前**：
```python
@router.post("/register", response_model=SuccessResponse, responses={
    400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 409: {"model": ErrorResponse}
})
async def register(...):
    try:
        service = AuthService(db)
        result = service.register(user_data)
        return SuccessResponse(...)
    except (BadRequestError, ConflictError, ForbiddenError) as e:
        raise e
```

**现在**：
```python
@router.post("/register")
@service_api(AuthService, 'register', SuccessResponse)
async def register(...):
    service = AuthService(db)
    result = service.register(user_data)
    return SuccessResponse(...)
```

#### 5. 实施规范
- 所有 Service 类必须定义 `METHOD_EXCEPTIONS`
- 新增 Service 方法时同步更新异常声明
- 路由层统一使用 `@service_api` 装饰器
