# ICU 校园LLM系统后端架构报告

## 项目概述

ICU（Intelligent Campus Utility）校园LLM系统是一个基于FastAPI框架构建的智能校园助手后端服务，旨在为校园学生提供基于大语言模型的智能问答和知识管理功能。系统当前版本为v1.9.10，采用现代化的微服务架构设计，集成了RAG（检索增强生成）技术、异步任务处理和完善的用户权限管理。

项目包含两个主要目录：`backend`（当前使用）和`backend_v2`（已废弃的重构版本）。本报告主要聚焦于正在运行的`backend`系统架构。

---

## 技术栈与核心依赖

### 主要框架
- **FastAPI 0.115.14**: 高性能异步Web框架，提供自动API文档生成和类型验证
- **SQLAlchemy**: ORM框架，用于数据库操作和模型管理
- **Celery 5.5.3**: 分布式异步任务队列，处理耗时的文件处理和定时清理任务
- **Redis**: 作为Celery的broker和结果后端，提供高性能消息队列

### AI与机器学习
- **OpenAI API**: 核心LLM服务提供商，支持多种模型（Star、StarPlus、StarCode）
- **LangChain 0.1.0**: RAG框架，实现知识检索增强生成功能
- **ChromaDB 0.4.18**: 向量数据库，用于文档嵌入和相似度检索
- **HuggingFace Hub**: 模型和嵌入向量生成

### 安全与认证
- **JWT (jose)**: 基于Token的无状态身份认证
- **Bcrypt**: 密码加密存储
- **Passlib**: 密码哈希处理库

### 文件处理
- **PyPDF**: PDF文档解析
- **Docx2txt**: Word文档提取
- **python-magic**: 文件类型检测

---

## 系统架构设计

### 1. 分层架构

系统采用经典的三层架构模式：

```
┌─────────────────────────────────────┐
│         API Layer (v1)              │  <- 路由处理、请求验证
├─────────────────────────────────────┤
│       Service Layer                 │  <- 业务逻辑、RAG服务
├─────────────────────────────────────┤
│       Model Layer                   │  <- 数据库模型、ORM
└─────────────────────────────────────┘
```

**API层** (`app/api/v1/`): 包含9个核心路由模块
- `auth.py`: 用户认证（注册、登录、邮箱验证）
- `chats.py`: 对话管理（创建、更新、删除对话）
- `messages.py`: 消息处理（发送消息、流式响应）
- `courses.py`: 课程管理
- `semesters.py`: 学期管理
- `files.py`: 文件上传与管理
- `folders.py`: 文件夹组织
- `admin.py`: 管理员功能
- `unified_files.py`: 统一文件处理接口

**服务层** (`app/services/`): 包含13个专业服务模块
- `ai_service.py`: AI调用核心服务
- `rag_service.py`: RAG检索增强生成（489行代码）
- `chat_service.py`: 对话管理业务逻辑
- `file_service.py`: 文件上传、去重、权限控制（315行）
- `auth_service.py`: 认证授权服务
- `email_service.py`: 邮件发送（Resend API）
- `local_file_storage.py`: 本地文件存储管理

**模型层** (`app/models/`): 包含17个数据库模型
- `user.py`: 用户模型（含余额、消费追踪）
- `chat.py`: 对话模型（支持通用对话和课程对话）
- `message.py`: 消息模型
- `course.py`: 课程模型
- `file.py`: 文件逻辑模型
- `physical_file.py`: 物理文件存储（支持文件去重）
- `document_chunk.py`: 文档分块（RAG向量化）
- `invite_code.py`: 邀请码系统

### 2. 核心功能模块

#### (1) 用户认证与权限管理

系统实现了完整的用户生命周期管理：

**注册流程**:
- 用户名和邮箱唯一性验证
- 邀请码验证机制（可配置开启/关闭）
- 邮箱域名白名单限制（可选）
- 邮箱验证码系统（通过Resend API发送）
- Bcrypt密码加密存储

**认证机制**:
- JWT Token认证，默认24小时有效期
- HTTPBearer安全方案，支持Bearer Token
- 自定义401未授权响应处理
- 用户余额和消费追踪系统

