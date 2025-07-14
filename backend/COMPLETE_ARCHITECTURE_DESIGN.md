# 校园LLM系统完整架构设计

## 1. 统一文件系统架构

### 1.1 核心改进
- ✅ 合并 `files` 和 `global_files` 表为统一的 `files` 表
- ✅ 增加 `scope` 字段: `'course'`, `'global'`, `'personal'`, `'shared'`
- ✅ 增加 `visibility` 字段: `'private'`, `'course'`, `'public'`, `'shared'`
- ✅ 修复文件哈希去重问题

### 1.2 统一文件模型
```python
class File(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    physical_file_id = Column(Integer, ForeignKey("physical_files.id"), nullable=False)
    
    # 基本信息
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    
    # 作用域和可见性 (核心改进)
    scope = Column(String(20), nullable=False, default='course', index=True)
    visibility = Column(String(20), default='private', index=True)
    
    # 关联字段
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 文件元数据
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_hash = Column(String(64), nullable=True, index=True)
    
    # 共享控制
    is_shareable = Column(Boolean, default=True)
    share_settings = Column(JSON, nullable=True)
```

## 2. 可扩展权限架构

### 2.1 通用权限模型
```sql
CREATE TABLE permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    
    -- 资源标识
    resource_type VARCHAR(50) NOT NULL,   -- 'file', 'course', 'folder', 'chat'
    resource_id VARCHAR(100) NOT NULL,
    
    -- 主体标识  
    subject_type VARCHAR(50) NOT NULL,    -- 'user', 'role', 'group', 'course_member'
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

### 2.2 权限检查引擎
```python
class PermissionEngine:
    def check_permission(
        self, 
        resource_type: str, 
        resource_id: str, 
        subject_type: str, 
        subject_id: str, 
        action: str
    ) -> bool:
        """
        权限检查优先级:
        1. 显式拒绝 -> False
        2. 显式允许 -> True
        3. 角色权限 -> 检查角色
        4. 默认策略 -> 业务规则
        5. 拒绝访问 -> False
        """
```

## 3. 聊天文件引用功能

### 3.1 简化API设计
```python
class MessageRequest(BaseModel):
    content: str                    # 用户消息
    file_ids: List[int] = []       # 引用的文件ID
    folder_ids: List[int] = []     # 引用的文件夹ID

@router.post("/chats/{chat_id}/messages")
async def send_message(
    chat_id: int,
    request: MessageRequest,
    current_user: User = Depends(get_current_user)
):
    """
    智能上下文策略:
    - 有 file_ids/folder_ids: 文件内容 + RAG相关文件
    - 无文件引用: 纯RAG检索
    """
```

### 3.2 智能上下文构建
```python
class ChatContextService:
    def build_context(self, message: str, file_ids: List[int], folder_ids: List[int], user_id: int):
        context_parts = []
        
        # 1. 直接引用的文件内容
        if file_ids or folder_ids:
            for file_id in file_ids:
                file_content = self._read_file_with_permission(file_id, user_id)
                context_parts.append(f"=== {file_content.name} ===\n{file_content.text}")
            
            for folder_id in folder_ids:
                folder_files = self._get_folder_files_with_permission(folder_id, user_id)
                for file_content in folder_files:
                    context_parts.append(f"=== {file_content.name} ===\n{file_content.text}")
        
        # 2. RAG检索相关文件 (总是执行)
        rag_sources = self._rag_search(message, user_id)
        for source in rag_sources:
            context_parts.append(f"=== 相关: {source.file_name} ===\n{source.content}")
        
        return {
            'context': '\n\n'.join(context_parts),
            'direct_files': len(file_ids) + sum(len(self._get_folder_files(fid)) for fid in folder_ids),
            'rag_sources': len(rag_sources)
        }
