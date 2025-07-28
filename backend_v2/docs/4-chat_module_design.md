# Chat 模块技术设计文档 💬

## 概述

Chat模块是Campus LLM System v2的核心对话管理模块，负责聊天会话、消息管理和AI对话集成。基于v1版本的成熟功能设计，采用FastAPI 2024最佳实践，提供流式对话、文件附件、RAG集成和多模型支持的完整聊天解决方案。

## 📋 业务需求分析

### 聊天会话管理
- **会话CRUD**: 创建、查询、更新、删除聊天会话
- **会话类型**: general(通用聊天)、course(课程聊天)两种类型
- **会话配置**: AI模型选择、上下文模式、RAG开关、搜索功能
- **会话统计**: 消息数量、token消耗、成本统计

### 消息管理功能
- **消息CRUD**: 发送、查询、编辑、删除消息
- **消息类型**: user(用户)、assistant(AI助手)、system(系统)三种角色
- **文件附件**: 支持文件引用和临时文件上传
- **流式对话**: 支持Server-Sent Events的实时流式响应

### AI集成功能
- **多模型支持**: Star、StarPlus、StarCode三种AI模型
- **上下文管理**: Economy/Standard/Premium/Max四种上下文模式
- **RAG集成**: 文档检索增强生成，支持课程文件和全局文件
- **成本追踪**: Token使用、响应时间、成本计算

### 高级功能
- **文件引用**: 支持直接文件引用和文件夹批量引用
- **临时文件**: 支持聊天中的临时文件上传和引用
- **搜索功能**: 可选的联网搜索增强
- **自定义提示**: 支持用户自定义系统提示词

## 🗄️ 数据模型设计

### 1. Chat 模型（基于v1扩展）
```python
class Chat(Base):
    __tablename__ = "chats"
    
    # === 基础字段 ===
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    chat_type = Column(String(20), nullable=False, index=True)  # 'general', 'course'
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    custom_prompt = Column(Text, nullable=True)
    
    # === AI模型配置 ===
    ai_model = Column(String(20), nullable=False, default='Star', index=True)  # 'Star', 'StarPlus', 'StarCode'
    search_enabled = Column(Boolean, nullable=False, default=False)
    
    # === 对话配置 ===
    context_mode = Column(String(20), nullable=False, default='Standard', index=True)  # Economy/Standard/Premium/Max
    max_context_messages = Column(Integer, nullable=True)  # 根据context_mode自动设置
    
    # === RAG配置 ===
    rag_enabled = Column(Boolean, default=True)
    rag_file_scope = Column(String(20), default='course')  # course, global, all
    rag_similarity_threshold = Column(DECIMAL(3, 2), default=0.7)  # 相似度阈值
    
    # === 会话状态 ===
    is_active = Column(Boolean, default=True, index=True)
    is_pinned = Column(Boolean, default=False)  # 置顶功能
    last_message_at = Column(DateTime, nullable=True, index=True)  # 最后消息时间
    
    # === 统计字段 ===
    message_count = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    total_cost = Column(DECIMAL(20, 8), default=0.00)
    
    # === 时间戳 ===
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), index=True)
    
    # === 复合索引 ===
    __table_args__ = (
        Index('idx_user_type_updated', user_id, chat_type, updated_at.desc()),
        Index('idx_course_active', course_id, is_active),
        Index('idx_user_pinned_active', user_id, is_pinned, is_active),
    )
    
    # === 关系定义 ===
    course = relationship("Course", back_populates="chats")
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan",
                           order_by="Message.created_at")
```

### 2. Message 模型（基于v1扩展）
```python
class Message(Base):
    __tablename__ = "messages"
    
    # === 基础字段 ===
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False, index=True)  # 'user', 'assistant', 'system'
    
    # === 消息元数据 ===
    message_type = Column(String(20), default='text')  # text, image, file, system
    parent_message_id = Column(Integer, ForeignKey("messages.id"), nullable=True, index=True)  # 消息链
    is_edited = Column(Boolean, default=False)
    edit_count = Column(Integer, default=0)
    
    # === AI相关字段 ===
    model_name = Column(String(50), nullable=True, index=True)
    model_version = Column(String(20), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    cost = Column(DECIMAL(20, 8), nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # === RAG相关 ===
    rag_sources = Column(JSON, nullable=True)  # RAG检索源信息
    rag_query = Column(Text, nullable=True)  # RAG查询文本
    rag_source_count = Column(Integer, default=0)
    
    # === 上下文统计字段 ===
    context_size = Column(Integer, nullable=True)  # 上下文token数
    direct_file_count = Column(Integer, default=0)  # 直接引用文件数
    context_file_count = Column(Integer, default=0)  # 上下文中的文件数
    
    # === 消息状态 ===
    is_deleted = Column(Boolean, default=False, index=True)  # 软删除
    deleted_at = Column(DateTime, nullable=True)
    
    # === 时间戳 ===
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # === 复合索引 ===
    __table_args__ = (
        Index('idx_chat_role_created', chat_id, role, created_at),
        Index('idx_chat_not_deleted', chat_id, is_deleted),
    )
    
    # === 关系定义 ===
    chat = relationship("Chat", back_populates="messages")
    parent_message = relationship("Message", remote_side=[id])
    child_messages = relationship("Message", back_populates="parent_message")
    file_references = relationship("MessageFileReference", back_populates="message", cascade="all, delete-orphan")
    rag_sources_tracked = relationship("MessageRAGSource", back_populates="message", cascade="all, delete-orphan")
```

