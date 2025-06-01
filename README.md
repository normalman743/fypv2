# 🎓 大学AI助手系统 - University AI Assistant

一个基于React + TypeScript的现代化大学智能助手系统，为大学生提供校园生活问答和学习管理的一站式解决方案。

![项目状态](https://img.shields.io/badge/状态-开发中-green)
![前端](https://img.shields.io/badge/前端-React%2018%20%2B%20TypeScript-blue)
![UI库](https://img.shields.io/badge/UI-Ant%20Design%205.x-orange)
![国际化](https://img.shields.io/badge/国际化-支持中英文-success)

## 🌟 核心功能

### 💬 校园生活问答
- 🤖 类似ChatGPT的智能对话界面
- 📱 响应式聊天设计，支持移动端
- 📎 文件上传功能 (图片/文本，最大10MB)
- 🔄 消息重发和编辑功能
- 📚 会话历史管理
- ⚡ 快速问题模板

### 📚 学习助手
- 📅 智能学期管理 (自动识别当前学期)
- 📖 课程创建和管理
- 📁 结构化资料管理 (Outline/Tutorial/Lecture/Note)
- 💬 课程专属问答聊天
- 🗂️ 自定义文件夹创建
- 📤 拖拽式文件上传

### 📁 文件管理
- 🔍 文件搜索和筛选
- 👁️ 在线预览功能
- 🏷️ 标签和分类管理
- 📊 文件统计分析

### 🔐 用户系统
- 🚪 安全的登录/注册
- 👤 个人资料管理
- 🌍 多语言支持 (简体中文/繁体中文/英语)
- 🎨 主题和偏好设置

## 🏗️ 技术架构

### 前端技术栈
```json
{
  "framework": "React 18 + TypeScript",
  "ui_library": "Ant Design 5.x",
  "routing": "React Router v6",
  "state_management": "React Context API",
  "animations": "Framer Motion",
  "internationalization": "React i18next",
  "styling": "CSS Modules + Ant Design Theme",
  "build_tool": "Create React App"
}
```

### 项目结构
```
frontend/
├── src/
│   ├── components/          # 可复用组件
│   │   ├── auth/           # 认证相关组件
│   │   ├── chat/           # 聊天相关组件
│   │   ├── common/         # 通用组件
│   │   └── files/          # 文件管理组件
│   ├── context/            # React Context
│   ├── i18n/               # 国际化配置
│   ├── pages/              # 页面组件
│   └── styles/             # 样式文件
└── public/                 # 静态资源
```
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
```

## 🚀 快速开始

### 安装依赖
```bash
cd frontend
npm install
```

### 启动开发服务器
```bash
npm start
```
应用将在 `http://localhost:3000` 启动

### 构建生产版本
```bash
npm run build
```

## 📱 功能演示

### 主要页面
- **首页**: 仪表盘 + 快捷操作
- **校园生活问答**: 智能聊天界面
- **学习助手**: 课程管理 + 资料组织
- **文件管理**: 文档上传和管理
- **用户中心**: 个人设置和偏好

### 核心特性
- ✅ 响应式设计 (支持移动端)
- ✅ 多语言国际化
- ✅ 现代化UI设计
- ✅ 文件上传和管理
- ✅ 会话历史管理
- ✅ 智能学期识别

## 📊 开发进度

- 🎨 **UI架构**: 100% ✅
- 💬 **校园问答**: 95% ✅
- 📚 **学习助手**: 85% 🔄
- 📁 **文件管理**: 80% 🔄
- 🔐 **用户系统**: 100% ✅

## 📄 文档

- [项目现状文档](./PROJECT_STATUS.md) - 详细的开发进度和功能说明
- [前端README](./frontend/README.md) - 前端特定的开发指南

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📝 许可证

MIT License

---

*最后更新：2025年6月1日*