**权限控制**:
- 基于角色的访问控制（RBAC）：user、admin
- 课程所有权验证
- 文件访问权限检查
- 文件夹访问控制

#### (2) RAG智能问答系统

这是系统的核心创新功能，实现了知识增强的AI对话：

**文档处理流程**:
1. **文件上传**: 支持PDF、DOC、DOCX、TXT、MD格式
2. **文件去重**: 基于SHA256哈希的物理文件去重机制
3. **异步处理**: Celery任务队列处理文件RAG向量化
4. **文档分块**: RecursiveCharacterTextSplitter，chunk_size=1000，overlap=200
5. **向量化存储**: ChromaDB存储文档嵌入向量
6. **相似度检索**: 基于余弦相似度的top-k检索

**RAG查询流程**:
```python
用户提问 -> 向量化查询 -> ChromaDB相似度检索 
  -> 获取相关文档片段 -> 构建增强上下文 
  -> OpenAI API生成回答 -> 返回结果（含来源引用）
```

**智能特性**:
- 支持课程级别的知识隔离
- 多文件联合检索
- 来源追溯（返回文档片段ID和得分）
- 自动降级机制（OpenAI API失败时使用Mock Embeddings）

#### (3) 对话管理系统

**对话类型**:
- `general`: 通用对话（无课程绑定）
- `course`: 课程对话（绑定特定课程，启用RAG）

**AI模型配置**:
- `Star`: 基础模型
- `StarPlus`: 增强模型
- `StarCode`: 代码专用模型

**上下文模式**:
- `Economy`: 经济模式（少量历史消息）
- `Standard`: 标准模式（中等历史消息）
- `Premium`: 高级模式（更多历史消息）
- `Max`: 最大模式（完整历史消息）

**功能特性**:
- 流式响应支持（Server-Sent Events）
- 自定义系统提示词
- 搜索功能集成（可选）
- 消息统计（消息数、总消耗、总Token数）

#### (4) 文件存储与管理

**三层存储架构**:

```
逻辑层 (File) -> 物理层 (PhysicalFile) -> 磁盘存储
     ↓                  ↓                    ↓
  元数据引用        哈希去重             实际文件
```

**核心优势**:
- **自动去重**: 相同内容的文件只存储一份物理副本
- **引用计数**: PhysicalFile.reference_count追踪使用情况
- **级联删除**: 删除逻辑文件时自动处理引用计数
- **存储优化**: 大幅减少存储空间占用

**文件处理**:
- 流式上传，避免大文件内存溢出
- SHA256哈希校验
- 文件类型自动检测
- 支持临时文件（5小时过期）

#### (5) 异步任务系统

**Celery任务队列**:

系统使用Redis作为消息broker，配置了两个专用队列：

1. **file_processing队列** (`app/tasks/file_processing.py`):
   - `process_file_rag_task`: 异步处理文件RAG向量化
   - 任务进度追踪（10% -> 30% -> 80% -> 100%）
   - 失败重试机制（最多3次，延迟60秒）
   - 处理状态实时更新

2. **cleanup队列** (`app/tasks/cleanup_tasks.py`):
   - `cleanup_expired_temporary_files`: 定时清理过期临时文件
   - 每小时运行一次（通过Celery Beat调度）
   - 自动删除磁盘文件和数据库记录
   - 物理文件引用计数管理

**配置特性**:
- 任务序列化：JSON格式
- 时区：Asia/Shanghai
- Worker配置：prefetch_multiplier=1，max_tasks_per_child=1000
- 结果过期：1小时后自动删除

---

## 安全与性能优化

### 1. 安全措施

**速率限制**: 
- 简单的内存速率限制器
- 每IP每分钟最多100个请求
- 超限返回429状态码

**请求超时**:
- 全局74秒超时控制
- 防止长时间请求占用资源
- 超时返回504 Gateway Timeout

**数据库安全**:
- `with_for_update()`行级锁，防止并发竞态
- SQL注入防护（ORM自动处理）
- 密码哈希存储（Bcrypt）

**CORS配置**:
- 可配置的跨域白名单
- 支持通配符`*`（开发环境）
- 生产环境建议限制具体域名

### 2. 性能优化

