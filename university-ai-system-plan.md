# University AI Assistant - Complete System Implementation Plan

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                 Frontend (React)                         │
│  ┌────────────┐  ┌────────────┐  ┌─────────────────┐  │
│  │  Auth UI   │  │  Chat UI   │  │  Admin Panel    │  │
│  │            │  │            │  │                 │  │
│  │ - Login    │  │ - Messages │  │ - Upload Docs   │  │
│  │ - Register │  │ - Upload   │  │ - Manage Users  │  │
│  │           │  │ - History  │  │ - Analytics     │  │
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
     ┌───────────────────────┼───────────────────────┐
     ▼                       ▼                       ▼
┌─────────┐          ┌─────────────┐         ┌─────────────┐
│  MySQL  │          │    Redis    │         │File Storage │
│         │          │   (Cache)   │         │  (Local)    │
└─────────┘          └─────────────┘         └─────────────┘
```

## 2. Database Schema (MySQL)

```sql
-- Users table
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    role ENUM('user', 'admin') DEFAULT 'user',
    verification_code VARCHAR(6),
    verification_expires DATETIME,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_email (email),
    INDEX idx_role (role)
);

-- Chat sessions table
CREATE TABLE chat_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
);

-- Chat messages table
CREATE TABLE chat_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id)
);

-- User files table
CREATE TABLE user_files (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50),
    file_size INT,
    purpose ENUM('study_material', 'assignment', 'notes', 'other') DEFAULT 'other',
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    embedding_status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (embedding_status)
);

-- System documents table (admin managed)
CREATE TABLE system_documents (
    id INT PRIMARY KEY AUTO_INCREMENT,
    doc_type ENUM('student_handbook', 'campus_info') NOT NULL,
    title VARCHAR(255) NOT NULL,
    content LONGTEXT,
    file_path VARCHAR(500),
    metadata JSON,
    uploaded_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(id),
    INDEX idx_doc_type (doc_type)
);

-- Study plans table
CREATE TABLE study_plans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    session_id INT,
    title VARCHAR(255),
    plan_content JSON,
    available_hours INT,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id)
);

-- Practice questions table
CREATE TABLE practice_questions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    file_id INT,
    question TEXT NOT NULL,
    options JSON,
    correct_answer TEXT,
    explanation TEXT,
    difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'medium',
    topic VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES user_files(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id)
);

-- System prompts table (for admin configuration)
CREATE TABLE system_prompts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    prompt_text TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    updated_by INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(id),
    INDEX idx_name (name)
);

-- Analytics table
CREATE TABLE analytics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    event_type VARCHAR(50) NOT NULL,
    event_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at)
);
```

## 3. API Documentation

### 3.1 Authentication Endpoints

```python
# POST /api/auth/register
{
    "email": "student@university.edu"
}
# Response: { "message": "Verification code sent to email" }

# POST /api/auth/verify
{
    "email": "student@university.edu",
    "code": "123456"
}
# Response: { "token": "jwt_token", "user": {...} }

# POST /api/auth/login
{
    "email": "student@university.edu",
    "password": "hashed_password"
}
# Response: { "token": "jwt_token", "user": {...} }

# POST /api/auth/logout
# Headers: Authorization: Bearer <token>
# Response: { "message": "Logged out successfully" }
```

### 3.2 Chat Endpoints

```python
# GET /api/chat/sessions
# Headers: Authorization: Bearer <token>
# Response: { "sessions": [...] }

# POST /api/chat/sessions
# Headers: Authorization: Bearer <token>
{
    "title": "Calculus Help Session"
}
# Response: { "session": {...} }

# GET /api/chat/sessions/{session_id}/messages
# Headers: Authorization: Bearer <token>
# Response: { "messages": [...] }

# POST /api/chat/sessions/{session_id}/messages
# Headers: Authorization: Bearer <token>
{
    "content": "Explain integration by parts",
    "context_files": [file_id1, file_id2]  # Optional
}
# Response: Streaming response with AI reply

# DELETE /api/chat/sessions/{session_id}
# Headers: Authorization: Bearer <token>
# Response: { "message": "Session deleted" }
```

### 3.3 File Management Endpoints

```python
# POST /api/files/upload
# Headers: Authorization: Bearer <token>
# Form-data: file, purpose
# Response: { "file": {...} }

# GET /api/files
# Headers: Authorization: Bearer <token>
# Response: { "files": [...] }

# DELETE /api/files/{file_id}
# Headers: Authorization: Bearer <token>
# Response: { "message": "File deleted" }
```

### 3.4 Study Tools Endpoints

```python
# POST /api/study/generate-questions
# Headers: Authorization: Bearer <token>
{
    "file_id": 123,
    "count": 5,
    "difficulty": "medium"
}
# Response: { "questions": [...] }

