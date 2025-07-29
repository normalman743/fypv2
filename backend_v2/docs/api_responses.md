# API 响应设计文档

## 响应格式规范

### 成功响应
```json
{
  "success": true,
  "data": {},
  "message": "操作成功描述"
}
```

### 失败响应
```json
{
  "success": false,
  "error": "错误描述信息"
}
```

---

## 系统健康检查 / System Health Check

### GET /health
**成功 200:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2025-01-27T10:00:00Z"
  },
  "message": "系统运行正常"
}
```

**失败 503:**
```json
{
  "success": false,
  "error": "数据库连接失败"
}
```

---

## 用户认证 / Authentication

### POST /api/v1/auth/register
**请求体:**
```json
{
  "username": "alice",
  "email": "alice@example.com", 
  "password": "SecurePass123!",
  "invite_code": "INVITE2024"
}
```

**成功 201:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "username": "john_doe",
      "email": "john@584743.xyz",
      "role": "user",
      "balance": 1.0,
      "email_verified": false,
      "created_at": "2024-01-01T00:00:00Z"
    }
  },
  "message": "注册成功！验证邮件已发送，如果没有收到，请检查垃圾邮件或稍后再试。"
}
```

**失败 400:**
```json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "400 错误请求"
  }
}
```

**失败 403:**
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "403 禁止访问"
  }
}
```

**失败 409:**
```json
{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "409 冲突"
  }
}
```

### POST /api/v1/auth/login
**请求体:**
```json
{
  "username": "alice",
  "password": "SecurePass123!"
}
```

**成功 200:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "role": "user",
      "balance": 1.0,
      "email_verified": true
    }
  }
}
```

**失败 400:**
```json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "400 错误请求"
  }
}
```

**失败 401:**
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "401 未认证"
  }
}
```

### GET /api/v1/auth/me
**成功 200:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "role": "user",
    "balance": 0.0,
    "total_spent": 0.0,
    "preferred_language": "zh_CN",
    "preferred_theme": "light",
    "last_opened_semester_id": null,
    "created_at": "2025-01-27T10:00:00Z",
    "updated_at": "2025-01-27T10:00:00Z",
    "is_active": true,
    "email_verified": false,
    "last_login_at": null
  }
}
```

**失败 401:**
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "401 未认证"
  }
}
```

### PUT /api/v1/auth/me
**请求体:**
```json
{
  "username": "string",
  "preferred_language": "zh_CN",
  "preferred_theme": "light",
  "last_opened_semester_id": 0
}
```

**成功 200:**
```json
{
  "success": true,
  "data": {
    "id": 0,
    "username": "string",
    "email": "string",
    "role": "user",
    "balance": 0,
    "total_spent": 0,
    "preferred_language": "zh_CN",
    "preferred_theme": "light",
    "last_opened_semester_id": 0,
    "created_at": "2025-07-29T00:49:47.928Z",
    "updated_at": "2025-07-29T00:49:47.928Z",
    "is_active": true,
    "email_verified": false,
    "last_login_at": "2025-07-29T00:49:47.928Z"
  },
  "message": "string"
}
```

**失败 400:**
```json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "400 错误请求"
  }
}
```

**失败 403:**
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "403 禁止访问"
  }
}
```

**失败 409:**
```json
{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "409 冲突"
  }
}
```

### POST /api/v1/auth/logout
**成功 200:**
```json
{
  "success": true,
  "data": {
    "message": "操作成功"
  }
}
```

---

## 学期管理 / Semesters

### GET /api/v1/semesters
**成功 200:**
```json
{
  "success": true,
  "data": {
    "semesters": [
      {
        "id": 3,
        "name": "2025第三学期",
        "code": "2025S3",
        "start_date": "2025-09-01T00:00:00Z",
        "end_date": "2025-12-31T23:59:59Z",
        "is_active": true,
        "created_at": "2025-06-10T10:30:00Z"
      }
    ]
  }
}
```

### POST /api/v1/semesters
**请求体:**
```json
{
  "name": "2025第三学期",
  "code": "2025S3",
  "start_date": "2025-09-01T00:00:00Z",
  "end_date": "2025-12-31T23:59:59Z"
}
```

**成功 201:**
```json
{
  "success": true,
  "data": {
    "semester": {
      "id": 3,
      "created_at": "2025-06-10T10:30:00Z"
    }
  },
  "message": "学期创建成功"
}
```

**失败 400:**
```json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "400 错误请求"
  }
}
```

**失败 409:**
```json
{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "409 冲突"
  }
}
```

### PUT /api/v1/semesters/{semester_id}
**请求体:**
```json
{
  "name": "2025第三学期（修订）",
  "start_date": "2025-09-01T00:00:00Z",
  "end_date": "2025-12-31T23:59:59Z"
}
```

