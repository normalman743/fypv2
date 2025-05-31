# 🎓 大学AI助手系统 - University AI Assistant

一个基于RAG（检索增强生成）技术的智能大学学习助手系统，支持多语言（简体中文、繁体中文、英语），为大学生提供个性化的校园生活和学习支持。

![项目状态](https://img.shields.io/badge/状态-开发中-green)
![前端](https://img.shields.io/badge/前端-React%2018%20%2B%20TypeScript-blue)
![后端](https://img.shields.io/badge/后端-Python%20%2B%20Flask-yellow)
![UI库](https://img.shields.io/badge/UI-Ant%20Design-orange)
https://test.cuhk-student.584743.xyz

## 🌟 系统特性

- 🤖 **智能对话**: 基于OpenAI的AI助手，支持学术问答和学习指导
- 📚 **文档上传**: 支持PDF、DOC、TXT等多种格式文件上传（最大10MB）
- 🌍 **多语言支持**: 简体中文、繁体中文、英语三语切换
- 👥 **用户管理**: 完整的用户注册、验证和权限管理系统
- 📊 **学习工具**: 自动生成练习题、创建学习计划
- 🔒 **安全可靠**: JWT认证、文件安全检查、防护机制
- 🎨 **现代UI**: Ant Design + Framer Motion 打造的流畅用户体验
- 📱 **响应式设计**: 完美适配桌面端和移动端设备
- ⚡ **高性能**: 组件化架构，代码分割，快速加载

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                 Frontend (React)                         │
│  ┌────────────┐  ┌────────────┐  ┌─────────────────┐  │
│  │  Auth UI   │  │  Chat UI   │  │  Admin Panel    │  │
│  │            │  │            │  │                 │  │
│  │ - Login    │  │ - Messages │  │ - Upload Docs   │  │
│  │ - Register │  │ - Upload   │  │ - Manage Users  │  │
│  │            │  │ - History  │  │ - Analytics     │  │
│  └────────────┘  └────────────┘  └─────────────────┘  │
└────────────────────────────┬────────────────────────────┘
                             │ HTTP/REST API
┌────────────────────────────▼────────────────────────────┐
│              Backend (Python Flask)                      │
│  ┌────────────┐  ┌────────────┐  ┌─────────────────┐  │
│  │Auth Routes │  │ Chat Routes│  │  Admin Routes   │  │
│  └────────────┘  └────────────┘  └─────────────────┘  │
│  ┌────────────────────────────────────────────────┐   │
│  │              Core Services                      │   │
│  │  - OpenAI Integration (with streaming)         │   │
│  │  - Document Processing & Embedding             │   │
│  │  - RAG (Retrieval Augmented Generation)       │   │
│  │  - File Upload Handler                        │   │
│  └────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────┘
                             │
     ▼                       ▼                       ▼
┌─────────┐          ┌─────────────┐         ┌─────────────┐
│  MySQL  │          │    Redis    │         │File Storage │
│         │          │   (Cache)   │         │  (Local)    │
└─────────┘          └─────────────┘         └─────────────┘
```

## 🛠️ 技术栈

### 前端
- **框架**: React 18 + TypeScript
- **UI库**: Ant Design 5.0
- **动画**: Framer Motion
- **样式**: CSS-in-JS + 全局CSS
- **状态管理**: React Context + Hooks
- **路由**: React Router v6
- **国际化**: react-i18next
- **HTTP客户端**: Axios
- **构建工具**: Create React App + TypeScript

### 后端
- **框架**: Python Flask
- **数据库**: MySQL 8.0
- **缓存**: Redis
- **AI服务**: OpenAI API
- **认证**: JWT (JSON Web Tokens)
- **文件处理**: Werkzeug
- **RAG技术**: 文档向量化 + 语义检索

### 开发工具
- **代码规范**: ESLint + Prettier
- **类型检查**: TypeScript
- **版本控制**: Git
- **包管理**: npm
- **API测试**: Postman

### 部署
- **Web服务器**: Nginx
- **进程管理**: systemd
- **容器化**: Docker (可选)

## 📋 主要功能

### 用户功能
1. **账户管理**
   - 邮箱注册和验证
   - 安全登录/登出
   - 多语言切换

2. **智能对话**
   - 实时AI问答
   - 对话历史管理
   - 流式响应显示

3. **文件管理**
   - 文档上传（PDF、DOC、TXT）
   - 文件安全检查
   - 基于文档的问答

4. **学习工具**
   - 自动生成练习题
   - 个性化学习计划
   - 学习进度跟踪

## 🎨 UI设计特色

### 设计系统
- **主色调**: 渐变色彩 (#667eea → #764ba2)
- **卡片设计**: 现代圆角卡片，柔和阴影效果
- **动画效果**: Framer Motion 提供丝滑交互体验
- **响应式**: 完美适配各种屏幕尺寸

### 核心组件
- **StatCard**: 统计数据展示卡片，支持趋势显示和图标
- **QuickActionCard**: 快速操作卡片，支持渐变背景和统计信息
- **PageHeader**: 专业页面头部，支持面包屗导航和操作按钮
- **ChatMessage**: 聊天气泡组件，支持用户和AI消息样式
- **SessionList**: 会话列表组件，支持删除和选择操作
- **LoadingSpinner**: 自定义加载动画组件

### 页面布局
1. **首页 (HomePage)**
   - 📊 数据统计概览
   - 🚀 快速操作入口
   - 📈 学习进度展示
   - 🔔 最近活动动态

2. **AI助手 (ChatPage)**
   - 💬 智能对话界面
   - 📁 文档上传支持
   - 🔍 热门问题推荐
   - 📝 会话历史管理

3. **学习助手 (StudyPage)**
   - 📚 课程管理
   - 🤖 AI学习工具
   - 📅 学习计划
   - 📊 进度统计

4. **文件管理 (FilesPage)**
   - ☁️ 文件上传下载
   - 🔍 智能搜索
   - 📂 分类管理
   - 🔗 分享功能

### 管理员功能
1. **用户管理**
   - 用户列表和权限管理
   - 账户状态控制

2. **内容管理**
   - 系统文档上传
   - 知识库维护

3. **数据分析**
   - 使用统计
   - 系统监控

## 🗄️ 数据库设计

### 核心表结构
```sql
-- 用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student', 'admin') DEFAULT 'student',
    is_verified BOOLEAN DEFAULT FALSE,
    language VARCHAR(10) DEFAULT 'zh-CN',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role)
);

-- 聊天会话表
CREATE TABLE chat_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
);

-- 聊天消息表
CREATE TABLE chat_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    role ENUM('user', 'assistant') NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id)
);