### 3. MessageFileReference 模型（文件引用）
```python
class MessageFileReference(Base):
    __tablename__ = "message_file_references"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=True, index=True)  # 永久文件
    temporary_file_id = Column(Integer, ForeignKey("temporary_files.id"), nullable=True, index=True)  # 临时文件
    
    # === 引用类型 ===
    reference_type = Column(String(20), nullable=False)  # direct, folder_batch, temporary
    file_purpose = Column(String(50), nullable=True)  # context, attachment, rag_source
    
    # === 引用状态 ===
    is_accessible = Column(Boolean, default=True)  # 文件是否可访问
    access_error = Column(String(200), nullable=True)  # 访问错误信息
    
    # === 时间戳 ===
    created_at = Column(DateTime, server_default=func.now())
    
    # === 关系定义 ===
    message = relationship("Message", back_populates="file_references")
    file = relationship("File", back_populates="message_references")
    temporary_file = relationship("TemporaryFile", back_populates="message_references")
```

### 4. MessageRAGSource 模型（RAG源追踪）
```python
class MessageRAGSource(Base):
    __tablename__ = "message_rag_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    document_chunk_id = Column(Integer, ForeignKey("document_chunks.id"), nullable=False, index=True)
    
    # === RAG检索信息 ===
    similarity_score = Column(DECIMAL(5, 4), nullable=False)  # 相似度得分
    chunk_rank = Column(Integer, nullable=False)  # 在检索结果中的排名
    query_text = Column(Text, nullable=True)  # 触发检索的查询文本
    
    # === 使用状态 ===
    is_used_in_context = Column(Boolean, default=True)  # 是否被使用在上下文中
    context_position = Column(Integer, nullable=True)  # 在上下文中的位置
    
    # === 时间戳 ===
    created_at = Column(DateTime, server_default=func.now())
    
    # === 关系定义 ===
    message = relationship("Message", back_populates="rag_sources_tracked")
    document_chunk = relationship("DocumentChunk", back_populates="message_rag_sources")
```

### 5. ❌ ChatSession 模型（已移除）
```python
# ⚠️ 根据架构优化，ChatSession模型已移除
# 原因：会话状态管理改用Redis缓存实现，提高性能和简化架构
# 
# 替代方案：
# - 用户在线状态 -> Redis缓存 (user:online:{user_id})
# - 聊天活跃状态 -> Redis缓存 (chat:active:{chat_id}:{user_id})
# - 会话令牌管理 -> JWT + Redis黑名单
# - 实时活动追踪 -> WebSocket连接管理

# 移除的数据库字段同样使用Redis管理：
REDIS_KEYS = {
    "user_online": "user:online:{user_id}",           # TTL: 30分钟
    "chat_active": "chat:active:{chat_id}:{user_id}", # TTL: 1小时  
    "typing_status": "typing:{chat_id}:{user_id}",    # TTL: 10秒
    "session_info": "session:{session_token}",        # TTL: 24小时
}
```

### Redis缓存会话管理设计
```python
class ChatSessionManager:
    """Redis-based聊天会话管理"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.USER_ONLINE_TTL = 1800    # 30分钟
        self.CHAT_ACTIVE_TTL = 3600    # 1小时
        self.TYPING_TTL = 10           # 10秒
    
    def mark_user_online(self, user_id: int):
        """标记用户在线"""
        key = f"user:online:{user_id}"
        self.redis.setex(key, self.USER_ONLINE_TTL, "active")
    
    def is_user_online(self, user_id: int) -> bool:
        """检查用户是否在线"""
        key = f"user:online:{user_id}"
        return self.redis.exists(key)
    
    def mark_chat_active(self, chat_id: int, user_id: int):
        """标记聊天活跃状态"""
        key = f"chat:active:{chat_id}:{user_id}"
        activity_data = {
            "last_seen": int(time.time()),
            "chat_id": chat_id,
            "user_id": user_id
        }
        self.redis.setex(key, self.CHAT_ACTIVE_TTL, json.dumps(activity_data))
    
    def set_typing_status(self, chat_id: int, user_id: int, is_typing: bool):
        """设置打字状态"""
        key = f"typing:{chat_id}:{user_id}"
        if is_typing:
            self.redis.setex(key, self.TYPING_TTL, "typing")
        else:
            self.redis.delete(key)
    
    def get_chat_active_users(self, chat_id: int) -> List[int]:
        """获取聊天中的活跃用户"""
        pattern = f"chat:active:{chat_id}:*"
        keys = self.redis.keys(pattern)
        active_users = []
        for key in keys:
            user_id = key.decode().split(':')[-1]
            active_users.append(int(user_id))
        return active_users
```

## 🚀 API 接口设计

### 路由前缀和标签
- **前缀**: `/chat`
- **标签**: `["聊天对话"]` (在 main.py 中设置)
- **权限**: 基于用户认证和聊天所有权的权限控制

### 聊天会话接口

