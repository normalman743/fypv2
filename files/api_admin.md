# 管理与系统 API

## 邀请码管理

### POST /api/v1/invite-codes
- 创建邀请码

**请求体：**
```json
{
  "description": "学生注册专用",
  "expires_at": "2025-12-31T23:59:59Z"
}
```
**响应：**
```json
{
  "success": true,
  "data": {
    "invite_code": {
      "id": 1,
      "code": "INVITE2025",
      "created_at": "2025-06-11T10:30:00Z"
    }
  }
}
```

### GET /api/v1/invite-codes
- 获取邀请码列表

**响应：**
```json
{
  "success": true,
  "data": {
    "invite_codes": [
      {
        "id": 1,
        "code": "INVITE2025",
        "description": "学生注册专用",
        "is_used": false,
        "expires_at": "2025-12-31T23:59:59Z",
        "created_at": "2025-06-11T10:30:00Z"
      }
    ]
  }
}
```

### PUT /api/v1/invite-codes/{id}
- 更新邀请码

**请求体：**
```json
{
  "description": "新描述",
  "expires_at": "2026-01-01T00:00:00Z"
}
```
**响应：**
```json
{
  "success": true,
  "data": {
    "invite_code": {
      "id": 1,
      "updated_at": "2025-06-12T10:30:00Z"
    }
  }
}
```

### DELETE /api/v1/invite-codes/{id}
- 删除邀请码

**响应：**
```json
{
  "success": true
}
```

---

## 系统配置

### GET /api/v1/system/config
- 获取系统配置

### PUT /api/v1/system/config
- 更新系统配置

---

## 审计日志

### GET /api/v1/audit-logs
- 获取操作日志