**成功 200:**
```json
{
  "success": true,
  "data": {
    "semester": {
      "id": 3,
      "updated_at": "2025-06-11T10:30:00Z"
    }
  },
  "message": "学期更新成功"
}
```

**失败 400:**
```json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "400 错误请求"
  }
}
```

**失败 404:**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "404 资源不存在"
  }
}
```

**失败 409:**
```json
{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "409 冲突"
  }
}
```

### DELETE /api/v1/semesters/{semester_id}
**成功 200:**
```json
{
  "success": true,
  "data": {},
  "message": "学期删除成功"
}
```

**失败 404:**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "404 资源不存在"
  }
}
```

**失败 409:**
```json
{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "409 冲突"
  }
}
```

---

## 课程管理 / Course Management

### GET /api/v1/courses
**成功 200:**
```json
{
  "success": true,
  "data": {
    "courses": [
      {
        "id": 1,
        "name": "数据结构与算法",
        "code": "计算机科学1101A",
        "description": "学习各种数据结构和算法",
        "semester_id": 3,
        "user_id": 2,
        "created_at": "2025-06-10T09:00:00Z",
        "semester": {
          "id": 3,
          "name": "2025第三学期",
          "code": "2025S3"
        },
        "stats": {
          "file_count": 5,
          "chat_count": 2
        }
      }
    ]
  }
}
```

### POST /api/v1/courses
**请求体:**
```json
{
  "name": "数据结构与算法",
  "code": "计算机科学1101A",
  "description": "学习各种数据结构和算法",
  "semester_id": 3
}
```

**成功 201:**
```json
{
  "success": true,
  "data": {
    "course": {
      "id": 3,
      "created_at": "2025-06-10T10:30:00Z"
    }
  },
  "message": "课程创建成功"
}
```

**失败 400:**
```json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "400 错误请求"
  }
}
```

**失败 409:**
```json
{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "409 冲突"
  }
}
```

### PUT /api/v1/courses/{course_id}
**请求体:**
```json
{
  "name": "数据结构与算法高级",
  "description": "更新的课程描述"
}
```

**成功 200:**
```json
{
  "success": true,
  "data": {
    "course": {
      "id": 3,
      "updated_at": "2025-06-11T10:30:00Z"
    }
  },
  "message": "课程更新成功"
}
```

**失败 400:**
```json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "400 错误请求"
  }
}
```

**失败 403:**
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "403 禁止访问"
  }
}
```

**失败 404:**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "404 资源不存在"
  }
}
```

**失败 409:**
```json
{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "409 冲突"
  }
}
```

### DELETE /api/v1/courses/{course_id}
**成功 200:**
```json
{
  "success": true,
  "data": {},
  "message": "课程删除成功"
}
```

**失败 403:**
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "403 禁止访问"
  }
}
```

**失败 404:**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "404 资源不存在"
  }
}
```

---

## 文件夹管理 / Folder Management

### GET /api/v1/courses/{course_id}/folders
**成功 200:**
```json
{
  "success": true,
  "data": {
    "folders": [
      {
        "id": 1,
        "name": "课程讲义",
        "folder_type": "lecture",
        "course_id": 1,
        "is_default": false,
        "created_at": "2025-01-27T10:00:00Z",
        "stats": {
          "file_count": 5
        }
      }
    ]
  }
}
```

**失败 404:**
```json
{
  "success": false,
  "error": "课程不存在"
}
```

### POST /api/v1/courses/{course_id}/folders
**请求体:**
```json
{
  "name": "作业提交",
  "folder_type": "assignment"
}
```

**成功 201:**
```json
{
  "success": true,
  "data": {
    "folder": {
      "id": 2,
      "created_at": "2025-01-27T10:00:00Z"
    }
  }
}
```

**失败 400:**
```json
{
  "success": false,
  "error": "文件夹名称已存在"
}
```

### PUT /api/v1/folders/{folder_id}
**请求体:**
```json
{
  "name": "课程讲义（更新）",
  "description": "更新的文件夹描述"
}
```

**成功 200:**
```json
{
  "success": true,
  "data": {
    "folder": {
      "id": 1,
      "name": "课程讲义（更新）",
      "updated_at": "2025-01-27T11:00:00Z"
    }
  }
}
```

**失败 404:**
```json
{
  "success": false,
  "error": "文件夹不存在"
}
```

### DELETE /api/v1/folders/{folder_id}
**成功 200:**
```json
{
  "success": true,
  "data": {}
}
```

**失败 409:**
```json
{
  "success": false,
  "error": "文件夹不为空，无法删除"
}
```

---

## 文件管理 / File Management

### POST /api/v1/files/upload
**请求体 (FormData):**
```
file: [File] - 要上传的文件
course_id: 1 - 课程ID
folder_id: 1 - 文件夹ID
```