-- 用户文件表
CREATE TABLE user_files (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    purpose VARCHAR(100) DEFAULT 'other',
    embedding_status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (embedding_status)
);
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- MySQL 8.0+
- Redis 6.0+

### 1. 克隆项目
```bash
git clone https://github.com/Starbest2025/fyp.git
cd fyp
```

### 2. 后端设置
```bash
# 创建虚拟环境
cd backend
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要的配置

# 初始化数据库
python init_db.py

# 启动后端服务
python app.py
```

### 3. 前端设置
```bash
# 安装依赖
cd frontend
npm install

# 启动开发服务器
npm start
```

### 4. 访问应用
- 前端: http://localhost:3000
- 后端API: http://localhost:5000/api

## ⚙️ 配置说明

### 环境变量配置 (.env)
```bash
# 基本配置
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DEBUG=True

# 数据库配置
DATABASE_URL=mysql://username:password@localhost/ai_assistant
REDIS_URL=redis://localhost:6379/0

# OpenAI配置
OPENAI_API_KEY=your-openai-api-key

# 文件上传配置
MAX_CONTENT_LENGTH=10485760  # 10MB
UPLOAD_FOLDER=storage/uploads

# 邮件配置
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# 国际化配置
DEFAULT_LANGUAGE=zh-CN
SUPPORTED_LANGUAGES=zh-CN,zh-TW,en-US
```

## 📁 项目结构

```
fyp/
├── backend/                  # 后端代码
│   ├── app.py               # Flask应用入口
│   ├── config.py            # 配置文件
│   ├── requirements.txt     # Python依赖
│   ├── api/                 # API路由
│   │   ├── auth.py         # 认证路由
│   │   ├── chat.py         # 聊天路由
│   │   ├── files.py        # 文件管理路由
│   │   └── admin.py        # 管理员路由
│   ├── models/              # 数据模型
│   ├── services/            # 业务逻辑
│   ├── utils/               # 工具函数
│   └── storage/             # 文件存储
│
├── frontend/                 # 前端代码
│   ├── package.json         # Node.js依赖
│   ├── public/              # 静态资源
│   └── src/                 # 源代码
│       ├── components/      # React组件
│       ├── pages/           # 页面组件
│       ├── services/        # API服务
│       ├── utils/           # 工具函数
│       ├── hooks/           # 自定义Hooks
│       ├── context/         # Context提供者
│       └── i18n/            # 国际化配置
│
├── docs/                     # 项目文档
├── README.md                # 项目说明
└── .gitignore               # Git忽略文件
```

## 🔐 安全特性

1. **认证安全**
   - JWT令牌认证
   - 密码哈希加密
   - 邮箱验证机制

2. **文件安全**
   - 文件类型检查
   - 文件大小限制
   - 安全文件名处理

3. **API安全**
   - 请求频率限制
   - 输入验证和过滤
   - CORS跨域保护

## 🌍 国际化支持

系统支持三种语言：
- **简体中文** (zh-CN) - 默认语言
- **繁体中文** (zh-TW)
- **英语** (en-US)

用户可以在系统中随时切换语言，设置会自动保存。

## 📈 开发路线图

### 第1阶段：基础功能 (Week 1-2)
- [x] 项目架构设计
- [x] 数据库设计
- [ ] 用户认证系统
- [ ] 基础UI框架

### 第2阶段：核心功能 (Week 3-4)
- [ ] AI对话功能
- [ ] 文件上传处理
- [ ] RAG系统实现
- [ ] 多语言支持

