# 校园LLM系统 API 实现计划

## 🎯 实现原则
1. **依赖优先** - 先实现被其他模块依赖的基础功能
2. **复杂度递增** - 从简单到复杂，逐步构建
3. **功能完整** - 每个模块实现完整后再进入下一个
4. **测试驱动** - 每个API都要有对应的测试

## 📋 实现次序

### 第一阶段：基础架构 (1-2天)
**目标：搭建项目基础框架**

1. **项目初始化**
   - [ ] 创建FastAPI应用结构
   - [ ] 配置数据库连接
   - [ ] 设置环境变量
   - [ ] 创建基础依赖注入

2. **数据库模型**
   - [ ] 用户模型 (User)
   - [ ] 学期模型 (Semester)
   - [ ] 课程模型 (Course)
   - [ ] 基础迁移文件

### 第二阶段：认证系统 (2-3天)
**目标：实现用户认证和授权**

1. **认证API** - `api_auth.md`
   - [ ] POST `/api/v1/auth/register` - 用户注册
   - [ ] POST `/api/v1/auth/login` - 用户登录
   - [ ] GET `/api/v1/auth/me` - 获取用户信息
   - [ ] PUT `/api/v1/auth/me` - 更新用户信息
   - [ ] POST `/api/v1/auth/logout` - 用户登出

2. **认证中间件**
   - [ ] JWT token验证
   - [ ] 用户权限检查
   - [ ] 邀请码验证

### 第三阶段：学期课程管理 (2-3天)
**目标：实现学期和课程的基础管理**

1. **学期管理** - `api_semester_course.md`
   - [ ] GET `/api/v1/semesters` - 获取学期列表
   - [ ] POST `/api/v1/semesters` - 创建学期 (admin)
   - [ ] PUT `/api/v1/semesters/{id}` - 更新学期 (admin)
   - [ ] DELETE `/api/v1/semesters/{id}` - 删除学期 (admin)

2. **课程管理**
   - [ ] GET `/api/v1/courses` - 获取课程列表
   - [ ] POST `/api/v1/courses` - 创建课程
   - [ ] PUT `/api/v1/courses/{id}` - 更新课程
   - [ ] DELETE `/api/v1/courses/{id}` - 删除课程

### 第四阶段：文件管理 (3-4天)
**目标：实现文件和文件夹管理**

1. **文件夹管理** - `api_folder_file.md`
   - [ ] GET `/api/v1/folders` - 获取文件夹列表
   - [ ] POST `/api/v1/folders` - 创建文件夹
   - [ ] PUT `/api/v1/folders/{id}` - 更新文件夹
   - [ ] DELETE `/api/v1/folders/{id}` - 删除文件夹

2. **文件管理**
   - [ ] POST `/api/v1/files/upload` - 文件上传
   - [ ] GET `/api/v1/files` - 获取文件列表
   - [ ] GET `/api/v1/files/{id}` - 获取文件详情
   - [ ] DELETE `/api/v1/files/{id}` - 删除文件

3. **文件处理服务**
   - [ ] 文件去重 (SHA256)
   - [ ] 文件格式验证
   - [ ] 文件存储管理

### 第五阶段：聊天和消息 (4-5天)
**目标：实现聊天和消息功能**

1. **聊天管理** - `api_chat_message_rag.md`
   - [ ] GET `/api/v1/chats` - 获取聊天列表
   - [ ] POST `/api/v1/chats` - 创建聊天
   - [ ] GET `/api/v1/chats/{id}` - 获取聊天详情
   - [ ] DELETE `/api/v1/chats/{id}` - 删除聊天

2. **消息管理**
   - [ ] GET `/api/v1/chats/{id}/messages` - 获取消息列表
   - [ ] POST `/api/v1/chats/{id}/messages` - 发送消息
   - [ ] 消息历史记录

### 第六阶段：AI和RAG功能 (5-7天)
**目标：实现AI对话和RAG检索**

1. **RAG服务**
   - [ ] 文档向量化
   - [ ] 向量数据库集成 (Chroma)
   - [ ] 相似度检索

2. **AI对话**
   - [ ] POST `/api/v1/chats/{id}/ai-message` - AI回复
   - [ ] 流式响应支持
   - [ ] 聊天标题自动生成

3. **知识库管理**
   - [ ] 课程知识库
   - [ ] 全局知识库
   - [ ] 检索策略

### 第七阶段：系统管理 (2-3天)
**目标：实现管理员功能**

1. **管理员API** - `api_admin.md`
   - [ ] 用户管理
   - [ ] 系统统计
   - [ ] 邀请码管理

### 第八阶段：优化和测试 (3-4天)
**目标：系统优化和完整测试**

1. **性能优化**
   - [ ] 数据库索引优化
   - [ ] 缓存策略
   - [ ] 异步处理

2. **完整测试**
   - [ ] 单元测试覆盖
   - [ ] 集成测试
   - [ ] 端到端测试

## 🚀 快速开始

### 第一步：环境准备
```bash
# 1. 检查当前项目结构
ls -la

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 3. 安装基础依赖
pip install fastapi uvicorn sqlalchemy pymysql pydantic python-jose[cryptography] passlib[bcrypt] python-multipart
```

### 第二步：开始第一阶段
```bash
# 1. 创建基础应用结构
mkdir -p app/{api/v1,models,schemas,services,core}

# 2. 创建主应用文件
touch app/__init__.py app/main.py app/config.py app/dependencies.py

# 3. 创建数据库模型
touch app/models/__init__.py app/models/database.py app/models/user.py
```

## 📊 进度跟踪

| 阶段 | 状态 | 预计时间 | 实际时间 | 完成度 |
|------|------|----------|----------|--------|
| 第一阶段 | 🔄 进行中 | 1-2天 | - | 0% |
| 第二阶段 | ⏳ 待开始 | 2-3天 | - | 0% |
| 第三阶段 | ⏳ 待开始 | 2-3天 | - | 0% |
| 第四阶段 | ⏳ 待开始 | 3-4天 | - | 0% |
| 第五阶段 | ⏳ 待开始 | 4-5天 | - | 0% |
| 第六阶段 | ⏳ 待开始 | 5-7天 | - | 0% |
| 第七阶段 | ⏳ 待开始 | 2-3天 | - | 0% |
| 第八阶段 | ⏳ 待开始 | 3-4天 | - | 0% |

**总计预计时间：22-31天**

## 🎯 成功标准

每个阶段完成后，应该能够：
1. ✅ 所有API端点正常工作
2. ✅ 通过所有单元测试
3. ✅ 通过集成测试
4. ✅ 文档与代码同步
5. ✅ 性能满足要求

---

**下一步：开始第一阶段 - 基础架构搭建**

准备好开始了吗？我们可以从创建FastAPI应用的基础结构开始！ 