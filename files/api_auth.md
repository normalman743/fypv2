# 认证与用户管理 API

## POST /api/v1/auth/register
- 用户注册（需邀请码）

**请求体：**
```json
{
  "email": "user@example.com",
  "username": "user01",
  "password": "yourpassword",
  "invite_code": "USER2024"
}
```
**响应：**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "username": "user01",
      "email": "user@example.com",
      "role": "user",
      "balance": 1.00,
      "created_at": "2025-06-11T10:30:00Z"
    }
  }
}
```

---

## POST /api/v1/auth/login
- 用户登录

**请求体：**
```json
{
  "username": "user01",
  "password": "yourpassword"
}
```
**响应：**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 86400,
    "user": {
      "id": 1,
      "username": "user01",
      "email": "user@example.com",
      "role": "user",
      "balance": 1.00,
      "preferred_language": "zh_CN",
      "preferred_theme": "light",
      "last_opened_semester_id": null,
      "created_at": "2025-06-11T10:30:00Z"
    }
  }
}
```

---

## GET /api/v1/auth/me
- 获取当前用户信息

**响应：**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "user01",
    "email": "user@example.com",
    "role": "user",
    "balance": 0.95,
    "total_spent": 0.05,
    "preferred_language": "zh_CN",
    "preferred_theme": "light",
    "last_opened_semester_id": 3,
    "created_at": "2025-06-11T10:30:00Z"
  }
}
```

---

## PUT /api/v1/auth/me
- 更新当前用户信息

**请求体：**
```json
{
  "username": "new_username",
  "preferred_language": "en",
  "preferred_theme": "dark"
}
```
**响应：**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "new_username",
    "email": "user@example.com",
    "role": "user",
    "balance": 0.95,
    "total_spent": 0.05,
    "preferred_language": "en",
    "preferred_theme": "dark",
    "last_opened_semester_id": 3,
    "created_at": "2025-06-11T10:30:00Z"
  }
}
```

---

## POST /api/v1/auth/logout
- 用户登出

**响应：**
```json
{
  "success": true,
  "data": {
    "message": "已成功登出"
  }
}
```