#### 1. GET /api/v1/chat/chats - 获取聊天列表
```python
# 兼容v1 API: GET /chats
Query Parameters:
- chat_type?: str (过滤聊天类型: general, course)
- course_id?: int (过滤特定课程)
- limit?: int = 50
- offset?: int = 0
- include_inactive?: bool = false

Response 200: ChatListResponse
{
  "success": true,
  "data": {
    "chats": [
      {
        "id": 1,
        "title": "Python编程问题讨论",
        "chat_type": "course",
        "course_id": 1,
        "user_id": 1,
        "custom_prompt": "你是一个Python编程助手",
        "ai_model": "StarPlus",
        "search_enabled": false,
        "context_mode": "Standard",
        "rag_enabled": true,
        "is_active": true,
        "is_pinned": false,
        "message_count": 25,
        "total_tokens_used": 15000,
        "total_cost": 0.045,
        "last_message_at": "2025-01-27T15:30:00Z",
        "created_at": "2025-01-27T10:00:00Z",
        "updated_at": "2025-01-27T15:30:00Z",
        "course": {
          "id": 1,
          "name": "Python编程基础",
          "code": "CS101"
        },
        "stats": {
          "message_count": 25,
          "avg_response_time": 1200,
          "user_satisfaction": 4.5
        }
      }
    ],
    "total": 10,
    "pagination": {
      "limit": 50,
      "offset": 0,
      "has_more": false
    }
  }
}
```

#### 2. POST /api/v1/chat/chats - 创建聊天会话
```python
# 兼容v1 API: POST /chats
Request: CreateChatRequest
{
  "chat_type": "course",
  "course_id": 1,
  "first_message": "请帮我解释Python的装饰器概念",
  "custom_prompt": "你是一个专业的Python编程导师",
  "ai_model": "StarPlus",
  "search_enabled": false,
  "context_mode": "Standard",
  "rag_enabled": true,
  "file_ids": [1, 2, 3],
  "folder_ids": [1],
  "temporary_file_tokens": ["temp-uuid-1"],
  "stream": false
}

Response 201: CreateChatResponse
{
  "success": true,
  "data": {
    "chat": {
      "id": 1,
      "title": "Python装饰器讨论",  // AI自动生成
      "chat_type": "course",
      "course_id": 1,
      "user_id": 1,
      "ai_model": "StarPlus",
      "context_mode": "Standard",
      "created_at": "2025-01-27T10:00:00Z"
    },
    "user_message": {
      "id": 1,
      "chat_id": 1,
      "content": "请帮我解释Python的装饰器概念",
      "role": "user",
      "created_at": "2025-01-27T10:00:00Z",
      "file_attachments": [
        {
          "id": 1,
          "filename": "decorators.py",
          "original_name": "decorators_example.py",
          "file_size": 2048
        }
      ]
    },
    "ai_message": {
      "id": 2,
      "chat_id": 1,
      "content": "Python装饰器是一种设计模式...",
      "role": "assistant",
      "model_name": "StarPlus",
      "tokens_used": 450,
      "input_tokens": 200,
      "output_tokens": 250,
      "cost": 0.0045,
      "response_time_ms": 1200,
      "rag_sources": [
        {
          "file_name": "python_advanced.pdf",
          "chunk_id": 15,
          "similarity_score": 0.85,
          "content_preview": "装饰器是Python中的高级特性..."
        }
      ],
      "created_at": "2025-01-27T10:00:05Z"
    },
    "chat_title_updated": true,
    "new_chat_title": "Python装饰器讨论"
  },
  "message": "聊天创建成功"
}

# 流式响应模式 (stream: true)
Response: Server-Sent Events
Content-Type: text/event-stream

data: {"type": "chat_created", "chat": {...}}

data: {"type": "user_message", "message": {...}}

data: {"type": "ai_message_start", "message_id": 2}

data: {"type": "ai_message_delta", "content": "Python装饰器"}

data: {"type": "ai_message_delta", "content": "是一种设计模式"}

data: {"type": "ai_message_complete", "message": {...}, "usage": {...}}

data: {"type": "rag_sources", "sources": [...]}

data: [DONE]

Errors: 400(参数错误), 403(课程权限不足), 409(模型不可用)
```

#### 3. PUT /api/v1/chat/chats/{chat_id} - 更新聊天会话
```python
# 兼容v1 API: PUT /chats/{chat_id}
Request: UpdateChatRequest
{
  "title": "新的聊天标题",
  "custom_prompt": "更新的系统提示",
  "ai_model": "StarCode",
  "context_mode": "Premium",
  "rag_enabled": false,
  "search_enabled": true,
  "is_pinned": true
}

Response 200: UpdateChatResponse
{
  "success": true,
  "data": {
    "chat": {
      "id": 1,
      "title": "新的聊天标题",
      "custom_prompt": "更新的系统提示",
      "ai_model": "StarCode",
      "context_mode": "Premium",
      "updated_at": "2025-01-27T11:00:00Z"
    }
  },
  "message": "聊天设置更新成功"
}
```

#### 4. DELETE /api/v1/chat/chats/{chat_id} - 删除聊天会话
```python
# 兼容v1 API: DELETE /chats/{chat_id}
Response 200: MessageResponse
{
  "success": true,
  "data": {"message": "聊天删除成功"}
}

Errors: 404(聊天不存在), 403(无删除权限)
```

### 消息管理接口

