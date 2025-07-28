# CLAUDE.md

This file provides guidance to Claude Code when working with the Campus LLM System codebase.

## 🎯 项目概览

### 项目简介
Campus LLM System (校园LLM系统) - 基于 RAG 的智能校园助手，为大学生提供统一的学术支持和校园生活信息服务。集成文档处理、向量搜索和对话AI功能。

### 架构版本

#### Backend v1 (传统分层架构)
- **位置**: `backend/app/`
- **结构**: 按技术层次分离 - `models/`, `schemas/`, `services/`, `api/v1/`
- **启动**: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000`
- **文档**: http://localhost:8000/docs

#### Backend v2 (模块化架构) 
- **位置**: `backend_v2/src/`
- **结构**: 按业务领域组织 - `auth/`, `admin/`, `course/`, `storage/`, `chat/`, `ai/`, `shared/`
- **启动**: `cd backend_v2 && source v2env/bin/activate && uvicorn src.main:app --reload --port 8001`
- **原则**: 高内聚低耦合，每个模块包含完整的 router、schemas、models、service

## 🛠️ 技术栈工具

### 版本控制
- **Git**: 不在 main 分支开发，功能开发使用 feature 分支
- **提交**: 有重大代码变更时注意及时 commit

### 核心技术
- **FastAPI**: 异步 Web 框架，严格遵循四层架构
- **MySQL**: 主数据库，支持索引和外键约束
- **Chroma**: 向量数据库，用于 RAG 功能
- **Alembic**: 数据库迁移工具 (`alembic revision --autogenerate`, `alembic upgrade head`)

### 异步和AI
- **Celery + Redis**: 异步任务队列（文件向量化、邮件发送、定时清理）
- **LangChain + OpenAI**: AI/RAG 集成，文档处理和对话功能
- **文件存储**: 本地文件系统 + SHA256 去重

## 🏗️ FastAPI 四层架构最佳实践

### Model 层 (数据库模型)
- **职责**: SQLAlchemy ORM 模型，定义数据库表结构
- **位置**: `models.py` 或 `models/`
- **规范**: 
  - 定义表关系、索引、约束
  - 使用 `relationship()` 定义关联
  - 避免业务逻辑，专注数据结构

### Schema 层 (数据验证)
- **职责**: Pydantic 模型，API 请求/响应数据验证和序列化
- **位置**: `schemas.py`
- **规范**:
  - 创建 Create/Update/Get/List 等不同操作的 Schema
  - 使用 `Field()` 添加验证和文档
  - 设置 `model_config = {"from_attributes": True}` 支持 ORM 转换

### Service 层 (业务逻辑)
- **职责**: 核心业务逻辑，数据库操作，异常处理
- **位置**: `service.py`
- **规范**:
  - 声明 `METHOD_EXCEPTIONS` 定义每个方法可能抛出的异常
  - 使用 `joinedload()` 优化数据库查询，避免 N+1 问题
  - 专注业务逻辑，数据格式化交给 Pydantic
  - 正确的事务管理 (try/except/rollback)

### API 层 (路由定义)
- **职责**: 定义 HTTP 路由，依赖注入，调用 Service 层
- **位置**: `router.py` 或 `api/`
- **规范**:
  - 使用正确的响应模型类型 (避免复用 Create 响应给 Get 操作)
  - 路径参数、查询参数正确类型注解
  - Operation ID 命名清晰 (`operation_id="create_user"`)
  - 路由层保持简洁，业务逻辑在 Service 层

## 📋 开发规范

### 统一响应格式
```python
# 成功响应
{
  "success": true,
  "data": {},
  "message": "操作成功"
}

# 错误响应  
{
  "success": false,
  "error": "错误描述"
}
```

### 错误处理
- **错误码**: 遵循 FastAPI 惯例，使用标准 HTTP 状态码
- **异常类**: 继承 `BaseAPIException`，自动格式化错误响应
- **Service 异常**: 每个 Service 方法声明 `METHOD_EXCEPTIONS`

### 开发环境
- **Backend v1**: `source venv/bin/activate`
- **Backend v2**: `source v2env/bin/activate`  
- **代理**: 本地请求使用 `--noproxy` 参数
- **依赖**: 用到什么添加什么，避免过度设计

### 测试规范
- **框架**: pytest，包括单元测试和 API 测试
- **原则**: 不硬编码 ID，动态获取或创建基础数据
- **环境**: 测试前重置数据库状态
- **发现问题**: 及时与 user 交流讨论

### 代码质量约束
- **Model/Service/Schema 修改**: 如需修改，告知原因等待统一确认
- **不假设信息**: 不清楚的查看 1-2 个文件，找不到立即询问 user
- **查看现有组件**: 创建 base/shared 组件前，先查看已有实现，不重复造轮子
- **主动沟通**: 遇到问题主动交流，communication makes program better

## 📈 当前任务

- **Shared 模块**: 数据库、异常、通用 Schema、依赖注入
- **Auth 模块**: 用户注册、登录、权限认证
- **Admin 模块**: 邀请码管理、审计日志、系统管理
- **Course 模块**: 学期、课程管理功能
- **Storage 模块**: 文件、文件夹管理
- **Chat 模块**: 聊天、消息功能  
- **AI 模块**: RAG、AI 对话功能

## 🎯 核心原则

1. **严格遵循 FastAPI 实践**: 四层分离，良好的代码结构
2. **质量优先**: 慢工出细活，不急躁，每一步都做到最好
3. **不重复造轮子**: 查看已有的 base/shared 组件实现模式
4. **主动沟通**: 认为需要修改时主动告诉 user，遇到问题及时讨论
5. **遵循现有模式**: 按照已建立的架构和代码模式开发新功能