**数据库优化**:
- `joinedload`预加载关联数据，减少N+1查询
- 索引优化（user_id、course_id、folder_id等）
- 连接池管理

**文件处理优化**:
- 流式文件读取，避免大文件内存溢出
- 异步任务处理，不阻塞主线程
- 物理文件去重，节省存储空间

**日志管理**:
- 分级日志（INFO、WARNING、ERROR）
- 同时输出到控制台和文件
- SQLAlchemy日志降级（WARNING），减少噪音

---

## 配置管理

系统使用Pydantic Settings进行环境配置管理（`app/core/config.py`）：

**核心配置项**:
- `DATABASE_URL`: 数据库连接（支持SQLite和MySQL）
- `SECRET_KEY`: JWT签名密钥
- `OPENAI_API_KEY`: OpenAI API密钥
- `REDIS_URL`: Redis连接地址
- `UPLOAD_DIR`: 文件上传目录
- `MAX_FILE_SIZE`: 最大文件大小（默认10MB）
- `TEMPORARY_FILE_EXPIRY_HOURS`: 临时文件过期时间（默认5小时）

**特色配置**:
- `registration_invite_code_verification`: 是否启用邀请码
- `email_domain_restriction`: 邮箱域名白名单
- `allowed_extensions`: 允许的文件扩展名
- `rag_chunk_size`: RAG文档分块大小

---

## 中间件与异常处理

**中间件栈**（按执行顺序）:
1. **CORS中间件**: 处理跨域请求
2. **速率限制中间件**: IP级别请求限流
3. **超时中间件**: 74秒请求超时控制
4. **日志中间件**: 记录请求响应信息

**全局异常处理**:
- 统一的错误响应格式（ErrorResponse schema）
- HTTPException自动转换为标准JSON格式
- 包含错误代码和本地化消息

---

## Backend_v2 对比说明

项目中存在`backend_v2`目录，这是一次架构重构尝试，但目前已废弃。主要区别：

- 使用Alembic进行数据库迁移管理
- 更细粒度的模块划分（admin、ai、auth、chat、course、storage等独立模块）
- 包含pytest测试套件和覆盖率报告
- 有独立的虚拟环境（v2env）

废弃原因可能是：重构成本过高、业务迁移风险、当前`backend`系统已经足够稳定。

---

## 系统优势与特色

1. **RAG技术集成**: 将静态文档转化为可检索的知识库，显著提升AI回答准确性
2. **文件去重机制**: 智能的物理文件管理，节省存储成本
3. **异步任务处理**: Celery任务队列，确保用户界面响应流畅
4. **流式响应**: Server-Sent Events实现实时AI回答流式输出
5. **完善的权限控制**: 课程级别的数据隔离和访问控制
6. **灵活的配置管理**: 基于环境变量的12-factor app设计
7. **自动降级策略**: OpenAI API失败时自动使用Mock服务，保证系统可用性

---

## 潜在改进方向

1. **监控与可观测性**: 集成Prometheus、Grafana进行性能监控
2. **缓存优化**: 引入Redis缓存热点数据（用户信息、课程列表）
3. **向量数据库升级**: 考虑使用Milvus或Pinecone替代ChromaDB，支持更大规模
4. **API版本管理**: 目前只有v1，未来可能需要v2 API并行运行
5. **国际化支持**: 完善多语言错误消息和系统提示
6. **WebSocket支持**: 实现更高效的实时通信
7. **容器化部署**: 编写Dockerfile和docker-compose.yml

---

## 总结

ICU校园LLM系统后端是一个设计精良、功能完整的现代化Web服务。它成功地将大语言模型能力、RAG技术和传统Web开发最佳实践相结合，为校园场景提供了智能化的知识管理和问答解决方案。系统架构清晰、代码组织合理、安全性考虑周全，具备良好的可维护性和扩展性。通过异步任务处理、文件去重、智能缓存等优化手段，系统在性能和资源利用方面也表现出色。这是一个值得参考的AI应用开发范例。

---

**报告生成日期**: 2025年11月23日  
**系统版本**: v1.9.10  
**代码行数**: 约15,000+ 行（不含依赖库）  
**核心模块数**: 50+ 个Python模块