#### 1. GET /api/v1/chat/chats/{chat_id}/messages - 获取聊天消息
```python
# 兼容v1 API: GET /chats/{chat_id}/messages
Query Parameters:
- limit?: int = 50
- before_message_id?: int (分页加载)
- include_deleted?: bool = false
- role?: str (过滤消息角色)

Response 200: MessageListResponse
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": 1,
        "chat_id": 1,
        "content": "请帮我解释Python的装饰器",
        "role": "user",
        "message_type": "text",
        "is_edited": false,
        "edit_count": 0,
        "created_at": "2025-01-27T10:00:00Z",
        "file_attachments": [
          {
            "id": 1,
            "filename": "example.py",
            "original_name": "decorator_example.py",
            "file_size": 2048,
            "reference_type": "direct"
          }
        ]
      },
      {
        "id": 2,
        "chat_id": 1,
        "content": "Python装饰器是一种设计模式...",
        "role": "assistant",
        "message_type": "text",
        "model_name": "StarPlus",
        "model_version": "1.0",
        "tokens_used": 450,
        "input_tokens": 200,
        "output_tokens": 250,
        "cost": 0.0045,
        "response_time_ms": 1200,
        "context_size": 2000,
        "direct_file_count": 1,
        "rag_source_count": 2,
        "rag_sources": [
          {
            "file_name": "python_advanced.pdf",
            "chunk_id": 15,
            "similarity_score": 0.85,
            "content_preview": "装饰器是Python中的高级特性...",
            "rank": 1
          }
        ],
        "created_at": "2025-01-27T10:00:05Z"
      }
    ],
    "total": 25,
    "has_more": true,
    "next_before_id": 2
  }
}
```

#### 2. POST /api/v1/chat/chats/{chat_id}/messages - 发送消息
```python
# 兼容v1 API: POST /chats/{chat_id}/messages
Request: SendMessageRequest
{
  "content": "请继续解释装饰器的高级用法",
  "file_ids": [4, 5],
  "folder_ids": [2],
  "temporary_file_tokens": ["temp-uuid-2"],
  "stream": false
}

Response 200: SendMessageResponse
{
  "success": true,
  "data": {
    "user_message": {
      "id": 3,
      "chat_id": 1,
      "content": "请继续解释装饰器的高级用法",
      "role": "user",
      "created_at": "2025-01-27T10:05:00Z",
      "file_attachments": [...]
    },
    "ai_message": {
      "id": 4,
      "chat_id": 1,
      "content": "装饰器的高级用法包括...",
      "role": "assistant",
      "model_name": "StarPlus",
      "tokens_used": 680,
      "cost": 0.0068,
      "response_time_ms": 1500,
      "rag_sources": [...],
      "created_at": "2025-01-27T10:05:03Z"
    },
    "chat_title_updated": false,
    "context_trimmed": false,
    "tokens_before_trim": 2500
  },
  "message": "消息发送成功"
}

# 流式响应 (stream: true)
Response: Server-Sent Events
data: {"type": "user_message", "message": {...}}
data: {"type": "ai_message_start", "message_id": 4}
data: {"type": "ai_message_delta", "content": "装饰器的"}
data: {"type": "ai_message_delta", "content": "高级用法"}
data: {"type": "ai_message_complete", "message": {...}}
data: [DONE]
```

#### 3. PUT /api/v1/chat/messages/{message_id} - 编辑消息
```python
# 兼容v1 API: PUT /messages/{message_id}
Request: EditMessageRequest
{
  "content": "请详细解释Python装饰器的概念和用法"
}

Response 200: EditMessageResponse
{
  "success": true,
  "data": {
    "message": {
      "id": 1,
      "content": "请详细解释Python装饰器的概念和用法",
      "is_edited": true,
      "edit_count": 1,
      "updated_at": "2025-01-27T10:10:00Z"
    },
    "regenerate_required": true  // 是否需要重新生成AI响应
  },
  "message": "消息编辑成功"
}
```

#### 4. DELETE /api/v1/chat/messages/{message_id} - 删除消息
```python
# 兼容v1 API: DELETE /messages/{message_id}
Response 200: MessageResponse
{
  "success": true,
  "data": {"message": "消息删除成功"}
}
```

### 高级功能接口

#### 1. POST /api/v1/chat/chats/{chat_id}/regenerate - 重新生成AI响应
```python
Request: RegenerateRequest
{
  "message_id": 2,  // 要重新生成的AI消息ID
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false
}

Response 200: RegenerateResponse
{
  "success": true,
  "data": {
    "new_message": {
      "id": 5,
      "content": "重新生成的回复内容...",
      "model_name": "StarPlus",
      "tokens_used": 520,
      "created_at": "2025-01-27T10:15:00Z"
    },
    "replaced_message_id": 2
  }
}
```

#### 2. GET /api/v1/chat/chats/{chat_id}/context - 获取上下文信息
```python
Response 200: ChatContextResponse
{
  "success": true,
  "data": {
    "context_messages": [
      {
        "message_id": 1,
        "role": "user",
        "content": "请帮我解释Python的装饰器",
        "token_count": 20
      }
    ],
    "context_files": [
      {
        "file_id": 1,
        "file_name": "decorators.py",
        "include_reason": "direct_reference"
      }
    ],
    "rag_sources": [
      {
        "chunk_id": 15,
        "file_name": "python_advanced.pdf",
        "similarity_score": 0.85
      }
    ],
    "total_context_tokens": 2000,
    "max_context_tokens": 4000,
    "context_utilization": 0.5
  }
}
```

#### 3. GET /api/v1/chat/presence/online - 获取在线用户状态
```python
# 新增：替代ChatSession的在线状态查询
Response 200: OnlineUsersResponse
{
  "success": true,
  "data": {
    "online_users": [
      {
        "user_id": 1,
        "username": "alice",
        "last_seen": "2025-01-27T15:30:00Z",
        "status": "online"
      }
    ],
    "total_online": 5,
    "chat_active_users": {
      "chat_1": [1, 2, 3],
      "chat_5": [1, 4]
    }
  }
}
```

#### 4. POST /api/v1/chat/presence/typing - 设置打字状态
```python
# 新增：替代ChatSession的实时状态管理
Request: TypingStatusRequest
{
  "chat_id": 1,
  "is_typing": true
}

Response 200: TypingStatusResponse
{
  "success": true,
  "data": {
    "chat_id": 1,
    "user_id": 1,
    "is_typing": true,
    "expires_at": "2025-01-27T15:30:10Z"
  }
}
```