### 第3阶段：完善优化 (Week 5)
- [ ] 管理员功能
- [ ] 性能优化
- [ ] 安全加固
- [ ] 部署配置

## 🚀 快速开始

### 环境要求
- Node.js 16+ 
- Python 3.8+
- MySQL 8.0+
- Git

### 前端安装

```bash
# 克隆项目
git clone <repository-url>
cd fyp

# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm start
```

### 后端安装

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动后端服务
python app.py
```

### 数据库配置

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE university_ai_system;"

# 导入数据库结构
mysql -u root -p university_ai_system < database/schema.sql

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置数据库连接信息
```

## 🔧 开发指南

### 项目结构
```
fyp/
├── frontend/                 # React前端应用
│   ├── src/
│   │   ├── components/       # 可复用组件
│   │   │   ├── common/       # 通用组件
│   │   │   │   ├── StatCard.tsx
│   │   │   │   ├── QuickActionCard.tsx
│   │   │   │   ├── PageHeader.tsx
│   │   │   │   └── LoadingSpinner.tsx
│   │   │   ├── chat/         # 聊天相关组件
│   │   │   └── ...
│   │   ├── pages/            # 页面组件
│   │   │   ├── HomePage.tsx
│   │   │   ├── ChatPage.tsx
│   │   │   ├── StudyPage.tsx
│   │   │   └── FilesPage.tsx
│   │   ├── context/          # React Context
│   │   ├── services/         # API服务
│   │   ├── styles/           # 样式文件
│   │   │   └── enhanced.css  # 全局增强样式
│   │   └── i18n/             # 国际化文件
│   └── package.json
├── backend/                  # Python后端API
│   ├── api/                  # API路由
│   ├── models/               # 数据模型
│   ├── services/             # 业务逻辑
│   ├── storage/              # 文件存储
│   └── requirements.txt
└── README.md
```

### 代码规范
- 使用 TypeScript 进行类型检查
- 遵循 ESLint + Prettier 代码规范
- 组件采用函数式组件 + Hooks
- 样式使用 CSS-in-JS 和全局CSS

### 组件开发示例
```tsx
// 示例：创建新的统计卡片组件
import React from 'react';
import { motion } from 'framer-motion';
import StatCard from '../components/common/StatCard';
import { UserOutlined } from '@ant-design/icons';

const MyComponent: React.FC = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <StatCard
        title="用户数量"
        value={1234}
        prefix={<UserOutlined />}
        color="#1890ff"
        trend={{ value: 12.5, isPositive: true }}
        description="本月新增用户"
        onClick={() => console.log('clicked')}
      />
    </motion.div>
  );
};
```

### API集成示例
```typescript
// services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  timeout: 10000,
});

// 请求拦截器
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const chatAPI = {
  sendMessage: (message: string) => 
    api.post('/chat/send', { message }),
  getHistory: () => 
    api.get('/chat/history'),
  uploadFile: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/chat/upload', formData);
  }
};
```

## 🛠️ 生产部署

### 前端构建
```bash
cd frontend
npm run build
# 构建产物在 frontend/build/ 目录
```

### 后端部署
```bash
cd backend
pip install -r requirements.txt
pip install gunicorn

# 使用 Gunicorn 启动生产服务器
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

### Nginx 配置
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://localhost:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Docker 部署 (可选)
```dockerfile
# 前端 Dockerfile
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=0 /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

## 📊 性能优化

### 前端优化
- ✅ 代码分割 (React.lazy + Suspense)
- ✅ 组件懒加载
- ✅ 图片压缩和懒加载
- ✅ Gzip 压缩
- ✅ 缓存策略

### 后端优化
- 数据库连接池
- Redis 缓存
- API 限流
- 静态文件CDN

## 🧪 测试

### 前端测试
```bash
# 运行单元测试
npm test

# 运行覆盖率测试
npm run test:coverage

# E2E 测试
npm run test:e2e
```

### 后端测试
```bash
# 运行 Python 测试
python -m pytest tests/

# 覆盖率测试
python -m pytest --cov=app tests/
```

## 🐛 常见问题

### Q: 无法连接到后端API
A: 请检查 `.env` 文件中的 `REACT_APP_API_URL` 配置是否正确。

### Q: 文件上传失败
A: 请检查文件大小是否超过10MB，格式是否支持（PDF、DOC、DOCX、TXT）。

### Q: AI回复很慢
A: 这是正常现象，OpenAI API 有时会较慢，系统已实现流式传输优化体验。

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

非开源项目

## 📞 联系方式

项目链接: [[[https://github.com/Starbest2025/fyp](https://github.com/normalman743/fyp](https://github.com/Starbest2025/fyp](https://github.com/normalman743/fyp)

## 🙏 致谢

- [OpenAI](https://openai.com/) - AI服务提供
- [Ant Design](https://ant.design/) - UI组件库
- [Flask](https://flask.palletsprojects.com/) - Web框架
- [React](https://reactjs.org/) - 前端框架
