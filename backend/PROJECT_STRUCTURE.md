# 🚀 校园LLM系统后端项目结构

本文档旨在详细说明校园LLM系统后端项目的目录结构和每个文件/文件夹的职责，以确保项目的高可维护性和团队协作效率。

```
. # 项目根目录
├── app/ # 核心应用代码
│   ├── __init__.py # Python包初始化文件
│   ├── api/ # API路由定义
│   │   ├── __init__.py # Python包初始化文件
│   │   └── v1/ # API版本1
│   │       ├── __init__.py # Python包初始化文件 (已完成)
│   │       ├── admin.py # 管理员相关API路由 (邀请码管理, 系统配置, 审计日志)
│   │       ├── auth.py # 认证与用户管理API路由 (注册, 登录, 用户信息) (已完成)
│   │       ├── chat.py # 聊天、消息与AI功能API路由
│   │       ├── course.py # 课程管理API路由
│   │       ├── file.py # 文件夹与文件管理API路由
│   │       └── semester.py # 学期管理API路由
│   ├── core/ # 核心配置与安全工具
│   │   ├── __init__.py # Python包初始化文件
│   │   ├── config.py # 项目配置 (数据库连接, JWT密钥, 文件路径等) (已完成)
│   │   └── security.py # 密码哈希和JWT token生成与验证 (已完成)
│   ├── crud/ # 数据库操作层 (Create, Read, Update, Delete)
│   │   ├── __init__.py # Python包初始化文件
│   │   ├── base.py # CRUD基类 (通用CRUD方法) (已完成)
│   │   ├── user.py # 用户CRUD操作 (已完成)
│   │   └── semester.py # 学期CRUD操作 (已完成)
│   │   └── ... (course.py, etc.) # 各模型对应的CRUD操作
│   ├── db/ # 数据库相关配置
│   │   ├── __init__.py # Python包初始化文件
│   │   ├── base.py # SQLAlchemy声明性基类 (所有模型继承) (已完成)
│   │   ├── session.py # 数据库引擎和会话管理 (get_db依赖) (已完成)
│   │   └── init_db.py # 数据库初始化脚本 (创建所有表) (已完成)
│   ├── models/ # SQLAlchemy数据库模型定义
│   │   ├── __init__.py # 导入所有模型，供SQLAlchemy发现 (已完成)
│   │   ├── user.py # 用户模型 (已完成)
│   │   ├── invite_code.py # 邀请码模型 (已完成)
│   │   ├── semester.py # 学期模型 (已完成)
│   │   ├── course.py # 课程模型 (已完成)
│   │   ├── file.py # 物理文件、逻辑文件、全局文件、文件夹、文档分块模型 (已完成)
│   │   ├── chat.py # 聊天模型 (已完成)
│   │   └── message.py # 消息、消息文件关联模型 (已完成)
│   ├── schemas/ # Pydantic数据模型 (请求/响应数据验证与序列化)
│   │   ├── __init__.py # Python包初始化文件 (已完成)
│   │   ├── user.py # 用户相关的Pydantic模型 (已完成)
│   │   ├── semester.py # 学期相关的Pydantic模型 (已完成)
│   │   ├── course.py # 课程相关的Pydantic模型 (已完成)
│   │   └── ... # 各模块对应的Pydantic模型
│   └── services/ # 业务逻辑服务层
│       ├── __init__.py # Python包初始化文件
│       └── ... (rag_service.py, file_service.py etc.) # 复杂业务逻辑处理
├── tests/ # 单元测试和集成测试
│   ├── __init__.py # Python包初始化文件 (已完成)
│   ├── test_auth.py # 认证模块的单元测试 (已完成)
│   ├── test_semester_course.py # 学期和课程模块的单元测试 (已完成，将补充)
│   └── ... # 各模块对应的测试文件
├── main.py # FastAPI应用入口文件 (已完成)
├── requirements.txt # Python项目依赖列表 (已完成)
├── .env # 环境变量配置文件 (敏感信息和配置) (已完成)
├── PROJECT_STRUCTURE.md # 本文档 (已完成，将更新)
└── .venv/ # Python虚拟环境 (由`python3 -m venv .venv`创建) (已完成)

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

## 后续开发计划

在完成用户认证模块后，建议按照以下顺序逐步实现其他功能：

1.  **学期与课程管理 (Semester & Course Management)**:
    *   定义Pydantic Schemas (`app/schemas/semester.py`, `app/schemas/course.py`) (已完成)
    *   实现CRUD操作 (`app/crud/semester.py`, `app/crud/course.py`)
    *   创建API路由 (`app/api/v1/semester.py`, `app/api/v1/course.py`)
    *   编写单元测试 (`tests/test_semester_course.py`)
        *   **学期管理测试单元**:
            *   **POST /api/v1/semesters - 创建学期**
                *   `test_create_semester_success`: 成功创建学期 (状态码 201, 返回正确数据, 数据库中存在)
                *   `test_create_semester_duplicate_code`: 尝试创建重复 `code` 的学期 (状态码 400, 返回错误信息)
                *   `test_create_semester_unauthenticated`: 未认证用户尝试创建学期 (状态码 401)
                *   `test_create_semester_invalid_data`: 提供无效数据 (例如缺少必填字段, 状态码 422)
                *   `test_create_semester_admin_only` (如果实现管理员权限): 非管理员用户尝试创建学期 (状态码 403)
            *   **GET /api/v1/semesters - 获取学期列表**
                *   `test_get_semesters_success`: 成功获取学期列表 (状态码 200, 返回列表, 包含已创建学期)
                *   `test_get_semesters_pagination`: 测试分页参数 `skip` 和 `limit` (状态码 200, 返回正确数量和范围的数据)
                *   `test_get_semesters_empty_list`: 没有学期时返回空列表 (状态码 200)
                *   `test_get_semesters_unauthenticated`: 未认证用户尝试获取列表 (状态码 401)
            *   **GET /api/v1/semesters/{id} - 获取单个学期**
                *   `test_get_semester_by_id_success`: 成功获取指定ID的学期 (状态码 200, 返回正确学期数据)
                *   `test_get_semester_by_id_not_found`: 获取不存在的学期 (状态码 404)
                *   `test_get_semester_by_id_unauthenticated`: 未认证用户尝试获取 (状态码 401)
            *   **PUT /api/v1/semesters/{id} - 更新学期**
                *   `test_update_semester_success`: 成功更新学期 (状态码 200, 返回更新后的数据, 数据库中数据已更新)
                *   `test_update_semester_not_found`: 更新不存在的学期 (状态码 404)
                *   `test_update_semester_unauthenticated`: 未认证用户尝试更新 (状态码 401)
                *   `test_update_semester_invalid_data`: 提供无效更新数据 (状态码 422)
                *   `test_update_semester_admin_only` (如果实现管理员权限): 非管理员用户尝试更新 (状态码 403)
            *   **DELETE /api/v1/semesters/{id} - 删除学期**
                *   `test_delete_semester_success`: 成功删除学期 (状态码 200, 再次获取返回404)
                *   `test_delete_semester_not_found`: 删除不存在的学期 (状态码 404)
                *   `test_delete_semester_unauthenticated`: 未认证用户尝试删除 (状态码 401)
                *   `test_delete_semester_admin_only` (如果实现管理员权限): 非管理员用户尝试删除 (状态码 403)
        *   **课程管理测试单元**:
            *   **POST /api/v1/courses - 创建课程**
                *   `test_create_course_success`: 成功创建课程 (状态码 201, 返回正确数据, 数据库中存在)
                *   `test_create_course_duplicate_code_in_semester`: 同一学期内创建重复 `code` 的课程 (状态码 400)
                *   `test_create_course_duplicate_code_across_semesters`: 不同学期内创建重复 `code` 的课程 (状态码 201)
                *   `test_create_course_semester_not_found`: 关联的学期不存在 (状态码 404)
                *   `test_create_course_unauthenticated`: 未认证用户尝试创建 (状态码 401)
                *   `test_create_course_invalid_data`: 提供无效数据 (状态码 422)
            *   **GET /api/v1/courses - 获取课程列表**
                *   `test_get_courses_success`: 成功获取课程列表 (状态码 200, 返回列表, 包含已创建课程)
                *   `test_get_courses_by_semester_id`: 按 `semester_id` 过滤课程 (状态码 200, 返回正确过滤结果)
                *   `test_get_courses_pagination`: 测试分页参数 `skip` 和 `limit` (状态码 200)
                *   `test_get_courses_empty_list`: 没有课程时返回空列表 (状态码 200)
                *   `test_get_courses_unauthenticated`: 未认证用户尝试获取列表 (状态码 401)
            *   **GET /api/v1/courses/{id} - 获取单个课程**
                *   `test_get_course_by_id_success`: 成功获取指定ID的课程 (状态码 200, 返回正确课程数据)
                *   `test_get_course_by_id_not_found`: 获取不存在的课程 (状态码 404)
                *   `test_get_course_by_id_unauthenticated`: 未认证用户尝试获取 (状态码 401)
                *   `test_get_course_by_id_not_owned` (如果实现课程所有权): 获取不属于自己的课程 (状态码 403)
            *   **PUT /api/v1/courses/{id} - 更新课程**
                *   `test_update_course_success`: 成功更新课程 (状态码 200, 返回更新后的数据, 数据库中数据已更新)
                *   `test_update_course_not_found`: 更新不存在的课程 (状态码 404)
                *   `test_update_course_unauthenticated`: 未认证用户尝试更新 (状态码 401)
                *   `test_update_course_invalid_data`: 提供无效更新数据 (状态码 422)
                *   `test_update_course_not_owned` (如果实现课程所有权): 更新不属于自己的课程 (状态码 403)
            *   **DELETE /api/v1/courses/{id} - 删除课程**
                *   `test_delete_course_success`: 成功删除课程 (状态码 200, 再次获取返回404)
                *   `test_delete_course_not_found`: 删除不存在的课程 (状态码 404)
                *   `test_delete_course_unauthenticated`: 未认证用户尝试删除 (状态码 401)
                *   `test_delete_course_not_owned` (如果实现课程所有权): 删除不属于自己的课程 (状态码 403)
    *   **理由**: 学期和课程是组织文件和聊天的基础结构，先完成它们可以为后续的文件和聊天功能提供上下文。

2.  **文件夹与文件管理 (Folder & File Management)**:
    *   定义Pydantic Schemas (`app/schemas/file.py`)
    *   实现CRUD操作 (`app/crud/file.py`, `app/crud/folder.py`)
    *   创建API路由 (`app/api/v1/file.py`)
    *   编写单元测试 (`tests/test_file.py`)
    *   **理由**: 文件管理是RAG系统的核心输入，需要与课程结构紧密结合。

3.  **聊天、消息与AI功能 (Chat, Message & AI Functionality)**:
    *   定义Pydantic Schemas (`app/schemas/chat.py`, `app/schemas/message.py`)
    *   实现CRUD操作 (`app/crud/chat.py`, `app/crud/message.py`)
    *   创建API路由 (`app/api/v1/chat.py`)
    *   实现RAG服务 (`app/services/rag_service.py`)
    *   编写单元测试 (`tests/test_chat.py`, `tests/test_message.py`)
    *   **理由**: 这是系统的核心价值所在，涉及LLM和RAG的复杂逻辑。

4.  **系统管理 (Admin APIs)**:
    *   定义Pydantic Schemas (`app/schemas/admin.py`)
    *   实现CRUD操作 (`app/crud/invite_code.py`)
    *   创建API路由 (`app/api/v1/admin.py`)
    *   编写单元测试 (`tests/test_admin.py`)
    *   **理由**: 管理功能通常在核心业务功能稳定后进行。

## 测试策略：先写测试 (Test-Driven Development - TDD)

对于本项目，我强烈建议采用**测试驱动开发 (TDD)** 的方式进行。这意味着在编写任何功能代码之前，我们先编写测试用例。

**理由如下：**

1.  **明确需求**: 编写测试迫使我们清晰地思考功能的需求和预期行为。这有助于在早期发现需求模糊或不一致的地方。
2.  **更好的设计**: 为了使代码易于测试，我们自然会倾向于编写模块化、低耦合的代码。这会促使我们设计出更健壮、更易于维护的架构。
3.  **减少Bug**: TDD 鼓励小步快跑，每次只实现通过一个测试所需的最小代码。这使得Bug更容易被发现和定位。
4.  **内置回归测试**: 随着项目的发展，每次修改代码后，我们都可以运行所有测试，确保新功能没有破坏现有功能，提供强大的回归测试套件。
5.  **代码即文档**: 测试用例本身就是对代码行为的最好文档，它们清晰地展示了代码的预期用途和边界情况。
6.  **提高信心**: 拥有全面的测试套件，可以让我们在重构或添加新功能时更有信心，减少对引入新错误的担忧。

**实践方式：**

-   **红-绿-重构 (Red-Green-Refactor)** 循环：
    1.  **红 (Red)**: 编写一个失败的测试（因为功能尚未实现）。
    2.  **绿 (Green)**: 编写最少量的代码，使测试通过。
    3.  **重构 (Refactor)**: 优化代码，同时确保所有测试仍然通过。

虽然 TDD 在初期可能会感觉速度较慢，但从长远来看，它能显著提高代码质量、减少后期维护成本，并提升开发效率，这与我们追求“高维护性”的目标高度契合。