```

## 4. 数据库迁移方案

### 4.1 迁移脚本 (已完成)
- ✅ 备份原始表
- ✅ 为 `files` 表添加新字段
- ✅ 迁移 `global_files` 数据
- ✅ 修复文件哈希值
- ✅ 创建文件共享表
- ✅ 更新 `document_chunks` 支持统一 `file_id`

### 4.2 关键表结构
```sql
-- 文件共享表
CREATE TABLE file_shares (
    id INT PRIMARY KEY AUTO_INCREMENT,
    file_id INT NOT NULL,
    shared_with_type VARCHAR(20) NOT NULL,  -- 'user', 'course', 'group'
    shared_with_id INT NULL,
    permission_level VARCHAR(20) DEFAULT 'read',
    expires_at DATETIME NULL,
    shared_by INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 消息文件引用表
CREATE TABLE message_file_references (
    id INT PRIMARY KEY AUTO_INCREMENT,
    message_id INT NOT NULL,
    file_id INT NOT NULL,
    reference_type ENUM('file', 'folder') NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 扩展消息表
ALTER TABLE messages ADD COLUMN context_size INT NULL;
ALTER TABLE messages ADD COLUMN direct_file_count INT DEFAULT 0;
ALTER TABLE messages ADD COLUMN rag_source_count INT DEFAULT 0;
```

## 5. 服务层架构

### 5.1 统一文件服务
```python
class UnifiedFileService:
    def upload_file(self, file, user_id, scope='course', **kwargs) -> File:
        """统一文件上传，支持所有作用域"""
        
    def get_accessible_files(self, user_id, scope=None, course_id=None) -> List[File]:
        """获取用户可访问的文件"""
        
    def share_file(self, file_id, shared_with_type, shared_with_id, permission_level) -> FileShare:
        """文件共享"""
```

### 5.2 权限服务
```python
class FilePermissionService:
    def can_access_file(self, file_id: int, user_id: int) -> bool:
        """检查文件访问权限"""
        
    def can_edit_file(self, file_id: int, user_id: int) -> bool:
        """检查文件编辑权限"""
        
    def get_accessible_files(self, user_id: int, **filters) -> List[File]:
        """获取可访问文件列表（含权限过滤）"""
```

### 5.3 聊天文件服务
```python
class ChatFileService:
    def send_message_with_files(self, chat_id, message, file_ids, folder_ids, user_id):
        """发送包含文件引用的消息，智能构建上下文"""
        
    def build_smart_context(self, message, file_ids, folder_ids, user_id):
        """构建智能上下文：直接文件 + RAG检索"""
```

## 6. API端点设计

### 6.1 统一文件API
```python
# 文件上传 (支持所有作用域)
POST /api/v1/files/upload
{
    "scope": "course|global|personal",
    "course_id": 123,
    "visibility": "private|course|public"
}

# 文件列表 (权限过滤)
GET /api/v1/files?scope=course&course_id=123

# 文件共享
POST /api/v1/files/{file_id}/share
{
    "shared_with_type": "user|course|group",
    "shared_with_id": 456,
    "permission_level": "read|edit|manage"
}
```

### 6.2 聊天文件API
```python
# 发送消息 (智能上下文)
POST /api/v1/chats/{chat_id}/messages
{
    "content": "用户消息",
    "file_ids": [123, 456],
    "folder_ids": [78]
}

# 响应包含上下文统计
{
    "message": {...},
    "context_stats": {
        "direct_files": 5,
        "rag_sources": 3,
        "total_context_size": 12000
    }
}
```

## 7. 前端集成指南

### 7.1 文件选择器
```javascript
// 用户@文件时，前端显示文件选择器
const selectedFiles = await showFileSelector({
    scope: ['course', 'personal'],
    course_id: currentCourse.id,
    allow_folders: true
});

// 发送消息时包含文件ID
await sendMessage({
    content: "请分析这些文件",
    file_ids: selectedFiles.files.map(f => f.id),
    folder_ids: selectedFiles.folders.map(f => f.id)
});
```

### 7.2 权限提示
```javascript
// 文件权限检查
const filePermissions = await checkFilePermissions(fileIds);
if (filePermissions.some(p => !p.can_access)) {
    showPermissionError("部分文件无访问权限");
}
```

## 8. 部署和迁移步骤

### 8.1 迁移执行
```bash
# 1. 备份数据库
mysqldump campus_llm_db > backup_$(date +%Y%m%d).sql

# 2. 运行迁移脚本
python scripts/migrate_to_unified_files.py
python scripts/fix_document_chunks.py
python scripts/fix_file_hashes.py

# 3. 验证迁移结果
python scripts/test_unified_files.py
python scripts/test_security_vulnerability.py
```

### 8.2 性能优化
```sql
-- 关键索引
CREATE INDEX idx_files_scope_visibility ON files(scope, visibility);
CREATE INDEX idx_files_owner_course ON files(user_id, course_id);
CREATE INDEX idx_document_chunks_file_id ON document_chunks(file_id);
CREATE INDEX idx_file_shares_target ON file_shares(shared_with_type, shared_with_id);
```

## 9. 扩展路线图

### 9.1 短期功能 (1-2个月)
- ✅ 统一文件系统
- ✅ 基础权限控制
- 🔄 聊天文件引用
- 🔄 文件共享功能

### 9.2 中期功能 (3-6个月)
- 📋 课程成员管理系统
- 📋 高级权限策略
- 📋 文件版本控制
- 📋 批量操作API

### 9.3 长期功能 (6-12个月)
- 📋 多租户支持
- 📋 文件协作编辑
- 📋 智能文档分析
- 📋 移动端优化

## 10. 安全和监控

### 10.1 安全措施
- 所有文件访问必须通过权限检查
- 完整的操作审计日志
- 文件上传类型和大小限制
- API访问频率限制

### 10.2 监控指标
- 文件上传/下载统计
- 权限检查性能
- RAG检索效果
- 用户活跃度分析

---

## 总结

这个完整架构设计实现了：

1. **统一性**: 所有文件通过一个表管理，一套API操作
2. **安全性**: 完善的权限控制，多层安全检查
3. **扩展性**: 可扩展权限引擎，支持未来各种业务场景
4. **智能性**: 聊天文件引用，智能上下文构建
5. **性能**: 优化的数据库设计，高效的权限检查

系统既解决了当前的文件管理问题，又为未来的功能扩展奠定了solid的基础。