#### 5. GET /api/v1/chat/chats/{chat_id}/active-users - 获取聊天活跃用户
```python
# 新增：基于Redis的活跃用户查询
Response 200: ChatActiveUsersResponse
{
  "success": true,
  "data": {
    "chat_id": 1,
    "active_users": [
      {
        "user_id": 1,
        "username": "alice",
        "last_activity": "2025-01-27T15:29:45Z",
        "is_typing": false
      },
      {
        "user_id": 2,
        "username": "bob", 
        "last_activity": "2025-01-27T15:30:00Z",
        "is_typing": true
      }
    ],
    "total_active": 2
  }
}
```

#### 6. POST /api/v1/chat/chats/{chat_id}/export - 导出聊天记录
```python
Request: ExportChatRequest
{
  "format": "markdown",  // markdown, json, pdf
  "include_attachments": true,
  "include_rag_sources": false,
  "date_range": {
    "start": "2025-01-01T00:00:00Z",
    "end": "2025-01-31T23:59:59Z"
  }
}

Response 200: ExportChatResponse
{
  "success": true,
  "data": {
    "export_id": "export-uuid",
    "download_url": "/api/v1/chat/exports/export-uuid/download",
    "format": "markdown",
    "file_size": 1024000,
    "expires_at": "2025-01-28T10:00:00Z"
  }
}
```

## 📊 Schema 设计（FastAPI 2024最佳实践）

### 请求模型
```python
# === 聊天相关请求 ===
class CreateChatRequest(BaseModel):
    chat_type: Literal["general", "course"] = Field("general", description="聊天类型")
    course_id: Optional[int] = Field(None, gt=0, description="课程ID（course类型时必填）")
    first_message: str = Field(..., min_length=1, max_length=10000, description="首条消息")
    custom_prompt: Optional[str] = Field(None, max_length=2000, description="自定义系统提示")
    ai_model: Literal["Star", "StarPlus", "StarCode"] = Field("Star", description="AI模型")
    search_enabled: bool = Field(False, description="启用搜索功能")
    context_mode: Literal["Economy", "Standard", "Premium", "Max"] = Field("Standard", description="上下文模式")
    rag_enabled: bool = Field(True, description="启用RAG检索")
    file_ids: Optional[List[int]] = Field([], description="引用文件ID列表")
    folder_ids: Optional[List[int]] = Field([], description="引用文件夹ID列表")
    temporary_file_tokens: Optional[List[str]] = Field([], description="临时文件令牌列表")
    stream: bool = Field(False, description="启用流式响应")

    @field_validator('course_id')
    @classmethod
    def validate_course_id(cls, v, info):
        if info.data.get('chat_type') == 'course' and v is None:
            raise ValueError('课程聊天必须指定course_id')
        return v

class UpdateChatRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    custom_prompt: Optional[str] = Field(None, max_length=2000)
    ai_model: Optional[Literal["Star", "StarPlus", "StarCode"]] = None
    context_mode: Optional[Literal["Economy", "Standard", "Premium", "Max"]] = None
    rag_enabled: Optional[bool] = None
    search_enabled: Optional[bool] = None
    is_pinned: Optional[bool] = None

# === 消息相关请求 ===
class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000, description="消息内容")
    file_ids: Optional[List[int]] = Field([], description="引用文件ID列表")
    folder_ids: Optional[List[int]] = Field([], description="引用文件夹ID列表")
    temporary_file_tokens: Optional[List[str]] = Field([], description="临时文件令牌列表")
    stream: bool = Field(False, description="启用流式响应")
    parent_message_id: Optional[int] = Field(None, description="父消息ID（用于消息分支）")

class EditMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)

class RegenerateRequest(BaseModel):
    message_id: int = Field(..., gt=0, description="要重新生成的消息ID")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="生成温度")
    max_tokens: int = Field(1000, gt=0, le=4000, description="最大token数")
    stream: bool = Field(False, description="启用流式响应")

# === 导出请求 ===
class ExportChatRequest(BaseModel):
    format: Literal["markdown", "json", "pdf"] = Field("markdown", description="导出格式")
    include_attachments: bool = Field(True, description="包含附件")
    include_rag_sources: bool = Field(False, description="包含RAG源信息")
    date_range: Optional[Dict[str, datetime]] = Field(None, description="日期范围")
```

