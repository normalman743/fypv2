# 🚀 校园LLM系统后端项目结构

本文档旨在详细说明校园LLM系统后端项目的目录结构和每个文件/文件夹的职责，以确保项目的高可维护性和团队协作效率。

```
. # 项目根目录
├── app/ # 核心应用代码
│   ├── __init__.py # Python包初始化文件
│   ├── api/ # API路由定义
│   │   ├── __init__.py # Python包初始化文件
│   │   └── v1/ # API版本1
│   │       ├── __init__.py # Python包初始化文件
│   │       ├── admin.py # 管理员相关API路由 (邀请码管理, 系统配置, 审计日志)
│   │       ├── auth.py # 认证与用户管理API路由 (注册, 登录, 用户信息)
│   │       ├── chat.py # 聊天、消息与AI功能API路由
│   │       ├── course.py # 课程管理API路由
│   │       ├── file.py # 文件夹与文件管理API路由
│   │       └── semester.py # 学期管理API路由
│   ├── core/ # 核心配置与安全工具
│   │   ├── __init__.py # Python包初始化文件
│   │   └── config.py # 项目配置 (数据库连接, JWT密钥, 文件路径等)
│   ├── crud/ # 数据库操作层 (Create, Read, Update, Delete)
│   │   ├── __init__.py # Python包初始化文件
│   │   └── base.py # CRUD基类 (通用CRUD方法)
│   │   └── ... (user.py, course.py等) # 各模型对应的CRUD操作
│   ├── db/ # 数据库相关配置
│   │   ├── __init__.py # Python包初始化文件
│   │   ├── base.py # SQLAlchemy声明性基类 (所有模型继承)
│   │   └── session.py # 数据库引擎和会话管理 (get_db依赖)
│   │   └── init_db.py # 数据库初始化脚本 (创建所有表)
│   ├── models/ # SQLAlchemy数据库模型定义
│   │   ├── __init__.py # 导入所有模型，供SQLAlchemy发现
│   │   ├── user.py # 用户模型
│   │   ├── invite_code.py # 邀请码模型
│   │   ├── semester.py # 学期模型
│   │   ├── course.py # 课程模型
│   │   ├── file.py # 物理文件、逻辑文件、全局文件、文件夹、文档分块模型
│   │   ├── chat.py # 聊天模型
│   │   └── message.py # 消息、消息文件关联模型
│   ├── schemas/ # Pydantic数据模型 (请求/响应数据验证与序列化)
│   │   ├── __init__.py # Python包初始化文件
│   │   └── ... (user.py, auth.py等) # 各模块对应的Pydantic模型
│   └── services/ # 业务逻辑服务层
│       ├── __init__.py # Python包初始化文件
│       └── ... (rag_service.py, file_service.py等) # 复杂业务逻辑处理
├── tests/ # 单元测试和集成测试
│   └── ... # 各模块对应的测试文件
├── main.py # FastAPI应用入口文件
├── requirements.txt # Python项目依赖列表
├── .env # 环境变量配置文件 (敏感信息和配置)
├── PROJECT_STRUCTURE.md # 本文档
└── .venv/ # Python虚拟环境 (由`python3 -m venv .venv`创建)

```

## 维护性与Git版本控制

- **模块化设计**: 每个功能模块都有独立的API路由、CRUD操作、数据库模型和Pydantic Schema，确保代码职责分离，易于理解和维护。
- **清晰的命名**: 文件和变量命名遵循一致的规范，提高代码可读性。
- **依赖注入**: FastAPI的依赖注入机制将用于管理数据库会话等依赖，降低模块间的耦合度。
- **Pydantic验证**: 严格的数据输入输出验证，减少运行时错误。
- **Git提交规范**: 每次完成一个独立的功能或修复一个bug时，都会进行一次清晰、有意义的Git提交。提交信息将遵循以下格式：
  ```
  <type>(<scope>): <subject>

  <body>

  <footer>
  ```
  - **type**: feat (新功能), fix (bug修复), docs (文档), style (格式), refactor (重构), test (测试), chore (构建过程或辅助工具的变动)
  - **scope**: 影响的模块或范围 (e.g., auth, db, models, file)
  - **subject**: 简短的描述 (少于50字)
  - **body**: 详细说明 (可选)
  - **footer**: 关联的issue或任务 (可选)

我们将严格遵循这些规范，以确保项目的健康发展和高可维护性。