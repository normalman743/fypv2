# 大学AI智能助手系统 - 前端

> 基于RAG（检索增强生成）技术的校园智能问答与学习管理系统

## 📋 项目概述

这是一个专为大学生设计的AI智能助手系统，旨在整合校园学习资源和生活信息，提供智能问答、文件管理、学习计划等功能。

### 🎯 核心功能模块

#### 1. **首页 (HomePage)** 📊
- **功能**: 系统仪表板和快速入口
- **特点**: 
  - 欢迎界面和用户统计
  - 快速操作入口（聊天、学习助手）
  - 个人数据概览（对话次数、上传文件、学习时长等）

#### 2. **智能聊天 (ChatPage)** 💬
- **功能**: AI对话界面，支持校园生活咨询
- **特点**:
  - 多会话管理
  - 支持文件附件上传
  - 实时AI问答（基于RAG技术）
  - 聊天历史记录

#### 3. **学习管理 (StudyPage)** 📚
- **功能**: 综合学习工具平台
- **特点**:
  - 学习计划制定和管理
  - 学习资料整理
  - 练习题生成和测验
  - 学习进度跟踪
  - 学习日历和提醒

#### 4. **文件管理 (FilesPage)** 📁
- **功能**: 学习资料上传和管理
- **特点**:
  - 支持多种文件格式（PDF、Word、Excel等）
  - 文件状态跟踪（上传中、处理中、完成）
  - 文件预览和下载
  - RAG知识库构建

#### 5. **管理后台 (AdminPage)** ⚙️
- **功能**: 系统管理和数据分析
- **特点**:
  - 用户管理
  - 系统统计
  - 内容审核
  - 配置管理

#### 6. **用户认证** 🔐
- **登录页 (LoginPage)**: 用户登录
- **注册页 (RegisterPage)**: 新用户注册
- **个人资料 (ProfilePage)**: 用户信息管理

## 🛠 技术栈

- **前端框架**: React 18 + TypeScript
- **UI组件库**: Ant Design
- **路由管理**: React Router v6
- **状态管理**: React Context API
- **国际化**: react-i18next (支持中文简体、繁体、英文)
- **构建工具**: Create React App

## 📁 项目结构

```
src/
├── components/          # 可复用组件
│   ├── admin/          # 管理员组件
│   ├── auth/           # 认证相关组件
│   ├── chat/           # 聊天组件
│   ├── common/         # 通用组件
│   ├── files/          # 文件管理组件
│   └── study/          # 学习相关组件
├── context/            # React Context
│   └── AuthContext.tsx # 认证上下文
├── hooks/              # 自定义Hooks
├── i18n/               # 国际化配置
├── pages/              # 页面组件
├── services/           # API服务
└── utils/              # 工具函数
```

## 🚀 开发计划与建议

### 阶段一：UI完善 (当前重点)

#### 1. **优化现有页面UI** 🎨
- [ ] 完善响应式设计，确保移动端适配
- [ ] 统一设计语言和色彩系统
- [ ] 优化加载状态和错误处理
- [ ] 增加更多交互动画

#### 2. **完善组件库** 🧩
- [ ] 开发通用组件（搜索框、卡片、按钮等）
- [ ] 创建聊天组件（消息气泡、输入框、文件上传）
- [ ] 开发学习相关组件（进度条、日历、测验界面）
- [ ] 建立组件文档

#### 3. **原型测试** 🔍
- [ ] 创建交互原型
- [ ] 进行用户体验测试
- [ ] 收集反馈并优化

### 阶段二：后端集成准备

#### 1. **API接口设计** 📡
- [ ] 定义RESTful API规范
- [ ] 设计数据结构
- [ ] 创建Mock数据服务

#### 2. **服务层开发** ⚡
- [ ] 实现API调用服务
- [ ] 错误处理机制
- [ ] 数据缓存策略

### 阶段三：RAG系统集成

#### 1. **AI聊天功能** 🤖
- [ ] 集成OpenAI/本地LLM API
- [ ] 实现流式响应
- [ ] 上下文管理

#### 2. **知识库管理** 📖
- [ ] 文件解析和索引
- [ ] 向量数据库集成
- [ ] 检索优化

## 👥 团队分工建议

### S (你) + A - 技术开发
- **前端开发**: React组件开发、UI优化
- **后端开发**: Python API开发、数据库设计
- **系统集成**: RAG技术实现、部署配置

### B - 需求分析
- **用户调研**: 学生需求访谈、功能需求整理
- **产品设计**: 用户体验设计、功能优先级排序
- **测试反馈**: 原型测试、用户反馈收集

### C - 数据收集
- **校园数据**: 收集学校设施信息、开放时间等
- **学习资源**: 整理课程资料、学习指南
- **知识库构建**: 数据清洗、标注、组织

## 🎯 近期目标

### 本周重点
1. **完善UI设计** - 统一视觉风格，优化用户体验
2. **组件开发** - 创建可复用的核心组件
3. **需求调研** - B同学开始用户访谈
4. **数据收集** - C同学开始收集校园基础数据

### 下周目标
1. **Mock API** - 创建前端开发用的模拟接口
2. **后端框架** - 搭建Python后端基础架构
3. **数据库设计** - 设计MySQL数据表结构

## 💡 技术建议

### 前端优化
- 使用React Query进行数据状态管理
- 实现虚拟滚动优化大量数据展示
- 添加PWA支持提升用户体验

### 后端技术选型
- **框架**: FastAPI (高性能、自动文档生成)
- **数据库**: MySQL + Redis (关系数据 + 缓存)
- **AI集成**: LangChain + Vector Database (Chroma/Pinecone)

### 部署方案
- **开发环境**: Docker Compose
- **生产环境**: Linux服务器 + Nginx + Gunicorn
- **CI/CD**: GitHub Actions

## 📞 联系与协作

建议使用以下工具进行团队协作：
- **代码管理**: Git + GitHub
- **项目管理**: GitHub Projects / Trello
- **设计协作**: Figma
- **文档共享**: Notion / 腾讯文档

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

The page will reload if you make edits.\
You will also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can’t go back!**

If you aren’t satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you’re on your own.

You don’t have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn’t feel obligated to use this feature. However we understand that this tool wouldn’t be useful if you couldn’t customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).
