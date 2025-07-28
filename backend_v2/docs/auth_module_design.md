# Auth 模块技术设计文档

## 1. 目标
基于现有backend实现，在backend_v2中创建模块化的Auth认证系统，保持API完全兼容并扩展密码管理功能。

## 2. API 接口设计

### 2.1 现有接口（保持兼容）
```
POST   /api/v1/auth/register          # 用户注册
POST   /api/v1/auth/login             # 用户登录  
GET    /api/v1/auth/me               # 获取用户信息
PUT    /api/v1/auth/me               # 更新用户信息
POST   /api/v1/auth/logout           # 用户登出
POST   /api/v1/auth/verify-email     # 验证邮箱（仅注册时）
POST   /api/v1/auth/resend-verification # 重发验证码（仅注册时）
```

### 2.2 新增接口
```
PUT    /api/v1/auth/change-password   # 修改密码
POST   /api/v1/auth/forgot-password   # 忘记密码
POST   /api/v1/auth/reset-password    # 重置密码  
```

## 3. 数据模型设计

### 3.1 User 模型扩展
基于现有 `/backend/app/models/user.py`，新增字段：

```python
class User(Base):
    __tablename__ = "users"
    
    # === 现有字段保持不变 ===
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)  # 注册后不可更改
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), default="user", index=True)
    balance = Column(DECIMAL(10, 2), default=1.00)
    total_spent = Column(DECIMAL(10, 2), default=0.00)
    preferred_language = Column(String(20), default="zh_CN")
    preferred_theme = Column(String(20), default="light")
    last_opened_semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # === 新增安全字段 ===
    email_verified = Column(Boolean, default=False, index=True)  # 邮箱验证状态
    last_login_at = Column(DateTime, nullable=True)              # 最后登录时间
    failed_login_attempts = Column(Integer, default=0)           # 失败登录次数
    locked_until = Column(DateTime, nullable=True, index=True)   # 账户锁定到期时间
    password_changed_at = Column(DateTime, nullable=True)        # 密码最后修改时间
    
    # === 新增关系 ===
    password_resets = relationship("PasswordReset", back_populates="user")
```

### 3.2 EmailVerification 模型（现有，保持不变）
用于注册时的邮箱验证，验证后email_verified设为True，之后不再允许更改邮箱。

### 3.3 新增 PasswordReset 模型  
```python
class PasswordReset(Base):
    __tablename__ = "password_resets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reset_token = Column(String(36), nullable=False, unique=True, index=True)  # UUID
    expires_at = Column(DateTime, nullable=False, index=True)                  # 1小时过期
    is_used = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    user = relationship("User", back_populates="password_resets")
```

## 4. 新增API详细规范

### 4.1 修改密码
```http
PUT /api/v1/auth/change-password
Authorization: Bearer <token>

Request:
{
  "old_password": "currentPassword123!",
  "new_password": "newPassword456!"
}

Response 200:
{
  "success": true,
  "data": {
    "message": "密码修改成功"
  }
}

Error 400: 旧密码错误
Error 401: 未认证
```

### 4.2 忘记密码
```http
POST /api/v1/auth/forgot-password

Request:
{
  "email": "user@example.com"
}

Response 200:
{
  "success": true,
  "data": {
    "message": "重置邮件已发送，请查收"
  }
}

Error 400: 邮箱不存在或请求过于频繁
```

### 4.3 重置密码
```http
POST /api/v1/auth/reset-password

Request:
{
  "reset_token": "uuid-token-string",
  "new_password": "newPassword456!"
}

Response 200:
{
  "success": true,
  "data": {
    "message": "密码重置成功"
  }
}

Error 400: 重置令牌无效或已过期
```

## 5. Schema设计要点

基于现有 `/backend/app/schemas/user.py` 的验证规则：

### 5.1 新增请求Schema
```python
class PasswordChangeRequest(BaseModel):
    old_password: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)
    # 使用现有的密码复杂度验证

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    reset_token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, max_length=128)
    # 使用现有的密码复杂度验证
```

### 5.2 验证规则
- **密码验证**: 8-128位，包含大小写字母、数字、特殊字符（使用现有的 `_validate_password`）
- **邮箱验证**: EmailStr类型，验证后不可更改
- **新旧密码**: 不能相同

## 6. 兼容性保证

### 6.1 API兼容
- 所有现有API端点完全不变
- 响应格式保持一致（BaseResponse[T]结构）
- 错误代码和消息保持一致

### 6.2 数据库兼容  
- 现有表结构不改变，只增加字段
- 使用Alembic生成迁移文件
- 新增字段都有默认值，不影响现有数据

### 6.3 认证兼容
- JWT token格式不变
- 现有依赖注入(get_current_user)保持不变
- 权限检查逻辑保持一致

### 6.4 邮箱管理策略
- ✅ 注册时：需要邮箱验证，验证后 email_verified=True
- ❌ 注册后：不允许更改邮箱，移除相关API
- 🔒 安全性：邮箱作为唯一身份标识，不可变更

---

**下一步**: 按此设计实现代码，重点关注密码管理功能的安全性。