### 响应模型（遵循BaseResponse[T]模式）
```python
# === 聊天数据模型 ===
class ChatData(BaseModel):
    id: int
    title: str
    chat_type: Literal["general", "course"]
    course_id: Optional[int]
    user_id: int
    custom_prompt: Optional[str]
    ai_model: Literal["Star", "StarPlus", "StarCode"]
    search_enabled: bool
    context_mode: Literal["Economy", "Standard", "Premium", "Max"]
    rag_enabled: bool
    is_active: bool
    is_pinned: bool
    message_count: int
    total_tokens_used: int
    total_cost: Decimal
    last_message_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # 关联数据
    course: Optional[CourseBasicData] = None
    stats: Optional[ChatStatsData] = None

class ChatStatsData(BaseModel):
    message_count: int
    avg_response_time: float
    user_satisfaction: Optional[float]
    total_cost: Decimal
    most_used_model: str

# === 消息数据模型 ===
class MessageData(BaseModel):
    id: int
    chat_id: int
    content: str
    role: Literal["user", "assistant", "system"]
    message_type: str
    parent_message_id: Optional[int]
    is_edited: bool
    edit_count: int
    
    # AI相关字段
    model_name: Optional[str]
    model_version: Optional[str]
    tokens_used: Optional[int]
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    cost: Optional[Decimal]
    response_time_ms: Optional[int]
    
    # RAG相关
    rag_sources: Optional[List[RAGSourceData]]
    rag_query: Optional[str]
    rag_source_count: int
    
    # 上下文信息
    context_size: Optional[int]
    direct_file_count: int
    context_file_count: int
    
    # 时间信息
    created_at: datetime
    updated_at: Optional[datetime]
    
    # 附件信息
    file_attachments: List[FileAttachmentData] = []

class RAGSourceData(BaseModel):
    file_name: str
    chunk_id: int
    similarity_score: float
    content_preview: str
    rank: int
    file_type: str

class FileAttachmentData(BaseModel):
    id: int
    filename: str
    original_name: str
    file_size: int
    reference_type: str
    file_purpose: str

# === 响应模型 ===
class CreateChatResponse(BaseResponse[Dict]):
    # data.chat: ChatData, data.user_message: MessageData, data.ai_message: MessageData
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "success": True,
                "data": {
                    "chat": {
                        "id": 1,
                        "title": "Python装饰器讨论",
                        "chat_type": "course",
                        "ai_model": "StarPlus",
                        "created_at": "2025-01-27T10:00:00Z"
                    },
                    "user_message": {
                        "id": 1,
                        "content": "请解释装饰器",
                        "role": "user",
                        "created_at": "2025-01-27T10:00:00Z"
                    },
                    "ai_message": {
                        "id": 2,
                        "content": "装饰器是...",
                        "role": "assistant",
                        "tokens_used": 450,
                        "created_at": "2025-01-27T10:00:05Z"
                    }
                },
                "message": "聊天创建成功"
            }]
        }
    )

class ChatListResponse(BaseResponse[Dict]):
    # data.chats: List[ChatData], data.total: int, data.pagination: PaginationInfo

class MessageListResponse(BaseResponse[Dict]):
    # data.messages: List[MessageData], data.total: int, data.has_more: bool

class SendMessageResponse(BaseResponse[Dict]):
    # data.user_message: MessageData, data.ai_message: MessageData
```

## 🛠️ Service 层设计

### ChatService 类设计
```python
class ChatService:
    """聊天服务 - 会话管理和消息处理"""
    
    METHOD_EXCEPTIONS = {
        # 聊天管理
        'create_chat': {BadRequestError, ForbiddenError, ConflictError},
        'get_user_chats': set(),  # 用户只能看自己的聊天
        'get_chat': {NotFoundError, ForbiddenError},
        'update_chat': {NotFoundError, ForbiddenError, BadRequestError},
        'delete_chat': {NotFoundError, ForbiddenError},
        
        # 消息管理
        'send_message': {NotFoundError, ForbiddenError, BadRequestError},
        'get_chat_messages': {NotFoundError, ForbiddenError},
        'edit_message': {NotFoundError, ForbiddenError, BadRequestError},
        'delete_message': {NotFoundError, ForbiddenError},
        'regenerate_message': {NotFoundError, ForbiddenError, BadRequestError},
        
        # 高级功能
        'export_chat': {NotFoundError, ForbiddenError, BadRequestError},
        'get_chat_context': {NotFoundError, ForbiddenError},
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()  # AI模块集成
        self.rag_service = RAGService()  # RAG检索服务
```