**成功 200:**
```json
{
  "success": true,
  "data": {
    "file": {
      "id": 1,
      "original_name": "lecture01.pdf",
      "file_type": "pdf",
      "file_size": 1024000,
      "scope": "course",
      "course_id": 1,
      "folder_id": 1,
      "created_at": "2025-01-27T10:00:00Z"
    }
  }
}
```

**失败 413:**
```json
{
  "success": false,
  "error": "文件大小超过限制(10MB)"
}
```

**失败 415:**
```json
{
  "success": false,
  "error": "不支持的文件格式"
}
```

### GET /api/v1/folders/{folder_id}/files
**成功 200:**
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "id": 1,
        "original_name": "lecture01.pdf",
        "file_type": "pdf",
        "file_size": 1024000,
        "created_at": "2025-01-27T10:00:00Z"
      }
    ],
    "folder": {
      "id": 1,
      "name": "课程讲义"
    },
    "total": 1
  }
}
```

**失败 404:**
```json
{
  "success": false,
  "error": "文件夹不存在"
}
```

### GET /api/v1/files/{file_id}/download
**成功 200:** (文件流，无JSON响应)

**失败 404:**
```json
{
  "success": false,
  "error": "文件不存在"
}
```

**失败 403:**
```json
{
  "success": false,
  "error": "无权限访问该文件"
}
```

**失败 410:**
```json
{
  "success": false,
  "error": "临时文件已过期"
}
```

### DELETE /api/v1/files/{file_id}
**成功 200:**
```json
{
  "success": true,
  "data": {}
}
```

**失败 404:**
```json
{
  "success": false,
  "error": "文件不存在"
}
```

### POST /api/v1/files/temporary
**请求体 (FormData):**
```
file: [File] - 要上传的临时文件
expiry_hours: 24 - 过期时间（小时）(可选，默认24)
purpose: "chat_upload" - 用途说明 (可选)
```

**成功 200:**
```json
{
  "success": true,
  "data": {
    "file": {
      "id": 2,
      "original_name": "temp_image.jpg",
      "file_type": "jpg",
      "scope": "temporary",
      "expires_at": "2025-01-28T10:00:00Z",
      "created_at": "2025-01-27T10:00:00Z"
    }
  }
}
```

### POST /api/v1/global-files/upload
**请求体 (FormData):**
```
file: [File] - 要上传的全局文件
description: "系统政策文档" - 文件描述 (可选)
```

**成功 200:**
```json
{
  "success": true,
  "data": {
    "file": {
      "id": 3,
      "original_name": "global_policy.pdf",
      "file_type": "pdf",
      "scope": "global",
      "created_at": "2025-01-27T10:00:00Z"
    }
  }
}
```

**失败 403:**
```json
{
  "success": false,
  "error": "需要管理员权限"
}
```

### GET /api/v1/global-files
**成功 200:**
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "id": 3,
        "original_name": "global_policy.pdf",
        "file_type": "pdf",
        "scope": "global",
        "created_at": "2025-01-27T10:00:00Z"
      }
    ],
    "total": 1
  }
}
```

### DELETE /api/v1/global-files/{file_id}
**成功 200:**
```json
{
  "success": true,
  "data": {}
}
```

**失败 403:**
```json
{
  "success": false,
  "error": "需要管理员权限"
}
```

---

## 聊天管理 / Chat Management

### GET /api/v1/chats
**成功 200:**
```json
{
  "success": true,
  "data": {
    "chats": [
      {
        "id": 1,
        "title": "Python学习讨论",
        "chat_type": "course",
        "course_id": 1,
        "message_count": 5,
        "last_message_at": "2025-01-27T15:30:00Z",
        "created_at": "2025-01-27T10:00:00Z"
      }
    ],
    "total": 1
  }
}
```

### POST /api/v1/chats
**请求体:**
```json
{
  "title": "Python学习讨论",
  "chat_type": "course",
  "course_id": 1,
  "first_message": "请帮我学习Python基础语法",
  "ai_model": "StarPlus",
  "rag_enabled": true
}
```

**成功 200:**
```json
{
  "success": true,
  "data": {
    "chat": {
      "id": 2,
      "title": "新的讨论",
      "chat_type": "general",
      "created_at": "2025-01-27T10:00:00Z"
    }
  }
}
```

**失败 400:**
```json
{
  "success": false,
  "error": "课程聊天必须指定course_id"
}
```

### PUT /api/v1/chats/{chat_id}
**请求体:**
```json
{
  "title": "Python高级讨论",
  "ai_model": "StarCode",
  "rag_enabled": false
}
```

**成功 200:**
```json
{
  "success": true,
  "data": {
    "chat": {
      "id": 1,
      "title": "Python高级讨论",
      "updated_at": "2025-01-27T11:00:00Z"
    }
  }
}
```

