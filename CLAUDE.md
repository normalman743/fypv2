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
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 

注意请你不要自己打开 让user 开启 以便user提供错误代码
```

### 注意事项

1. 使用python前注意source venv
2. 如果需要curl或者直接和localhost 8000 注意--noproxy
3. 注意不能修改所有的api文档 可以增加 不能修改 这个是最终对齐方向
4. 目前有的api访问 8000/docx 

