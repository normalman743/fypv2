# 可扩展权限架构设计

## 设计理念

基于 **资源-主体-权限** (Resource-Subject-Permission) 的通用权限模型，支持未来各种业务场景的扩展。

## 核心架构

### 1. 权限抽象层

```python
# 权限系统的核心抽象
class Permission:
    resource_type: str    # 'file', 'course', 'folder', 'chat', etc.
    resource_id: int      # 资源实例ID
    subject_type: str     # 'user', 'role', 'group', 'course_member', etc.
    subject_id: int       # 主体实例ID
    action: str          # 'read', 'write', 'delete', 'share', 'manage', etc.
    effect: str          # 'allow', 'deny'
    conditions: dict     # 额外条件 (时间、IP等)
```

### 2. 数据库设计

#### 主表: 通用权限表
```sql
CREATE TABLE permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    
    -- 资源标识
    resource_type VARCHAR(50) NOT NULL,   -- 'file', 'course', 'folder'
    resource_id VARCHAR(100) NOT NULL,    -- 支持字符串ID，增强灵活性
    
    -- 主体标识  
    subject_type VARCHAR(50) NOT NULL,    -- 'user', 'role', 'group', 'course_member'
    subject_id VARCHAR(100) NOT NULL,
    
    -- 权限定义
    action VARCHAR(50) NOT NULL,          -- 'read', 'write', 'delete', 'share'
    effect ENUM('allow', 'deny') DEFAULT 'allow',
    
    -- 条件和元数据
    conditions JSON NULL,                 -- 复杂条件: 时间、IP、设备等
    metadata JSON NULL,                   -- 扩展字段
    
    -- 管理字段
    granted_by INT NULL,                  -- 授权人
    granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NULL,             -- 过期时间
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 索引优化
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_subject (subject_type, subject_id),
    INDEX idx_action (action),
    INDEX idx_active_permissions (is_active, expires_at),
    
    FOREIGN KEY (granted_by) REFERENCES users(id)
);
```

#### 角色表: 支持动态角色
```sql
CREATE TABLE roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    scope VARCHAR(50) DEFAULT 'global',   -- 'global', 'course', 'organization'
    scope_id INT NULL,                    -- 作用域ID
    is_system BOOLEAN DEFAULT FALSE,      -- 系统内置角色
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 系统内置角色示例
INSERT INTO roles (name, description, is_system) VALUES
('admin', '系统管理员', TRUE),
('course_owner', '课程所有者', TRUE),
('course_collaborator', '课程协作者', TRUE),
('course_member', '课程成员', TRUE);
```

#### 主体-角色关联表
```sql
CREATE TABLE subject_roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    subject_type VARCHAR(50) NOT NULL,
    subject_id VARCHAR(100) NOT NULL,
    role_id INT NOT NULL,
    scope_type VARCHAR(50) NULL,         -- 角色生效范围
    scope_id VARCHAR(100) NULL,
    assigned_by INT NULL,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    INDEX idx_subject_role (subject_type, subject_id, role_id),
    INDEX idx_scope (scope_type, scope_id),
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (assigned_by) REFERENCES users(id)
);
```

#### 权限策略表 (可选)
```sql
CREATE TABLE permission_policies (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    resource_type VARCHAR(50) NOT NULL,
    policy_rules JSON NOT NULL,          -- 策略规则定义
    is_default BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3. 权限引擎实现

```python
class PermissionEngine:
    """可扩展的权限检查引擎"""
    
    def __init__(self, db: Session):
        self.db = db
        self.policy_cache = {}
        self.role_cache = {}
    
    def check_permission(
        self, 
        resource_type: str, 
        resource_id: str, 
        subject_type: str, 
        subject_id: str, 
        action: str,
        context: dict = None
    ) -> bool:
        """
        通用权限检查方法
        
        检查顺序:
        1. 显式拒绝权限 (effect='deny')
        2. 显式允许权限 (effect='allow') 
        3. 角色继承权限
        4. 默认策略
        5. 拒绝访问
        """
        
        # 1. 检查显式拒绝
        if self._has_explicit_deny(resource_type, resource_id, subject_type, subject_id, action):
            return False
        
        # 2. 检查显式允许
        if self._has_explicit_allow(resource_type, resource_id, subject_type, subject_id, action):
            return True
        
        # 3. 检查角色权限
        if self._has_role_permission(resource_type, resource_id, subject_type, subject_id, action):
            return True
        
        # 4. 检查默认策略
        if self._check_default_policy(resource_type, resource_id, subject_type, subject_id, action, context):
            return True
        
        # 5. 默认拒绝
        return False
    
    def grant_permission(
        self,
        resource_type: str,
        resource_id: str, 
        subject_type: str,
        subject_id: str,
        action: str,
        granted_by: int,
        expires_at: datetime = None,
        conditions: dict = None
    ):
        """授予权限"""
        permission = Permission(
            resource_type=resource_type,
            resource_id=resource_id,
            subject_type=subject_type,
            subject_id=subject_id,
            action=action,
            effect='allow',
            granted_by=granted_by,
            expires_at=expires_at,
            conditions=conditions
        )
        
        self.db.add(permission)
        self.db.commit()
        
        # 清除相关缓存
        self._clear_cache(subject_type, subject_id)
    
    def revoke_permission(self, permission_id: int):
        """撤销权限"""
        permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
        if permission:
            permission.is_active = False
            self.db.commit()
    
    def assign_role(
        self, 
        subject_type: str, 
        subject_id: str, 
        role_name: str, 
        scope_type: str = None, 
        scope_id: str = None
    ):
        """分配角色"""
        role = self.db.query(Role).filter(Role.name == role_name).first()
        if not role:
            raise ValueError(f"Role {role_name} not found")
        
        subject_role = SubjectRole(
            subject_type=subject_type,
            subject_id=subject_id,
            role_id=role.id,
            scope_type=scope_type,
            scope_id=scope_id
        )
        
        self.db.add(subject_role)
        self.db.commit()
