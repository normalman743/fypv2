# 校园LLM系统统一设计文档

## 目录
1. [文件系统重构](#1-文件系统重构)
2. [权限架构设计](#2-权限架构设计)  
3. [聊天文件集成](#3-聊天文件集成)
4. [实施计划](#4-实施计划)

---

## 1. 文件系统重构

### 1.1 问题分析
- ❌ `files` 和 `global_files` 双表重复
- ❌ 课程文件哈希值缺失导致重复上传
- ❌ 权限检查不完整

### 1.2 解决方案: 统一文件表

#### 数据库迁移
```sql
-- 为 files 表添加统一字段
ALTER TABLE files ADD COLUMN scope VARCHAR(20) DEFAULT 'course';
ALTER TABLE files ADD COLUMN visibility VARCHAR(20) DEFAULT 'private';
ALTER TABLE files ADD COLUMN file_hash VARCHAR(64) NULL;
ALTER TABLE files ADD COLUMN tags JSON NULL;
-- ... 其他字段

-- 迁移 global_files 数据到 files 表
INSERT INTO files (scope, visibility, file_hash, ...) 
SELECT 'global', CASE WHEN is_public THEN 'public' ELSE 'private' END, file_hash, ...
FROM global_files;

-- 为 document_chunks 添加统一关联
ALTER TABLE document_chunks ADD COLUMN file_id INT NULL;
UPDATE document_chunks dc 
INNER JOIN files f ON f.physical_file_id = dc.physical_file_id 
SET dc.file_id = f.id;
```

#### 统一文件模型
```python
class File(Base):
    __tablename__ = "files"
    
    # 基础字段
    id = Column(Integer, primary_key=True)
    physical_file_id = Column(Integer, ForeignKey("physical_files.id"))
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    
    # 统一管理字段
    scope = Column(String(20), default='course', index=True)  # 'course', 'global', 'personal'
    visibility = Column(String(20), default='private', index=True)  # 'private', 'course', 'public'
    file_hash = Column(String(64), index=True)  # 用于去重
    
    # 归属和权限
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True)
    
    # 元数据
    tags = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # RAG处理
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(20), default="pending")
    chunk_count = Column(Integer, default=0)
```

---

## 2. 权限架构设计

### 2.1 可扩展权限模型

#### 通用权限表
```sql
CREATE TABLE permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    
    -- 资源标识
    resource_type VARCHAR(50) NOT NULL,   -- 'file', 'course', 'folder', 'chat'
    resource_id VARCHAR(100) NOT NULL,
    
    -- 主体标识  
    subject_type VARCHAR(50) NOT NULL,    -- 'user', 'role', 'group'
    subject_id VARCHAR(100) NOT NULL,
    
    -- 权限定义
    action VARCHAR(50) NOT NULL,          -- 'read', 'write', 'delete', 'share'
    effect ENUM('allow', 'deny') DEFAULT 'allow',
    
    -- 条件和管理
    conditions JSON NULL,
    granted_by INT NULL,
    expires_at DATETIME NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_subject (subject_type, subject_id)
);
```

#### 权限引擎
```python
class PermissionEngine:
    def check_permission(self, resource_type: str, resource_id: str, 
                        subject_type: str, subject_id: str, action: str) -> bool:
        """
        权限检查优先级:
        1. 显式拒绝 (effect='deny')
        2. 显式允许 (effect='allow')  
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
        return self._check_default_policy(resource_type, resource_id, subject_type, subject_id, action)
```

#### 业务适配器
```python
class FilePermissionAdapter:
    def __init__(self, engine: PermissionEngine):
        self.engine = engine
    
    def can_read_file(self, file_id: int, user_id: int) -> bool:
        return self.engine.check_permission(
            resource_type='file', resource_id=str(file_id),
            subject_type='user', subject_id=str(user_id), action='read'
        )
    
    def share_file_to_course(self, file_id: int, course_id: int, granted_by: int):
        self.engine.grant_permission(
            resource_type='file', resource_id=str(file_id),
            subject_type='course_member', subject_id=str(course_id),
            action='read', granted_by=granted_by
        )
```

---

## 3. 聊天文件集成

### 3.1 简化API设计

#### 消息请求模型
```python
class MessageWithFilesRequest(BaseModel):
    content: str                    # 用户消息
    file_ids: List[int] = []       # 直接引用的文件
    folder_ids: List[int] = []     # 引用的文件夹
```

#### 智能上下文策略
```python
def build_message_context(user_message: str, file_ids: List[int], folder_ids: List[int]) -> str:
    """
    上下文构建策略:
    - 有 file_ids/folder_ids: 直接文件内容 + RAG相关文件
    - 无 file_ids/folder_ids: 纯RAG检索
    """
    
    context_parts = []
    
    if file_ids or folder_ids:
        # 直接文件内容
        direct_content = read_specified_files(file_ids, folder_ids)
        context_parts.append("=== 指定文件内容 ===")
        context_parts.append(direct_content)
        
        # RAG相关文件
        rag_content = rag_search_related_files(user_message, exclude_files=file_ids)
        if rag_content:
            context_parts.append("=== 相关文件内容 ===")
            context_parts.append(rag_content)
    else:
        # 纯RAG检索
        rag_content = rag_search_files(user_message)
        context_parts.append("=== 检索到的相关内容 ===")
        context_parts.append(rag_content)
    
    context_parts.append("=== 用户问题 ===")
    context_parts.append(user_message)
    
    return "\n\n".join(context_parts)
```

#### API实现
```python
@router.post("/chats/{chat_id}/messages", response_model=ResponseModel)
async def send_message_with_files(
    chat_id: int,
    request: MessageWithFilesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送消息 - 支持文件引用"""
    
    # 权限检查
    accessible_files = check_file_permissions(request.file_ids, request.folder_ids, current_user.id)
    
    # 构建上下文
    context = build_message_context(request.content, accessible_files['file_ids'], accessible_files['folder_ids'])
    
    # 调用AI
    ai_response = await call_ai_service(context)
    
    # 保存消息和文件关联
    message = save_message_with_file_refs(
        chat_id=chat_id,
        user_message=request.content,
        ai_response=ai_response,
        file_refs=accessible_files,
        user_id=current_user.id
    )
    
    return ResponseModel(success=True, data=message)
```

### 3.2 数据库设计

```sql
-- 消息文件引用表
CREATE TABLE message_file_references (
    id INT PRIMARY KEY AUTO_INCREMENT,
    message_id INT NOT NULL,
    file_id INT NOT NULL,
    reference_type ENUM('file', 'folder') NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    INDEX idx_message_refs (message_id)
);

-- 扩展messages表
ALTER TABLE messages ADD COLUMN context_size INT NULL COMMENT '上下文大小';
ALTER TABLE messages ADD COLUMN file_ref_count INT DEFAULT 0 COMMENT '引用文件数量';
```

---

## 4. 实施计划

### 阶段1: 文件系统重构 ✅
1. ✅ 创建数据库迁移脚本
2. ✅ 更新File模型为统一结构  
3. ✅ 修复文件哈希值同步问题
4. ✅ 创建UnifiedFileService
5. ✅ 更新RAG服务支持统一文件

### 阶段2: 权限系统完善 🔄
1. 🔄 实现PermissionEngine核心逻辑
2. ⏳ 创建权限相关数据表
3. ⏳ 实现FilePermissionAdapter 
4. ⏳ 更新所有API的权限检查
5. ⏳ 添加权限测试用例

### 阶段3: 聊天文件集成 ⏳
1. ⏳ 实现ChatFileService
2. ⏳ 创建消息文件引用表
3. ⏳ 实现智能上下文构建
4. ⏳ 更新聊天API支持文件引用
5. ⏳ 前端UI适配

### 阶段4: 高级功能 ⏳
1. ⏳ 课程成员管理
2. ⏳ 文件共享功能
3. ⏳ 权限管理界面
4. ⏳ 访问统计和审计

---

## 5. 技术优势总结

### 5.1 文件系统
- ✅ **统一管理**: 一个表管理所有文件类型
- ✅ **智能去重**: 基于文件哈希的物理文件共享
- ✅ **灵活作用域**: 支持course/global/personal多种场景
- ✅ **向后兼容**: 平滑迁移现有数据

### 5.2 权限系统  
- ✅ **高度可扩展**: 支持任意资源类型的权限控制
- ✅ **细粒度控制**: action级别的权限管理
- ✅ **角色继承**: 支持复杂的角色权限体系
- ✅ **条件权限**: 支持时间、IP等条件限制

### 5.3 聊天集成
- ✅ **智能上下文**: 直接文件 + RAG检索的混合策略
- ✅ **权限安全**: 统一的文件访问权限检查  
- ✅ **API简洁**: 前后端职责分离，接口清晰
- ✅ **性能可控**: 内置文件大小和数量限制

### 5.4 扩展性
- ✅ **新资源类型**: 可轻松添加folder、chat、course等权限
- ✅ **新主体类型**: 支持user、group、role等各种主体
- ✅ **新业务场景**: 权限引擎独立，可适配任意业务
- ✅ **新功能集成**: 聊天、文件、权限完全解耦

---

## 6. API使用示例

### 文件上传 (统一接口)
```javascript
POST /api/v1/files/upload
{
    "scope": "course",           // course/global/personal
    "course_id": 123,
    "visibility": "course",      // private/course/public
    "description": "课程讲义",
    "tags": ["lecture", "week1"]
}
```

### 聊天with文件
```javascript  
POST /api/v1/chats/456/messages
{
    "content": "请总结这些文件的核心观点",
    "file_ids": [789, 790],      // 直接指定文件
    "folder_ids": [12]           // 指定文件夹
}
```

### 权限管理
```javascript
POST /api/v1/permissions/grant
{
    "resource_type": "file",
    "resource_id": "789", 
    "subject_type": "user",
    "subject_id": "10",
    "action": "read"
}
```

这个统一设计既解决了当前的技术债务，又为未来的功能扩展提供了solid的架构基础。