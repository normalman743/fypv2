# 聊天、消息与AI功能 API

## 聊天管理

### GET /api/v1/chats
- 获取聊天列表

**响应：**
```json
{
  "success": true,
  "data": {
    "chats": [
      {
        "id": 1,
        "title": "通用学习讨论",
        "chat_type": "general",
        "course_id": null,
        "user_id": 2,
        "custom_prompt": null,
        "created_at": "2025-06-10T09:00:00Z",
        "updated_at": "2025-06-10T10:25:00Z",
        "course": null,
        "stats": {
          "message_count": 8
        }
      },
      {
        "id": 2,
        "title": "数据结构讨论",
        "chat_type": "course",
        "course_id": 3,
        "user_id": 2,
        "custom_prompt": null,
        "created_at": "2025-06-10T09:30:00Z",
        "updated_at": "2025-06-10T11:15:00Z",
        "course": {
          "id": 3,
          "name": "数据结构与算法",
          "code": "CS201"
        },
        "stats": {
          "message_count": 12
        }
      }
    ]
  }
}
```
### POST /api/v1/chats
- 创建聊天（无需显式提供标题，可以包含首条消息和文件）

**请求体：**
```json
{
    "chat_type": "general",
    "first_message": "崇基学院体育馆的开放时间是什么时候",
    "course_id": null,
    "custom_prompt": null,
    "file_ids": [1, 2]
}
```
或课程相关聊天：
```json
{
    "chat_type": "course",
    "first_message": "这节课讲了什么",
    "course_id": 3,
    "custom_prompt": null,
    "file_ids": [3]
}
```
**响应（SSE流）：**
```
event: message
data: {"id": "msg_1", "type": "chat_created", "chat": {"id": 4, "title": "新聊天", "chat_type": "general", "course_id": null, "user_id": 2, "custom_prompt": null, "created_at": "2025-06-10T10:30:00Z", "updated_at": "2025-06-10T10:30:00Z"}}

event: message
data: {"id": "msg_2", "type": "user_message", "message": {"id": 5, "chat_id": 4, "content": "崇基学院体育馆的开放时间是什么时候", "role": "user", "created_at": "2025-06-10T10:30:00Z", "file_attachments": [{"id": 1, "filename": "20250610_abc123.pdf", "original_name": "campus_map.pdf", "file_size": 102400}]}}

event: message
data: {"id": "msg_3", "type": "ai_start", "message_id": 6}

event: message
data: {"id": "msg_4", "type": "ai_content", "delta": "崇基学院体育馆的开放时间是"}

event: message
data: {"id": "msg_5", "type": "ai_content", "delta": "周一至周五上午9点至晚上10点，"}

event: message
data: {"id": "msg_6", "type": "ai_content", "delta": "周末和节假日为上午10点至晚上8点。"}

event: message
data: {"id": "msg_7", "type": "ai_content", "delta": "请注意，体育馆可能会因学校活动临时关闭，建议您在前往前查看最新的通知。"}

event: message
data: {"id": "msg_8", "type": "ai_sources", "sources": [{"source_file": "校园设施指南.pdf", "chunk_id": 25}, {"source_file": "campus_map.pdf", "chunk_id": 7}]}

event: message
data: {"id": "msg_9", "type": "ai_end", "tokens_used": 120, "cost": 0.00024, "chat_title_updated": true, "new_chat_title": "崇基学院体育馆开放时间"}
```

**非流式备用响应：**
```json
{
    "success": true,
    "data": {
        "chat": {
            "id": 4,
            "title": "新聊天", // 初始标题，会在首次响应后自动更新
            "chat_type": "general",
            "course_id": null,
            "user_id": 2,
            "custom_prompt": null,
            "created_at": "2025-06-10T10:30:00Z",
            "updated_at": "2025-06-10T10:30:00Z"
        },
        "user_message": {
            "id": 5,
            "chat_id": 4,
            "content": "崇基学院体育馆的开放时间是什么时候",
            "role": "user",
            "tokens_used": null,
            "cost": null,
            "created_at": "2025-06-10T10:30:00Z",
            "file_attachments": [
                {
                    "id": 1,
                    "filename": "20250610_abc123.pdf",
                    "original_name": "campus_map.pdf",
                    "file_size": 102400
                }
            ]
        },
        "ai_message": {
            "id": 6,
            "chat_id": 4,
            "content": "崇基学院体育馆的开放时间是周一至周五上午9点至晚上10点，周末和节假日为上午10点至晚上8点。请注意，体育馆可能会因学校活动临时关闭，建议您在前往前查看最新的通知。",
            "role": "assistant",
            "tokens_used": 120,
            "cost": 0.00024,
            "created_at": "2025-06-10T10:30:05Z",
            "rag_sources": [
                {
                    "source_file": "校园设施指南.pdf",
                    "chunk_id": 25
                },
                {
                    "source_file": "campus_map.pdf",
                    "chunk_id": 7
                }
            ],
            "file_attachments": []
        },
        "chat_title_updated": true,
        "new_chat_title": "崇基学院体育馆开放时间"
    }
}
```

### PUT /api/v1/chats/{id}
- 更新聊天