# POST /api/study/create-plan
# Headers: Authorization: Bearer <token>
{
    "topics": ["calculus", "linear algebra"],
    "available_hours": 10,
    "deadline": "2024-12-20"
}
# Response: { "plan": {...} }

# GET /api/study/plans
# Headers: Authorization: Bearer <token>
# Response: { "plans": [...] }
```

### 3.5 Admin Endpoints

```python
# POST /api/admin/system-docs
# Headers: Authorization: Bearer <token>
# Requires: role=admin
{
    "doc_type": "student_handbook",
    "title": "Student Handbook 2024",
    "content": "...",
    "metadata": {...}
}

# GET /api/admin/users
# Headers: Authorization: Bearer <token>
# Requires: role=admin
# Response: { "users": [...] }

# PUT /api/admin/users/{user_id}
# Headers: Authorization: Bearer <token>
# Requires: role=admin
{
    "role": "admin",
    "is_verified": true
}

# GET /api/admin/analytics
# Headers: Authorization: Bearer <token>
# Requires: role=admin
# Query params: start_date, end_date, event_type
# Response: { "analytics": {...} }

# PUT /api/admin/prompts
# Headers: Authorization: Bearer <token>
# Requires: role=admin
{
    "name": "study_plan_prompt",
    "prompt_text": "You are a helpful study assistant..."
}
```

## 4. Folder Structure

### 4.1 Backend (Flask)

```
backend/
├── app.py                 # Flask app initialization
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
├── .gitignore
│
├── api/                  # API routes
│   ├── __init__.py
│   ├── auth.py          # Authentication routes
│   ├── chat.py          # Chat routes
│   ├── files.py         # File management routes
│   ├── study.py         # Study tools routes
│   └── admin.py         # Admin routes
│
├── models/               # Database models
│   ├── __init__.py
│   ├── user.py
│   ├── chat.py
│   ├── file.py
│   └── study.py
│
├── services/            # Business logic
│   ├── __init__.py
│   ├── auth_service.py
│   ├── openai_service.py
│   ├── rag_service.py
│   ├── file_service.py
│   └── study_service.py
│
├── utils/               # Utility functions
│   ├── __init__.py
│   ├── decorators.py    # Auth decorators
│   ├── validators.py
│   ├── embeddings.py
│   └── rate_limiter.py
│
├── storage/            # File storage
│   ├── uploads/
│   └── system_docs/
│
└── tests/              # Test files
    ├── __init__.py
    ├── test_auth.py
    ├── test_chat.py
    └── test_utils.py
```

### 4.2 Frontend (React)

```
frontend/
├── package.json
├── package-lock.json
├── .gitignore
├── .env
│
├── public/
│   ├── index.html
│   └── favicon.ico
│
├── src/
│   ├── index.js
│   ├── App.js
│   ├── index.css
│   │
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.jsx
│   │   │   ├── RegisterForm.jsx
│   │   │   └── VerificationForm.jsx
│   │   ├── chat/
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── MessageList.jsx
│   │   │   ├── MessageInput.jsx
│   │   │   └── SessionList.jsx
│   │   ├── files/
│   │   │   ├── FileUpload.jsx
│   │   │   └── FileList.jsx
│   │   ├── study/
│   │   │   ├── QuestionGenerator.jsx
│   │   │   └── StudyPlanCreator.jsx
│   │   ├── admin/
│   │   │   ├── AdminDashboard.jsx
│   │   │   ├── UserManagement.jsx
│   │   │   └── Analytics.jsx
│   │   └── common/
│   │       ├── Header.jsx
│   │       ├── Footer.jsx
│   │       └── LoadingSpinner.jsx
│   │
│   ├── pages/
│   │   ├── Home.jsx
│   │   ├── Chat.jsx
│   │   ├── Study.jsx
│   │   ├── Admin.jsx
│   │   └── Profile.jsx
│   │
│   ├── services/
│   │   ├── api.js
│   │   ├── auth.js
│   │   ├── chat.js
│   │   └── admin.js
│   │
│   ├── utils/
│   │   ├── constants.js
│   │   ├── helpers.js
│   │   └── validators.js
│   │
│   ├── hooks/
│   │   ├── useAuth.js
│   │   ├── useChat.js
│   │   └── useStream.js
│   │
│   └── context/
│       ├── AuthContext.js
│       └── ChatContext.js
```

## 5. Development Roadmap

### Phase 1: Foundation (Week 1-2)
1. **Day 1-2**: Set up project structure, Git repository
2. **Day 3-4**: Create MySQL database schema, set up Redis
3. **Day 5-6**: Implement basic Flask app with configuration
4. **Day 7-8**: Build authentication system (register, verify, login)
5. **Day 9-10**: Create React project, implement auth UI
6. **Day 11-12**: Connect frontend auth to backend
7. **Day 13-14**: Add rate limiting and basic security

### Phase 2: Core Chat Features (Week 3-4)
1. **Day 15-16**: Implement chat session management
2. **Day 17-18**: Integrate OpenAI API with streaming
3. **Day 19-20**: Build chat UI with message history
4. **Day 21-22**: Implement file upload system
5. **Day 23-24**: Create document processing and embedding
6. **Day 25-26**: Build basic RAG system
7. **Day 27-28**: Test chat with context retrieval

### Phase 3: Study Tools (Week 5)
1. **Day 29-30**: Implement question generation
2. **Day 31-32**: Build study plan creation
3. **Day 33-34**: Create UI for study tools
4. **Day 35**: Integration testing

### Phase 4: Admin Features (Week 6)
1. **Day 36-37**: Build admin dashboard
2. **Day 38-39**: Implement system document management
3. **Day 40-41**: Create user management interface
4. **Day 42**: Add analytics and reporting

### Phase 5: Polish & Deploy (Week 7)
1. **Day 43-44**: UI/UX improvements
2. **Day 45-46**: Performance optimization
3. **Day 47-48**: Security audit and fixes
4. **Day 49**: Deployment preparation

## 6. Key Implementation Details

### 6.1 OpenAI Streaming Implementation

```python
# services/openai_service.py
import openai
from flask import Response, stream_with_context

