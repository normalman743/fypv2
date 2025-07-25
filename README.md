# 🏫 校园LLM系统 (Campus LLM System)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.14-green.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个基于RAG的智能校园助手系统，为大学生提供统一的学术支持和校园生活信息服务。系统集成了文档处理、向量搜索和对话AI功能。

## 📋 目录

- [🏗️ 系统架构](#️-系统架构)
- [✨ 核心特性](#-核心特性)
- [🚀 快速开始](#-快速开始)
- [📁 项目结构](#-项目结构)
- [🔧 配置说明](#-配置说明)
- [📚 API文档](#-api文档)
- [🧪 测试](#-测试)
- [📊 数据库设计](#-数据库设计)
- [🔍 代码审查](#-代码审查)
- [🚧 已知问题](#-已知问题)
- [📖 开发指南](#-开发指南)
- [📞 技术支持](#-技术支持)

## 🏗️ 系统架构

### 后端架构 (FastAPI)
- **框架**: FastAPI with async support
- **数据库**: MySQL + Chroma 向量数据库
- **AI/RAG**: LangChain + OpenAI integration
- **任务队列**: Celery with Redis
- **文件存储**: 本地文件系统 + SHA256去重

### 核心组件
- **Models** (`app/models/`): SQLAlchemy ORM 数据模型
- **API Routes** (`app/api/v1/`): RESTful API 端点
- **Services** (`app/services/`): 业务逻辑层
- **Schemas** (`app/schemas/`): Pydantic 数据验证模型
- **Tasks** (`app/tasks/`): 异步文件处理任务

## ✨ 核心特性

### 🤖 智能AI对话
- **RAG检索增强**: 基于课程文档的智能问答
- **流式响应**: 实时AI对话体验
- **自动标题生成**: 基于首条消息智能生成聊天标题
- **多模型支持**: 支持不同AI模型切换

### 📁 文件管理系统
- **智能去重**: SHA256哈希实现物理文件去重
- **多格式支持**: PDF, DOC, DOCX, TXT, MD等
- **文件分享**: 支持课程内文件共享
- **临时文件**: 支持临时文件上传和自动清理

### 👥 用户与权限管理
- **邀请码注册**: 基于邀请码的用户注册系统
- **角色权限**: 管理员和普通用户权限区分
- **邮箱验证**: 可选的邮箱验证功能

### 📚 学术管理
- **学期管理**: 支持多学期数据管理
- **课程组织**: 课程文件夹结构化管理
- **文档处理**: 自动提取和向量化文档内容

## 🚀 快速开始

### 环境要求
- Python 3.7+
- MySQL 8.0+
- Redis 6.0+
- 10GB+ 可用磁盘空间

### 1. 克隆项目
```bash
git clone https://github.com/normalman743/fypv2.git
cd fypv2
```

### 2. 设置后端环境
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 环境配置
创建 `.env` 文件并配置以下参数：

```env
# 数据库配置
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/campus_llm_db

# JWT配置
SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Redis配置
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AI配置
OPENAI_API_KEY=your-openai-api-key
CHROMA_DATA_DIR=./data/chroma

# 文件存储配置
UPLOAD_DIR=./storage/uploads
MAX_FILE_SIZE=52428800  # 50MB

# 邮件配置 (可选)
RESEND_API_KEY=your-resend-api-key
EMAIL_ADDRESS=no-reply@yourdomain.com
```

### 4. 数据库初始化
```bash
# 确保MySQL服务运行
# 创建数据库: CREATE DATABASE campus_llm_db;

# 初始化测试数据
cd api_test_v3
python reset_system.py
```

### 5. 启动服务
```bash
cd backend
source venv/bin/activate

# 启动主服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动Celery (新终端)
celery -A app.celery_app worker --loglevel=info
```

### 6. 验证安装
访问 http://localhost:8000/docs 查看API文档

默认测试账户：
- 管理员: `admin` / `admin123456`
- 普通用户: `user` / `user123456`

## 📁 项目结构

```
fypv2/
├── README.md                           # 项目说明文档
├── CLAUDE.md                          # Claude开发指南
├── campus_llm_database_analysis.md    # 数据库结构分析
├── api_*.md                           # API文档集合
│
├── backend/                           # 后端主目录
│   ├── requirements.txt               # Python依赖
│   ├── app/                          # 应用核心代码
│   │   ├── main.py                   # FastAPI应用入口
│   │   ├── config.py                 # 应用配置
│   │   ├── dependencies.py           # 依赖注入
│   │   ├── celery_app.py             # Celery配置
│   │   │
│   │   ├── api/v1/                   # API路由层
│   │   │   ├── auth.py               # 认证相关API
│   │   │   ├── semesters.py          # 学期管理API
│   │   │   ├── courses.py            # 课程管理API
│   │   │   ├── folders.py            # 文件夹API
│   │   │   ├── files.py              # 文件管理API
│   │   │   ├── unified_files.py      # 统一文件API
│   │   │   ├── chats.py              # 聊天管理API
│   │   │   ├── messages.py           # 消息API
│   │   │   └── admin.py              # 管理员API
│   │   │
│   │   ├── core/                     # 核心配置
│   │   │   ├── config.py             # 配置管理
│   │   │   ├── security.py           # 安全相关
│   │   │   ├── exceptions.py         # 异常处理
│   │   │   └── model_config.py       # 模型配置
│   │   │
│   │   ├── models/                   # 数据模型 (SQLAlchemy)
│   │   │   ├── database.py           # 数据库连接
│   │   │   ├── user.py               # 用户模型
│   │   │   ├── semester.py           # 学期模型
│   │   │   ├── course.py             # 课程模型
│   │   │   ├── folder.py             # 文件夹模型
│   │   │   ├── file.py               # 文件模型
│   │   │   ├── physical_file.py      # 物理文件模型
│   │   │   ├── chat.py               # 聊天模型
│   │   │   ├── message.py            # 消息模型
│   │   │   ├── document_chunk.py     # 文档块模型
│   │   │   └── ...                   # 其他模型
│   │   │
│   │   ├── schemas/                  # Pydantic数据模式
│   │   │   ├── user.py               # 用户数据模式
│   │   │   ├── semester.py           # 学期数据模式
│   │   │   ├── course.py             # 课程数据模式
│   │   │   ├── file.py               # 文件数据模式
│   │   │   ├── chat.py               # 聊天数据模式
│   │   │   ├── message.py            # 消息数据模式
│   │   │   └── ...                   # 其他模式
│   │   │
│   │   ├── services/                 # 业务逻辑层
│   │   │   ├── auth_service.py       # 认证服务
│   │   │   ├── semester_service.py   # 学期服务
│   │   │   ├── course_service.py     # 课程服务
│   │   │   ├── folder_service.py     # 文件夹服务
│   │   │   ├── file_service.py       # 文件服务
│   │   │   ├── unified_file_service.py # 统一文件服务
│   │   │   ├── chat_service.py       # 聊天服务
│   │   │   ├── message_service.py    # 消息服务
│   │   │   ├── ai_service.py         # AI服务
│   │   │   ├── rag_service.py        # RAG检索服务
│   │   │   └── ...                   # 其他服务
│   │   │
│   │   ├── tasks/                    # Celery异步任务
│   │   │   ├── file_processing.py    # 文件处理任务
│   │   │   └── cleanup_tasks.py      # 清理任务
│   │   │
│   │   └── utils/                    # 工具函数
│   │       ├── file_processing_utils.py # 文件处理工具
│   │       ├── file_validation.py    # 文件验证
│   │       └── image_utils.py        # 图像处理工具
│   │
│   └── api_test_v3/                  # 测试套件
│       ├── README.md                 # 测试说明
│       ├── config.py                 # 测试配置
│       ├── utils.py                  # 测试工具
│       ├── database.py               # 数据库测试工具
│       ├── reset_system.py           # 系统重置工具
│       └── test_*.py                 # 各模块测试文件
│
└── email_workers/                    # 邮件处理模块
    └── email_processor.py            # 邮件处理器
```

## 🔧 配置说明

### 核心配置参数

| 参数 | 说明 | 默认值 | 必填 |
|------|------|--------|------|
| `DATABASE_URL` | MySQL数据库连接字符串 | `sqlite:///./local_campus_llm.db` | ✅ |
| `SECRET_KEY` | JWT密钥 | `your-secret-key-here-change-in-production` | ✅ |
| `OPENAI_API_KEY` | OpenAI API密钥 | - | ✅ |
| `REDIS_URL` | Redis连接字符串 | `redis://localhost:6379/0` | ✅ |
| `UPLOAD_DIR` | 文件上传目录 | `./storage/uploads` | ❌ |
| `MAX_FILE_SIZE` | 最大文件大小(字节) | `52428800` (50MB) | ❌ |
| `CHROMA_DATA_DIR` | 向量库数据目录 | `./data/chroma` | ❌ |

### 邮件配置 (可选)
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `RESEND_API_KEY` | Resend邮件服务API密钥 | - |
| `EMAIL_ADDRESS` | 发件人邮箱地址 | `no-reply@icu.584743.xyz` |
| `EMAIL_DOMAIN_RESTRICTION` | 允许注册的邮箱域名(逗号分隔) | - |

### RAG配置
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `RAG_CHUNK_SIZE` | 文档分块大小 | `1000` |
| `RAG_CHUNK_OVERLAP` | 分块重叠大小 | `200` |

## 📚 API文档

系统提供完整的RESTful API，所有API都使用统一的JSON响应格式。

### API模块组织

1. **[认证与用户管理 API](api_auth.md)**
   - 用户注册、登录、个人资料管理
   - JWT token管理

2. **[学期与课程管理 API](api_semester_course.md)**
   - 学期创建与管理
   - 课程创建与管理

3. **[文件夹与文件管理 API](api_folder_file.md)**
   - 文件夹操作
   - 文件上传、下载、删除
   - 文件共享管理

4. **[聊天、消息与AI功能 API](api_chat_message_rag.md)**
   - 聊天会话管理
   - 消息发送与检索
   - AI对话与RAG检索

5. **[系统管理 API](api_admin.md)**
   - 用户管理
   - 系统配置
   - 统计信息

### 在线API文档
启动服务后访问以下地址查看交互式API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

### 认证方式
除了登录和注册API，所有API都需要在请求头中包含JWT token：
```
Authorization: Bearer {your_jwt_token}
```

## 🧪 测试

### 测试套件结构
项目使用 `api_test_v3` 测试套件，提供模块化的API测试工具。

### 运行测试

#### 1. 系统重置 (测试前必须)
```bash
cd backend/api_test_v3
python reset_system.py
```

#### 2. 运行特定模块测试
```bash
# 认证和用户管理测试
python -m pytest test_auth_user.py -v

# 学期和课程管理测试
python -m pytest test_semester_course.py -v
python -m pytest test_course_folders.py -v

# 文件管理测试
python -m pytest test_file_upload.py -v
python -m pytest test_file_upload_comprehensive.py -v

# 聊天和消息测试
python -m pytest test_chat_message.py -v

# 管理员功能测试
python -m pytest test_admin_functions.py -v

# 删除操作测试
python -m pytest test_delete_operations.py -v
```

#### 3. 运行所有测试
```bash
python -m pytest -v
```

### 测试覆盖范围

| 测试模块 | 覆盖功能 | 状态 |
|----------|----------|------|
| `test_auth_user.py` | 用户注册、登录、资料管理 | ✅ 完成 |
| `test_semester_course.py` | 学期和课程管理 | ✅ 完成 |
| `test_course_folders.py` | 课程文件夹管理 | ✅ 完成 |
| `test_file_upload.py` | 文件上传下载 | ⚠️ 部分API未实现 |
| `test_chat_message.py` | 聊天和消息功能 | ⏳ 待测试 |
| `test_admin_functions.py` | 管理员功能 | ⏳ 待测试 |
| `test_delete_operations.py` | 删除操作 | ⏳ 待测试 |

### 测试配置
测试使用独立的配置文件 `api_test_v3/config.py`，默认配置：
- API服务地址: `http://localhost:8000`
- 测试用户: admin/user
- 数据库: 使用生产数据库(重置后)

## 📊 数据库设计

### 数据库概览
- **数据库名**: campus_llm_db
- **引擎**: MySQL 8.0+
- **表数量**: 20+ 张表
- **主要特性**: 外键约束、索引优化、审计日志

### 核心表结构

#### 用户相关
- `users`: 用户基本信息
- `invite_codes`: 邀请码管理
- `audit_logs`: 操作审计日志

#### 学术结构
- `semesters`: 学期信息
- `courses`: 课程信息
- `folders`: 文件夹结构

#### 文件系统
- `physical_files`: 物理文件(去重)
- `files`: 文件元数据
- `document_chunks`: 文档向量块

#### 聊天系统
- `chats`: 聊天会话
- `messages`: 消息记录
- `message_file_references`: 消息文件关联

#### 权限系统
- `permissions`: 权限配置
- `file_shares`: 文件共享
- `roles`: 角色定义

### 详细数据库分析
参考 [数据库结构分析文档](campus_llm_database_analysis.md) 了解完整的表结构、关系和索引设计。

## 🔍 代码审查

### 代码审查分组建议

#### 第一组：核心架构层 (高优先级)
**审查重点**: 架构设计、安全性、性能
```
app/main.py                 # 应用入口和中间件配置
app/core/                   # 核心配置和安全模块
app/dependencies.py         # 依赖注入
app/models/database.py      # 数据库连接和配置
```

#### 第二组：数据模型层 (高优先级)
**审查重点**: 数据完整性、关系设计、索引优化
```
app/models/                 # 所有SQLAlchemy模型
app/schemas/                # 所有Pydantic模式
```

#### 第三组：API接口层 (中优先级)
**审查重点**: API设计、输入验证、错误处理
```
app/api/v1/auth.py         # 认证API
app/api/v1/admin.py        # 管理API
app/api/v1/files.py        # 文件API
app/api/v1/unified_files.py # 统一文件API
```

#### 第四组：业务逻辑层 (中优先级)
**审查重点**: 业务逻辑正确性、异常处理
```
app/services/auth_service.py      # 认证服务
app/services/unified_file_service.py # 统一文件服务
app/services/ai_service.py        # AI服务
app/services/rag_service.py       # RAG服务
```

#### 第五组：工具和任务层 (低优先级)
**审查重点**: 代码质量、工具函数正确性
```
app/tasks/                  # Celery任务
app/utils/                  # 工具函数
email_workers/             # 邮件处理
```

### 代码审查流程建议

1. **预审查准备**
   - 阅读相关API文档 (`api_*.md`)
   - 查看数据库设计文档
   - 了解已知问题 (`CODE_REVIEW_ISSUES.md`)

2. **审查步骤**
   - 架构合理性检查
   - 安全性漏洞扫描
   - 性能瓶颈识别
   - 代码质量评估
   - 测试覆盖度检查

3. **工具推荐**
   - 静态代码分析: `pylint`, `black`, `mypy`
   - 安全扫描: `bandit`
   - 测试覆盖: `pytest-cov`

## 🚧 已知问题

根据 `CODE_REVIEW_ISSUES.md` 分析，当前系统存在以下需要关注的问题：

### 🚨 高优先级问题

1. **API端点服务不一致**
   - 临时文件上传使用 `UnifiedFileService`
   - 下载和删除使用 `TemporaryFileService`
   - **影响**: 可能导致文件路径不匹配

2. **路径生成不一致**
   - 不同服务生成的文件路径格式不统一
   - **影响**: 文件下载失败、去重机制失效

3. **物理文件引用计数管理不统一**
   - 多套引用计数逻辑可能不同步
   - **影响**: 文件误删或无法删除

### 🔶 中优先级问题

4. **代码重复导入** - `hashlib` 在 `unified_file_service.py` 中重复导入
5. **错误处理不一致** - 不同模块使用不同的错误处理方式
6. **文件类型检测简单** - 缺少恶意文件检测

### 🔷 低优先级问题

7. **代码注释不完整** - 部分方法缺少详细注释
8. **日志记录不统一** - 混用 `print` 和 `logger`

### 修复建议

**立即修复** (高优先级):
1. 统一临时文件服务到 `UnifiedFileService`
2. 修复路径生成逻辑
3. 统一引用计数管理

**后续优化** (中低优先级):
1. 清理重复导入
2. 统一错误处理机制
3. 改进文件类型检测
4. 完善日志记录

## 📖 开发指南

### 开发环境设置

1. **Python环境**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **开发工具配置**
   ```bash
   # 代码格式化
   pip install black isort

   # 静态检查
   pip install pylint mypy

   # 安全检查
   pip install bandit
   ```

### 开发规范

#### API开发标准流程

1. **API文档设计**: 编写详细的 `api_*.md` 文档，定义接口规范
2. **API实现对齐**: 确保实际API实现与文档规范完全对齐
3. **系统化测试**: 使用 `api_test_v3` 进行全面测试验证

#### 三方对齐原则

⚠️ **重要**: 以下三方必须保持一致
- **API文档** ↔ **真实API实现** ↔ **数据库结构**

#### 开发检查清单

- [ ] 查看现有API文档了解接口规范
- [ ] 检查 `/openapi.json` 确认当前API实现  
- [ ] 查看数据库分析文档确认表结构
- [ ] 对比三者找出不一致之处
- [ ] 优先以数据库结构为准，更新API文档和实现

### 分支管理

- **main**: 生产分支
- **develop**: 开发主分支
- **feature/***: 功能开发分支
- **fix/***: 问题修复分支

⚠️ **注意**: 不要在main分支上直接开发，每次改bug或测试新功能使用新分支

### 数据库管理

```bash
# 数据库连接信息
# 参考 campus_llm_database_analysis.md

# 重置系统 (测试环境)
cd backend/api_test_v3
python reset_system.py
```

### 测试准则

- **测试健壮性原则**: 不要假设硬编码的ID，应动态获取或创建基础数据
- **环境隔离**: 使用 `reset_system.py` 重置测试环境
- **API对齐**: 编写测试前先查看API文档和实际实现

## 📞 技术支持

### 常见问题

**Q: 如何启动开发服务器？**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Q: 数据库连接失败怎么办？**
1. 检查MySQL服务是否运行
2. 验证 `DATABASE_URL` 配置
3. 确认数据库和用户权限

**Q: AI功能不工作？**
1. 检查 `OPENAI_API_KEY` 是否配置
2. 验证网络连接
3. 查看Celery worker日志

**Q: 文件上传失败？**
1. 检查 `UPLOAD_DIR` 目录权限
2. 验证文件大小限制
3. 查看文件格式是否支持

### 联系方式

- **项目仓库**: https://github.com/normalman743/fypv2
- **问题反馈**: 创建 GitHub Issue
- **开发团队**: normalman743

### 贡献指南

1. Fork 项目仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

**🎯 Version**: 1.9.10  
**📅 最后更新**: 2025-07-25  
**👨‍💻 维护者**: Campus LLM Development Team