### 核心业务方法示例
```python
def create_chat_with_first_message(
    self, 
    request: CreateChatRequest, 
    user_id: int
) -> Dict[str, Any]:
    """创建聊天并发送首条消息"""
    # 1. 权限检查
    if request.chat_type == 'course':
        if not self._can_access_course(user_id, request.course_id):
            raise ForbiddenError("无权限访问此课程")
    
    # 2. 创建聊天会话
    chat = Chat(
        title="新对话",  # 临时标题，后续AI生成
        chat_type=request.chat_type,
        course_id=request.course_id,
        user_id=user_id,
        custom_prompt=request.custom_prompt,
        ai_model=request.ai_model,
        search_enabled=request.search_enabled,
        context_mode=request.context_mode,
        rag_enabled=request.rag_enabled,
        max_context_messages=self._get_max_context_messages(request.context_mode)
    )
    
    self.db.add(chat)
    self.db.flush()  # 获取chat.id
    
    # 3. 创建用户消息
    user_message = Message(
        chat_id=chat.id,
        content=request.first_message,
        role='user',
        message_type='text'
    )
    
    self.db.add(user_message)
    
    # 4. 处理文件引用
    if request.file_ids or request.folder_ids or request.temporary_file_tokens:
        self._attach_files_to_message(
            user_message.id, 
            request.file_ids, 
            request.folder_ids, 
            request.temporary_file_tokens
        )
    
    # 5. 生成AI响应
    ai_context = self._build_ai_context(chat, user_message, request)
    ai_response = self.ai_service.generate_response(ai_context)
    
    ai_message = Message(
        chat_id=chat.id,
        content=ai_response.content,
        role='assistant',
        model_name=ai_response.model_name,
        tokens_used=ai_response.tokens_used,
        input_tokens=ai_response.input_tokens,
        output_tokens=ai_response.output_tokens,
        cost=ai_response.cost,
        response_time_ms=ai_response.response_time_ms,
        rag_sources=ai_response.rag_sources,
        context_size=ai_response.context_size
    )
    
    self.db.add(ai_message)
    
    # 6. 生成聊天标题
    if len(request.first_message) > 10:
        generated_title = self.ai_service.generate_chat_title(
            request.first_message, 
            ai_response.content
        )
        chat.title = generated_title[:200]  # 限制长度
    
    # 7. 更新统计
    chat.message_count = 2
    chat.total_tokens_used = ai_response.tokens_used
    chat.total_cost = ai_response.cost
    chat.last_message_at = ai_message.created_at
    
    self.db.commit()
    self.db.refresh(chat)
    self.db.refresh(user_message)
    self.db.refresh(ai_message)
    
    return {
        "chat": chat,
        "user_message": user_message,
        "ai_message": ai_message,
        "chat_title_updated": True,
        "new_chat_title": chat.title
    }

def send_message(
    self, 
    chat_id: int, 
    request: SendMessageRequest, 
    user_id: int
) -> Dict[str, Any]:
    """发送消息并获取AI响应"""
    # 1. 获取聊天并检查权限
    chat = self._get_chat_with_permission(chat_id, user_id)
    
    # 2. 检查上下文限制
    context_messages = self._get_context_messages(chat)
    if len(context_messages) >= chat.max_context_messages:
        # 执行上下文裁剪
        self._trim_context_messages(chat, context_messages)
    
    # 3. 创建用户消息
    user_message = Message(
        chat_id=chat_id,
        content=request.content,
        role='user',
        parent_message_id=request.parent_message_id
    )
    
    self.db.add(user_message)
    self.db.flush()
    
    # 4. 处理文件引用
    self._attach_files_to_message(
        user_message.id,
        request.file_ids,
        request.folder_ids, 
        request.temporary_file_tokens
    )
    
    # 5. 构建AI上下文
    ai_context = self._build_ai_context(chat, user_message, request)
    
    # 6. 生成AI响应
    ai_response = self.ai_service.generate_response(ai_context)
    
    ai_message = Message(
        chat_id=chat_id,
        content=ai_response.content,
        role='assistant',
        model_name=chat.ai_model,
        tokens_used=ai_response.tokens_used,
        input_tokens=ai_response.input_tokens,
        output_tokens=ai_response.output_tokens,
        cost=ai_response.cost,
        response_time_ms=ai_response.response_time_ms,
        rag_sources=ai_response.rag_sources,
        context_size=ai_response.context_size,
        parent_message_id=user_message.id
    )
    
    self.db.add(ai_message)
    
    # 7. 更新聊天统计
    chat.message_count += 2
    chat.total_tokens_used += ai_response.tokens_used
    chat.total_cost += ai_response.cost
    chat.last_message_at = ai_message.created_at
    
    self.db.commit()
    
    return {
        "user_message": user_message,
        "ai_message": ai_message,
        "chat_title_updated": False,
        "context_trimmed": len(context_messages) >= chat.max_context_messages
    }

def send_message_stream(
    self, 
    chat_id: int, 
    request: SendMessageRequest, 
    user_id: int
) -> Iterator[Dict[str, Any]]:
    """流式发送消息"""
    # 1. 创建用户消息（同上）
    chat = self._get_chat_with_permission(chat_id, user_id)
    user_message = self._create_user_message(chat_id, request)
    
    yield {
        "type": "user_message",
        "message": self._format_message_data(user_message)
    }
    
    # 2. 开始AI响应流
    ai_context = self._build_ai_context(chat, user_message, request)
    
    ai_message = Message(
        chat_id=chat_id,
        content="",  # 初始为空
        role='assistant',
        model_name=chat.ai_model
    )
    
    self.db.add(ai_message)
    self.db.flush()
    
    yield {
        "type": "ai_message_start",
        "message_id": ai_message.id
    }
    
    # 3. 流式生成内容
    full_content = ""
    for chunk in self.ai_service.generate_response_stream(ai_context):
        if chunk.type == "content_delta":
            full_content += chunk.content
            yield {
                "type": "ai_message_delta",
                "content": chunk.content
            }
        elif chunk.type == "usage":
            ai_message.tokens_used = chunk.tokens_used
            ai_message.input_tokens = chunk.input_tokens
            ai_message.output_tokens = chunk.output_tokens
            ai_message.cost = chunk.cost
            ai_message.response_time_ms = chunk.response_time_ms
    
    # 4. 完成消息
    ai_message.content = full_content
    self.db.commit()
    
    yield {
        "type": "ai_message_complete",
        "message": self._format_message_data(ai_message),
        "usage": {
            "tokens_used": ai_message.tokens_used,
            "cost": float(ai_message.cost or 0)
        }
    }
```

## 🔐 权限控制设计

### 权限模型
```python
# chat/dependencies.py
def get_chat_permission(
    action: str  # read, write, delete
) -> Callable:
    """聊天权限检查装饰器"""
    def permission_check(
        chat_id: int,
        current_user: UserDep,
        db: DbDep
    ) -> Chat:
        service = ChatService(db)
        chat = service.get_chat_with_permission(chat_id, current_user.id, action)
        return chat
    
    return permission_check

# 权限检查类型别名
ChatReadDep = Annotated[Chat, Depends(get_chat_permission("read"))]
ChatWriteDep = Annotated[Chat, Depends(get_chat_permission("write"))]
ChatDeleteDep = Annotated[Chat, Depends(get_chat_permission("delete"))]
```