class OpenAIService:
    def __init__(self, api_key):
        self.client = openai.OpenAI(api_key=api_key)
    
    def stream_chat_completion(self, messages, context=""):
        system_prompt = self._get_system_prompt()
        
        # Add context if available
        if context:
            messages.insert(0, {
                "role": "system",
                "content": f"Context: {context}"
            })
        
        stream = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "system", "content": system_prompt}] + messages,
            stream=True,
            temperature=0.7,
            max_tokens=2000
        )
        
        def generate():
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield f"data: {chunk.choices[0].delta.content}\n\n"
            yield "data: [DONE]\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream"
        )
```

### 6.2 RAG Implementation

```python
# services/rag_service.py
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

class RAGService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.documents = []
    
    def add_document(self, text, metadata):
        # Generate embedding
        embedding = self.model.encode(text)
        
        # Store in vector database
        if self.index is None:
            self.index = faiss.IndexFlatL2(embedding.shape[0])
        
        self.index.add(np.array([embedding]))
        self.documents.append({
            'text': text,
            'metadata': metadata
        })
    
    def search(self, query, k=5):
        query_embedding = self.model.encode(query)
        distances, indices = self.index.search(
            np.array([query_embedding]), k
        )
        
        results = []
        for idx in indices[0]:
            if idx < len(self.documents):
                results.append(self.documents[idx])
        
        return results
```

### 6.3 Redis Caching Strategy

```python
# utils/cache.py
import redis
import json
from functools import wraps

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)

def cache_result(expiration=3600):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            redis_client.setex(
                cache_key,
                expiration,
                json.dumps(result)
            )
            
            return result
        return wrapper
    return decorator
```

## 7. Testing Strategy

### 7.1 Unit Tests
- Test each service method independently
- Mock external dependencies (OpenAI, Redis)
- Test database models and queries

### 7.2 Integration Tests
- Test API endpoints with test database
- Test file upload and processing
- Test authentication flow

### 7.3 End-to-End Tests
- Test complete user flows
- Test admin workflows
- Test error handling

### 7.4 Performance Tests
- Test concurrent users
- Test large file uploads
- Test response times

## 8. Security Measures

1. **Authentication**: JWT tokens with expiration
2. **Rate Limiting**: 100 requests per hour per user
3. **File Validation**: Check file types and sizes
4. **SQL Injection Prevention**: Use parameterized queries
5. **XSS Prevention**: Sanitize all user inputs
6. **CORS Configuration**: Restrict to your domain
7. **Environment Variables**: Never commit secrets

## 9. Deployment Checklist

- [ ] Set up production MySQL database
- [ ] Configure Redis for production
- [ ] Set environment variables
- [ ] Configure Nginx reverse proxy
- [ ] Set up SSL certificates
- [ ] Configure file upload limits
- [ ] Set up logging and monitoring
- [ ] Create backup strategy
- [ ] Test all features in production environment
- [ ] Create user documentation