**请求体：**
```json
{
  "title": "新的聊天标题"
}
```
**响应：**
```json
{
  "success": true,
  "data": {
    "chat": {
      "id": 4,
      "title": "新的聊天标题",
      "updated_at": "2025-06-10T10:35:00Z"
    }
  }
}
```

### DELETE /api/v1/chats/{id}
- 删除聊天

**响应：**
```json
{
  "success": true
}
```

---

## 消息管理

### GET /api/v1/chats/{id}/messages
- 获取消息列表

**响应：**
```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": 1,
        "chat_id": 2,
        "content": "什么是二叉树？",
        "role": "user",
        "tokens_used": null,
        "cost": null,
        "created_at": "2025-06-10T10:15:00Z",
        "file_attachments": []
      },
      {
        "id": 2,
        "chat_id": 2,
        "content": "二叉树是一种树形数据结构，其中每个节点最多有两个子节点，通常称为左子节点和右子节点...",
        "role": "assistant",
        "tokens_used": 150,
        "cost": 0.0003,
        "created_at": "2025-06-10T10:15:03Z",
        "rag_sources": [
          {
            "source_file": "数据结构第一讲.pdf",
            "chunk_id": 101
          }
        ],
        "file_attachments": []
      }
    ]
  }
}
```

### POST /api/v1/chats/{id}/messages
- 发送消息（自动触发AI流式回复，可带文件）

**请求体：**
```json
{
  "content": "什么是二叉树的遍历？",
  "file_ids": [1, 2]
}
```

**响应（SSE流）：**
```
event: message
data: {"id": "msg_1", "type": "user_message", "message": {"id": 3, "chat_id": 2, "content": "什么是二叉树的遍历？", "role": "user", "created_at": "2025-06-10T10:20:00Z", "file_attachments": [{"id": 1, "filename": "20250610_abc123.pdf", "original_name": "tree_notes.pdf", "file_size": 102400}]}}

event: message
data: {"id": "msg_2", "type": "ai_start", "message_id": 4}

event: message
data: {"id": "msg_3", "type": "ai_content", "delta": "二叉树的遍历是指"}

event: message
data: {"id": "msg_4", "type": "ai_content", "delta": "按照特定顺序访问二叉树中所有节点的过程。"}

event: message
data: {"id": "msg_5", "type": "ai_content", "delta": "主要有三种遍历方式：前序遍历、中序遍历和后序遍历。"}

event: message
data: {"id": "msg_6", "type": "ai_sources", "sources": [{"source_file": "数据结构第一讲.pdf", "chunk_id": 101}, {"source_file": "树形结构总结.md", "chunk_id": 52}]}

event: message
data: {"id": "msg_7", "type": "ai_end", "tokens_used": 200, "cost": 0.0004, "chat_title_updated": true, "new_chat_title": "关于二叉树的讨论"}
```

**非流式备用响应：**
```json
{
  "success": true,
  "data": {
    "user_message": {
      "id": 3,
      "chat_id": 2,
      "content": "什么是二叉树的遍历？",
      "role": "user",
      "tokens_used": null,
      "cost": null,
      "created_at": "2025-06-10T10:20:00Z",
      "file_attachments": [
        {
          "id": 1,
          "filename": "20250610_abc123.pdf",
          "original_name": "tree_notes.pdf",
          "file_size": 102400
        }
      ]
    },
    "ai_message": {
      "id": 4,
      "chat_id": 2,
      "content": "二叉树的遍历是指按照特定顺序访问二叉树中所有节点的过程。主要有三种遍历方式：前序遍历、中序遍历和后序遍历。",
      "role": "assistant",
      "tokens_used": 200,
      "cost": 0.0004,
      "created_at": "2025-06-10T10:20:03Z",
      "rag_sources": [
        {
          "source_file": "数据结构第一讲.pdf",
          "chunk_id": 101
        },
        {
          "source_file": "树形结构总结.md",
          "chunk_id": 52
        }
      ],
      "file_attachments": []
    },
    "chat_title_updated": true, // 如果是聊天的第一条消息，会自动更新聊天标题
    "new_chat_title": "关于二叉树的讨论" // 如果聊天标题被更新，返回新标题
  }
}
```

> **注意**：
> 1. 所有AI响应均为流式(stream)响应，支持实时显示生成内容
> 2. 所有AI回答都会自动使用RAG检索相关知识
> 3. 当发送聊天的第一条消息时，系统会自动生成一个合适的聊天标题

### PUT /api/v1/messages/{id}
- 编辑消息

**请求体：**
```json
{
  "content": "新的消息内容"
}
```
**响应：**
```json
{
  "success": true,
  "data": {
    "message": {
      "id": 3,
      "content": "新的消息内容",
      "updated_at": "2025-06-10T10:40:00Z"
    }
  }
}
```

### DELETE /api/v1/messages/{id}
- 删除消息

**响应：**
```json
{
  "success": true
}
```

---

## 聊天类型与RAG检索范围

聊天类型与RAG检索的默认行为:

| 聊天类型 | 检索范围 | 检索行为 |
|----------|----------|----------|
| general  | global   | 只检索全局知识库文件 |
| course   | course   | 优先检索课程相关文件，辅以全局知识库 |

这种设计使系统能够根据聊天的上下文自动选择最相关的知识源，提供更准确的回答。
