# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Campus LLM System (校园LLM系统) - a RAG-based intelligent campus assistant that provides unified academic support and campus life information services for university students. The system integrates document processing, vector search, and conversational AI capabilities.

## Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with async support
- **Database**: MySQL + Chroma vector database
- **AI/RAG**: LangChain with OpenAI integration
- **Task Queue**: Celery with Redis
- **File Storage**: Local filesystem with SHA256 deduplication

### Key Components
- **Models**: SQLAlchemy ORM models in `app/models/`
- **API Routes**: REST endpoints in `app/api/v1/`
- **Services**: Business logic in `app/services/`
- **Schemas**: Pydantic models in `app/schemas/`
- **Tasks**: Async file processing in `app/tasks/`

## Development Commands

### Database Management
you can find database info in
/Users/mannormal/Downloads/fyp/campus_llm_database_analysis.md


### Running the Application
```bash
# Start FastAPI server
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 

注意请你不要自己打开 让user 开启 以便user提供错误代码
```

### 注意事项

1. 使用python前注意source venv
2. 如果需要curl或者直接和localhost 8000 注意--noproxy
3. 注意不能修改所有的api文档 可以增加 不能修改 这个是最终对齐方向
4. 目前有的api访问 8000/docx
5. **测试健壮性原则**：写测试文件时不要假设硬编码的ID（如course_id=1），应动态获取或在reset系统中创建所需的基础数据 


## Workflow

### API开发标准流程

1. **API文档设计**: 编写详细的api_*.md文档，定义接口规范
2. **API实现对齐**: 确保实际API实现与文档规范完全对齐
3. **系统化测试**: 使用api_test_v3进行全面测试验证

### 测试流程

#### 使用api_test_v3进行测试
```bash
cd backend/api_test_v3
python -m pytest test_specific_module.py -v
```

#### 测试进度跟踪
按照API文档模块组织：

- ✅ **已完成测试**: 
  - 认证与用户管理 (api_auth.md → test_auth_user.py)
  - 学期与课程管理 (api_semester_course.md → test_semester_course.py, test_course_folders.py)
  - 文件夹与文件管理 (api_folder_file.md → test_file_upload.py) ⚠️ 部分API未实现
  
- ⏳ **待测试**: 
  - 聊天、消息与AI功能 (api_chat_message_rag.md → test_chat_message.py)
  - 系统管理 (api_admin.md → test_admin_functions.py)
  - 删除操作 (跨模块功能 → test_delete_operations.py)

#### 测试注意事项
- 测试前确保数据库已启动并连接正常
- 使用reset_system.py重置测试环境
- 测试时注意--noproxy参数用于本地连接
- **RAG功能测试**: 运行`python prepare_test_documents.py`上传测试文档
- **Mock vs Production模式**: 没有OpenAI API密钥时系统使用Mock模式，RAG结果为模拟数据

#### API开发和测试重要原则

⚠️ **编写测试API前的必要步骤**：
1. **查看API文档** - 先阅读对应的`api_*.md`文档了解接口定义
2. **检查真实API** - 访问 `/openapi.json` 或 `/docs` 查看实际API参数和响应格式
3. **对比验证** - 确保文档与实际实现一致，发现不匹配及时更新

⚠️ **编写真实API前的必要步骤**：
1. **查看API文档** - 确保理解业务需求和接口规范
2. **检查数据库结构** - 参考 `/Users/mannormal/Downloads/fyp/campus_llm_database_analysis.md` 了解表结构和字段
3. **验证数据一致性** - 确保API设计与数据库模型匹配

⚠️ **三方对齐原则**：
- **API文档** ↔ **真实API实现** ↔ **数据库结构** 必须保持一致
- 任何修改都要同时更新相关的文档、代码和数据库
- 测试用例要基于最新的API文档编写

🔍 **常见对齐检查点**：
- **字段名称**: 确保API文档、数据库字段、请求参数名称一致
- **数据类型**: 确保string、int、boolean等类型在三方中匹配
- **必填字段**: 确保required字段在API和数据库中都正确标记
- **枚举值**: 确保状态码、类型等枚举值在各处保持一致

📋 **开发检查清单**：
- [ ] 查看现有API文档了解接口规范
- [ ] 检查 `/openapi.json` 确认当前API实现  
- [ ] 查看数据库分析文档确认表结构
- [ ] 对比三者找出不一致之处
- [ ] 优先以数据库结构为准，更新API文档和实现