### 权限检查逻辑
```python
def _check_chat_permission(self, chat: Chat, user_id: int, action: str) -> bool:
    """检查聊天权限"""
    # 1. 聊天所有者
    if chat.user_id == user_id:
        return True
    
    # 2. 课程聊天的课程成员权限
    if chat.chat_type == "course" and chat.course_id:
        if action == "read" and self._is_course_member(user_id, chat.course_id):
            return True
    
    # 3. 管理员权限
    if self._is_admin(user_id):
        return True
    
    return False

def _check_message_permission(self, message: Message, user_id: int, action: str) -> bool:
    """检查消息权限"""
    # 消息权限基于聊天权限
    return self._check_chat_permission(message.chat, user_id, action)
```

## 📁 文件系统结构

### 项目结构
```
src/chat/
├── __init__.py
├── models.py          # Chat, Message, MessageFileReference, MessageRAGSource (移除ChatSession)
├── schemas.py         # 请求/响应模型
├── service.py         # ChatService (统一聊天和消息管理)
├── router.py          # API 路由
├── dependencies.py    # 权限检查依赖
├── exceptions.py      # 聊天相关异常
├── utils.py          # 聊天工具函数
└── session_manager.py # Redis-based会话状态管理

src/chat/services/
├── __init__.py
├── message_processor.py    # 消息处理和格式化
├── context_manager.py      # 上下文管理和裁剪
├── stream_handler.py       # 流式响应处理
├── export_service.py       # 聊天导出功能
└── redis_session.py        # Redis会话管理服务

src/chat/websocket/
├── __init__.py
├── connection_manager.py   # WebSocket连接管理
├── typing_handler.py       # 实时打字状态
└── presence_tracker.py     # 用户在线状态追踪
```

## 🧪 测试策略

### 单元测试覆盖
```python
class TestChatService:
    """聊天服务单元测试"""
    
    def test_create_chat_success(self, chat_service, regular_user):
        """测试创建聊天成功"""
        
    def test_send_message_with_files(self, chat_service, sample_chat, test_files):
        """测试发送带文件的消息"""
        
    def test_context_trimming(self, chat_service, chat_with_many_messages):
        """测试上下文裁剪功能"""
        
    def test_rag_integration(self, chat_service, course_chat, course_files):
        """测试RAG集成功能"""

class TestChatAPI:
    """聊天API集成测试"""
    
    def test_create_chat_stream(self, client, user_headers):
        """测试流式创建聊天"""
        
    def test_send_message_stream(self, client, user_headers, sample_chat):
        """测试流式发送消息"""
        
    def test_chat_export(self, client, user_headers, chat_with_messages):
        """测试聊天导出功能"""
        
    def test_chat_permissions(self, client, user_headers, other_user_chat):
        """测试聊天权限控制"""
```

## 🚀 性能优化

### 消息加载优化
- **分页加载**: 按时间倒序分页加载消息
- **懒加载**: 附件和RAG源信息按需加载
- **缓存策略**: 最近聊天和消息缓存
- **索引优化**: chat_id+created_at复合索引

### 流式响应优化
- **WebSocket连接**: 长连接支持实时对话
- **压缩传输**: 消息内容压缩传输
- **断点续传**: 支持连接中断后恢复
- **并发控制**: 限制用户并发聊天数量

### AI集成优化
- **模型选择**: 根据任务复杂度自动选择模型
- **上下文优化**: 智能上下文裁剪和压缩
- **并行处理**: RAG检索和AI生成并行执行
- **结果缓存**: 相似问题的答案缓存

## 🔗 与其他模块的集成

### Storage 模块集成
- 文件附件管理
- 临时文件引用
- 文件权限验证
- 文件预览生成

### AI 模块集成
- 多模型调用
- RAG检索集成
- 流式响应处理
- 成本计算统计

### Course 模块集成
- 课程权限验证
- 课程文件访问
- 课程成员检查
- 课程统计更新

### Admin 模块集成
- 聊天审计日志
- 使用统计报告
- 异常监控告警
- 成本分析统计

## 📊 监控和统计

### 聊天统计
- 用户活跃度统计
- 消息数量分布
- AI模型使用统计
- 成本消耗分析

### 性能监控
- 消息响应时间
- AI生成延迟
- 流式传输性能
- 数据库查询优化

### 用户体验监控
- 对话满意度
- 功能使用频率
- 错误率统计
- 用户反馈收集

## 🎯 总结

Chat模块严格遵循FastAPI 2024最佳实践和Campus LLM System的架构标准：

- ✅ **Service API装饰器**: 自动生成完整的OpenAPI文档
- ✅ **统一响应格式**: BaseResponse[T]泛型设计，message/data分离
- ✅ **现代依赖注入**: 类型安全的权限控制
- ✅ **异常处理自动化**: METHOD_EXCEPTIONS声明
- ✅ **v1 API兼容**: 保持API路径和响应格式兼容
- ✅ **流式响应支持**: Server-Sent Events实时对话
- ✅ **完整测试覆盖**: 单元测试+API集成测试+流式测试
- ✅ **AI集成**: 多模型支持+RAG增强+成本追踪

### 🚀 架构优化亮点

- ⚡ **Redis会话管理**: 移除ChatSession数据库表，改用Redis缓存实现，提高性能
- 🔄 **实时状态追踪**: 基于Redis TTL的用户在线状态和打字状态管理
- 💾 **数据库简化**: 减少不必要的数据库表，专注于核心聊天和消息功能
- 🌐 **WebSocket集成**: 为实时通信和状态同步提供WebSocket支持基础

该模块为Campus LLM System提供了强大、灵活、高效的聊天对话解决方案，通过Redis缓存优化和架构简化，确保了更好的性能表现和系统可扩展性。