```

### 4. 业务层适配器

```python
class FilePermissionAdapter:
    """文件权限业务适配器"""
    
    def __init__(self, engine: PermissionEngine):
        self.engine = engine
    
    def can_read_file(self, file_id: int, user_id: int) -> bool:
        return self.engine.check_permission(
            resource_type='file',
            resource_id=str(file_id),
            subject_type='user', 
            subject_id=str(user_id),
            action='read'
        )
    
    def can_edit_file(self, file_id: int, user_id: int) -> bool:
        return self.engine.check_permission(
            resource_type='file',
            resource_id=str(file_id),
            subject_type='user',
            subject_id=str(user_id), 
            action='write'
        )
    
    def share_file_to_user(self, file_id: int, target_user_id: int, permission_level: str, granted_by: int):
        """将文件共享给用户"""
        actions = self._get_actions_for_level(permission_level)
        
        for action in actions:
            self.engine.grant_permission(
                resource_type='file',
                resource_id=str(file_id),
                subject_type='user',
                subject_id=str(target_user_id),
                action=action,
                granted_by=granted_by
            )
    
    def share_file_to_course(self, file_id: int, course_id: int, permission_level: str, granted_by: int):
        """将文件共享给课程"""
        actions = self._get_actions_for_level(permission_level)
        
        for action in actions:
            self.engine.grant_permission(
                resource_type='file',
                resource_id=str(file_id),
                subject_type='course_member',
                subject_id=str(course_id),
                action=action,
                granted_by=granted_by
            )

class CoursePermissionAdapter:
    """课程权限业务适配器"""
    
    def __init__(self, engine: PermissionEngine):
        self.engine = engine
    
    def add_course_member(self, course_id: int, user_id: int, role: str = 'member'):
        """添加课程成员"""
        self.engine.assign_role(
            subject_type='user',
            subject_id=str(user_id),
            role_name=f'course_{role}',
            scope_type='course',
            scope_id=str(course_id)
        )
    
    def can_manage_course(self, course_id: int, user_id: int) -> bool:
        return self.engine.check_permission(
            resource_type='course',
            resource_id=str(course_id),
            subject_type='user',
            subject_id=str(user_id),
            action='manage'
        )
```

## 扩展性示例

### 1. 新增聊天权限控制

```python
# 无需修改核心权限引擎，只需添加适配器
class ChatPermissionAdapter:
    def can_read_chat(self, chat_id: int, user_id: int) -> bool:
        return self.engine.check_permission(
            resource_type='chat',
            resource_id=str(chat_id),
            subject_type='user',
            subject_id=str(user_id),
            action='read'
        )
```

### 2. 新增组织级权限

```python
# 添加新的主体类型
class OrganizationPermissionAdapter:
    def assign_org_admin(self, org_id: int, user_id: int):
        self.engine.assign_role(
            subject_type='user',
            subject_id=str(user_id),
            role_name='org_admin',
            scope_type='organization', 
            scope_id=str(org_id)
        )
```

### 3. 条件权限示例

```python
# 基于时间的权限
time_condition = {
    "time_range": {
        "start": "09:00",
        "end": "18:00"
    },
    "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
}

# 基于IP的权限
ip_condition = {
    "allowed_ips": ["192.168.1.0/24", "10.0.0.0/8"]
}

# 基于设备的权限  
device_condition = {
    "device_types": ["mobile", "tablet"],
    "require_app": True
}
```

## 实施计划

### 阶段1: 核心权限引擎
1. 创建权限相关数据表
2. 实现 PermissionEngine 核心逻辑
3. 添加基础角色和策略

### 阶段2: 文件权限适配
1. 实现 FilePermissionAdapter
2. 迁移现有文件权限逻辑
3. 更新所有文件相关API

### 阶段3: 课程权限扩展
1. 实现 CoursePermissionAdapter
2. 添加课程成员管理
3. 支持课程级文件共享

### 阶段4: 高级功能
1. 权限策略配置界面
2. 条件权限支持
3. 审计日志和监控

## 优势总结

1. **高度可扩展**: 新业务场景只需添加适配器
2. **统一管理**: 所有权限都通过统一引擎处理
3. **灵活配置**: 支持复杂的权限策略和条件
4. **性能优化**: 内置缓存和索引优化
5. **审计友好**: 完整的权限变更记录

这个架构可以支持从简单的文件权限到复杂的企业级权限管理的各种场景。