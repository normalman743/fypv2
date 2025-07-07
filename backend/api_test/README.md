# 🧪 API测试套件

这是一个完整的API测试套件，用于测试校园LLM系统的各项功能。

## 📁 文件结构

```
api_test/
├── config.py              # 测试配置文件
├── utils.py               # 工具函数和API客户端
├── test_basic.py          # 基础API测试
├── test_auth.py           # 认证API测试
├── test_courses.py        # 课程管理API测试
├── test_files.py          # 文件管理API测试
├── test_chats.py          # 聊天API测试
├── test_admin.py          # 管理员API测试
├── run_all_tests.py       # 运行所有测试
└── README.md              # 说明文档
```

## 🚀 快速开始

### 安装依赖

```bash
pip install requests
```

### 配置测试

编辑 `config.py` 文件，确保以下配置正确：

- `BASE_URL`: API服务器地址
- `TEST_USER`: 测试用户信息（包括有效的邀请码）
- `ADMIN_USER`: 管理员账号信息

### 运行测试

#### 运行所有测试
```bash
cd api_test
python run_all_tests.py
```

#### 运行单个测试
```bash
# 基础API测试
python test_basic.py

# 认证API测试  
python test_auth.py

# 课程管理API测试
python test_courses.py

# 文件管理API测试
python test_files.py

# 聊天API测试
python test_chats.py

# 管理员API测试
python test_admin.py
```

## 📋 测试覆盖范围

### 🔧 基础API测试 (test_basic.py)
- ✅ 健康检查 `/health`
- ✅ 根路径 `/`
- ✅ API文档 `/docs`
- ✅ OpenAPI规范 `/openapi.json`

### 🔐 认证API测试 (test_auth.py)
- 👤 用户注册 `POST /api/v1/auth/register`
- 🔑 用户登录 `POST /api/v1/auth/login`
- 👤 获取用户信息 `GET /api/v1/auth/me`
- ✏️ 更新用户信息 `PUT /api/v1/auth/me`
- 🚪 用户登出 `POST /api/v1/auth/logout`
- ❌ 未授权访问测试

### 📚 课程管理API测试 (test_courses.py)
- 📅 获取学期列表 `GET /api/v1/semesters`
- ➕ 创建学期 `POST /api/v1/semesters`
- 📚 获取课程列表 `GET /api/v1/courses`
- ➕ 创建课程 `POST /api/v1/courses`
- ✏️ 更新课程 `PUT /api/v1/courses/{id}`
- 📁 获取课程文件夹 `GET /api/v1/courses/{id}/folders`
- ➕ 创建文件夹 `POST /api/v1/courses/{id}/folders`
- 🗑️ 删除文件夹 `DELETE /api/v1/folders/{id}`

### 📁 文件管理API测试 (test_files.py)
- ⬆️ 文件上传 `POST /api/v1/files/upload`
- 📄 获取文件列表 `GET /api/v1/folders/{id}/files`
- 👁️ 文件预览 `GET /api/v1/files/{id}/preview`
- 📊 文件状态 `GET /api/v1/files/{id}/status`
- ⬇️ 文件下载 `GET /api/v1/files/{id}/download`
- 🗑️ 删除文件 `DELETE /api/v1/files/{id}`

### 💬 聊天API测试 (test_chats.py)
- 📝 获取聊天列表 `GET /api/v1/chats`
- ➕ 创建通用聊天 `POST /api/v1/chats`
- ➕ 创建课程聊天 `POST /api/v1/chats`
- 💭 获取聊天消息 `GET /api/v1/chats/{id}/messages`
- 📤 发送消息 `POST /api/v1/chats/{id}/messages`
- 📎 发送带文件的消息
- ✏️ 编辑消息 `PUT /api/v1/messages/{id}`
- ✏️ 更新聊天标题 `PUT /api/v1/chats/{id}`
- 🗑️ 删除消息 `DELETE /api/v1/messages/{id}`
- 🗑️ 删除聊天 `DELETE /api/v1/chats/{id}`

### 👑 管理员API测试 (test_admin.py)
- 🎫 获取邀请码列表 `GET /api/v1/invite-codes`
- ➕ 创建邀请码 `POST /api/v1/invite-codes`
- ✏️ 更新邀请码 `PUT /api/v1/invite-codes/{id}`
- 🗑️ 删除邀请码 `DELETE /api/v1/invite-codes/{id}`
- ⚙️ 获取系统配置 `GET /api/v1/system/config`
- ✏️ 更新系统配置 `PUT /api/v1/system/config`
- 📋 获取审计日志 `GET /api/v1/audit-logs`

## 🔧 配置说明

### API地址配置
```python
BASE_URL = "https://api-icu.584743.xyz"
```

### 测试用户配置
```python
TEST_USER = {
    "username": "api_test_user",
    "email": "api_test@example.com", 
    "password": "testpass123",
    "invite_code": "INVITE2025"  # 需要有效的邀请码
}
```

### 管理员配置
```python
ADMIN_USER = {
    "username": "admin",
    "password": "admin123"
}
```

## 📊 测试结果解读

### 成功标志
- ✅ 绿色对勾 - 测试通过
- 📈 显示通过的测试数量

### 失败标志  
- ❌ 红色叉号 - 测试失败
- 💥 爆炸符号 - 运行异常
- ⚠️ 警告 - 部分功能不可用

### 特殊情况
- 🔐 认证失败 - 可能是邀请码或用户凭据问题
- 👑 管理员权限 - 某些测试需要管理员权限
- 📁 数据依赖 - 某些测试需要预先存在的数据

## 🛠️ 故障排除

### 常见问题

1. **认证失败**
   - 检查邀请码是否有效
   - 确认用户名密码正确
   - 验证API服务器状态

2. **权限不足**
   - 确认管理员账号配置
   - 检查用户角色权限

3. **网络问题**
   - 检查API服务器是否可访问
   - 确认防火墙设置
   - 验证SSL证书

4. **数据依赖**
   - 确保测试数据库已初始化
   - 检查必要的种子数据

### 调试技巧

1. **查看详细响应**
   - 测试脚本会打印完整的HTTP响应
   - 检查状态码和错误信息

2. **单独运行测试**
   - 先运行基础测试确保API可访问
   - 逐个运行测试模块定位问题

3. **检查API文档**
   - 访问 `/docs` 查看API文档
   - 对比请求格式和参数

## 🚀 扩展测试

### 添加新测试

1. 创建新的测试文件
2. 导入 `utils.py` 中的工具函数
3. 实现测试函数
4. 在 `run_all_tests.py` 中添加测试模块

### 自定义配置

- 修改 `config.py` 适应不同环境
- 调整超时时间和重试策略
- 添加环境变量支持

## 📞 技术支持

如果遇到问题，请检查：
1. API服务器状态
2. 测试配置是否正确
3. 数据库是否已初始化
4. 网络连接是否正常

测试愉快！🎉