**失败 404:**
```json
{
  "success": false,
  "error": "聊天不存在"
}
```

### DELETE /api/v1/chats/{chat_id}
**成功 200:**
```json
{
  "success": true,
  "data": {}
}
```

**失败 403:**
```json
{
  "success": false,
  "error": "只能删除自己的聊天"
}
```

---

## 消息管理 / Message Management

### GET /api/v1/chats/{chat_id}/messages
**成功 200:**
```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": 1,
        "chat_id": 1,
        "content": "请解释Python装饰器",
        "role": "user",
        "created_at": "2025-01-27T10:00:00Z"
      },
      {
        "id": 2,
        "chat_id": 1,
        "content": "装饰器是Python的高级特性...",
        "role": "assistant",
        "created_at": "2025-01-27T10:00:05Z"
      }
    ],
    "total": 2
  }
}
```

**失败 404:**
```json
{
  "success": false,
  "error": "聊天不存在"
}
```

### POST /api/v1/chats/{chat_id}/messages
**请求体:**
```json
{
  "content": "谢谢解答，还有其他问题",
  "file_ids": [1, 2],
  "stream": false
}
```

**成功 200:**
```json
{
  "success": true,
  "data": {
    "user_message": {
      "id": 3,
      "chat_id": 1,
      "content": "谢谢解答",
      "role": "user",
      "created_at": "2025-01-27T10:05:00Z"
    },
    "ai_message": {
      "id": 4,
      "chat_id": 1,
      "content": "不用客气，还有其他问题吗？",
      "role": "assistant",
      "created_at": "2025-01-27T10:05:03Z"
    }
  }
}
```

**失败 400:**
```json
{
  "success": false,
  "error": "消息内容不能为空"
}
```

### PUT /api/v1/messages/{message_id}
**请求体:**
```json
{
  "content": "请详细解释Python装饰器的用法"
}
```

**成功 200:**
```json
{
  "success": true,
  "data": {
    "message": {
      "id": 1,
      "content": "请详细解释Python装饰器",
      "is_edited": true,
      "updated_at": "2025-01-27T11:00:00Z"
    }
  }
}
```

**失败 403:**
```json
{
  "success": false,
  "error": "只能编辑自己的消息"
}
```

### DELETE /api/v1/messages/{message_id}
**成功 200:**
```json
{
  "success": true,
  "data": {}
}
```

**失败 404:**
```json
{
  "success": false,
  "error": "消息不存在"
}
```

---

## 管理员管理 / Admin Management

### POST /api/v1/invite-codes
**请求体:**
```json
{
  "description": "测试邀请码",
  "expires_at": "2025-12-31T23:59:59Z"
}
```

**成功 201:**
```json
{
  "success": true,
  "data": {
    "invite_code": {
      "id": 1,
      "code": "ABC12345",
      "description": "测试邀请码",
      "is_used": false,
      "expires_at": "2025-12-31T23:59:59Z",
      "is_active": true,
      "created_by": 1,
      "created_by_username": "admin",
      "created_at": "2025-01-27T10:00:00Z"
    }
  },
  "message": "邀请码创建成功"
}
```

**失败 400:**
```json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "400 错误请求"
  }
}
```

**失败 409:**
```json
{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "409 冲突"
  }
}
```

### GET /api/v1/invite-codes
**成功 200:**
```json
{
  "success": true,
  "data": {
    "invite_codes": [
      {
        "id": 1,
        "code": "ABC12345",
        "description": "测试邀请码",
        "is_used": false,
        "expires_at": "2025-12-31T23:59:59Z",
        "is_active": true,
        "created_by": 1,
        "created_by_username": "admin",
        "created_at": "2025-01-27T10:00:00Z"
      }
    ],
    "total": 1,
    "pagination": {
      "skip": 0,
      "limit": 100,
      "total": 1,
      "has_more": false
    }
  }
}
```

### PUT /api/v1/invite-codes/{invite_code_id}
**请求体:**
```json
{
  "description": "更新的邀请码描述",
  "expires_at": "2025-03-31T23:59:59Z",
  "is_active": false
}
```

**成功 200:**
```json
{
  "success": true,
  "data": {
    "invite_code": {
      "id": 1,
      "code": "ABC12345",
      "description": "更新的邀请码描述",
      "updated_at": "2025-01-27T11:00:00Z"
    }
  },
  "message": "邀请码更新成功"
}
```

**失败 404:**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "404 资源不存在"
  }
}
```

### DELETE /api/v1/invite-codes/{invite_code_id}
**成功 200:**
```json
{
  "success": true,
  "data": {
    "message": "操作成功"
  },
  "message": "操作成功"
}
```

**失败 404:**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "404 资源不存在"
  }
}
```

**失败 409:**
```json
{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "409 冲突"
  }
}
```