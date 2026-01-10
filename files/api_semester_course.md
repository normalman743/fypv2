# 学期与课程管理 API

## 学期管理

### GET /api/v1/semesters
- 获取学期列表

**响应：**
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
        "is_active": true
      }
    ]
  }
}
```

### POST /api/v1/semesters
- 创建学期（admin）

**请求体：**
```json
{
  "name": "2025第三学期",
  "code": "2025S3",
  "start_date": "2025-09-01T00:00:00Z",
  "end_date": "2025-12-31T23:59:59Z"
}
```
**响应：**
```json
{
  "success": true,
  "data": {
    "semester": {
      "id": 3,
      "created_at": "2025-06-10T10:30:00Z"
    }
  }
}
```

### PUT /api/v1/semesters/{id}
- 更新学期（admin）

**请求体：**
```json
{
  "name": "2025第三学期-更新",
  "start_date": "2025-09-01T00:00:00Z",
  "end_date": "2025-12-31T23:59:59Z",
  "is_active": true
}
```
**响应：**
```json
{
  "success": true,
  "data": {
    "semester": {
      "id": 3,
      "updated_at": "2025-06-11T10:30:00Z"
    }
  }
}
```

### GET /api/v1/semesters/{id}
- 获取学期详情

**响应：**
```json
{
  "success": true,
  "data": {
    "semester": {
      "id": 3,
      "name": "2025第三学期",
      "code": "2025S3",
      "start_date": "2025-09-01T00:00:00Z",
      "end_date": "2025-12-31T23:59:59Z",
      "is_active": true,
      "created_at": "2025-06-10T10:30:00Z"
    }
  }
}
```

### DELETE /api/v1/semesters/{id}
- 删除学期（admin）

**响应：**
```json
{
  "success": true
}
```

### GET /api/v1/semesters/{id}/courses
- 获取学期下的所有课程

**响应：**
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

---

## 课程管理

### GET /api/v1/courses
- 获取课程列表

**请求参数：**
- semester_id: int (可选)

**响应：**
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
- 创建课程

**请求体：**
```json
{
  "name": "数据结构与算法",
  "code": "计算机科学1101A",
  "description": "学习各种数据结构和算法",
  "semester_id": 3
}
```
**响应：**
```json
{
  "success": true,
  "data": {
    "course": {
      "id": 3,
      "created_at": "2025-06-10T10:30:00Z"
    }
  }
}
```

### PUT /api/v1/courses/{id}
- 更新课程

**请求体：**
```json
{
  "name": "新课程名称",
  "description": "新描述"
}
```
**响应：**
```json
{
  "success": true,
  "data": {
    "course": {
      "id": 3,
      "updated_at": "2025-06-11T10:30:00Z"
    }
  }
}
```

### GET /api/v1/courses/{id}
- 获取课程详情

**响应：**
```json
{
  "success": true,
  "data": {
    "course": {
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
  }
}
```

### DELETE /api/v1/courses/{id}
- 删除课程

**响应：**
```json
{
  "success": true
}
```
