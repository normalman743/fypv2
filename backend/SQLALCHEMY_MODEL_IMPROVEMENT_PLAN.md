# 🔧 SQLAlchemy模型改进计划 - 单表+Chroma架构

**目标架构**: 单表文件存储 + Chroma向量数据库  
**改进时间**: 2025-06-29  
**当前模型数量**: 9个 → **目标**: 13个  

---

## 🎯 架构设计原则

### 📋 核心理念
- **单表文件存储** - 避免复杂的双表设计，简化管理
- **Chroma向量检索** - 专业向量数据库处理文档检索
- **最小化关系表** - 减少JOIN查询复杂度
- **JSON字段优化** - 使用JSON存储结构化但灵活的数据

---

## 📊 当前模型状态分析

### ✅ **完整且无需修改 (5个)**
| 模型 | 文件 | 状态 | 说明 |
|------|------|------|------|
| User | user.py | ✅ 完整 | 用户认证、偏好、财务管理 |
| Semester | semester.py | ✅ 完整 | 学期管理 |
| Course | course.py | ✅ 完整 | 课程管理 |
| Folder | folder.py | ✅ 完整 | 文件分类 |
| InviteCode | invite_code.py | ✅ 完整 | 邀请注册 |

### ⚠️ **需要改进 (2个)**
| 模型 | 文件 | 问题 | 优先级 |
|------|------|------|--------|
| File | file.py | 缺少RAG处理字段 | 🔴 高 |
| Message | message.py | 缺少rag_sources JSON字段 | 🔴 高 |

### ✅ **设计合理但可优化 (2个)**
| 模型 | 文件 | 状态 | 说明 |
|------|------|------|------|
| Chat | chat.py | ✅ 良好 | RAG配置完整 |
| MessageAttachment | message_attachment.py | ✅ 良好 | 关联表设计合理 |

### ❌ **完全缺失 (4个)**
| 模型 | 用途 | 优先级 | 说明 |
|------|------|--------|------|
| DocumentChunk | Chroma同步 | 🔴 高 | 文档分块管理 |
| GlobalFile | 全局文件 | 🟡 中 | FAQ、政策文档 |
| AuditLog | 审计日志 | 🟢 低 | 操作记录 |
| SystemConfig | 系统配置 | 🟢 低 | 动态配置 |

---

## 🛠️ 具体改进方案

### 🔴 **高优先级修复**

#### 1. **扩展File模型** (app/models/file.py)

**添加字段**:
```python
# RAG处理相关
file_hash = Column(String(64), nullable=True, index=True, comment='SHA256文件哈希，用于去重')
content_preview = Column(Text, nullable=True, comment='文件内容预览')
processing_error = Column(Text, nullable=True, comment='处理错误信息')
processed_at = Column(DateTime, nullable=True, comment='处理完成时间')
chunk_count = Column(Integer, default=0, comment='在Chroma中的分块数量')

# 存储优化
cloud_url = Column(String(500), nullable=True, comment='云存储URL（可选）')
```

**修改现有字段**:
```python
# 使文件路径可选，支持云存储
file_path = Column(String(500), nullable=True, comment='本地存储路径')
```

#### 2. **扩展Message模型** (app/models/message.py)

**添加JSON字段**:
```python
# RAG检索结果
rag_sources = Column(JSON, nullable=True, comment='RAG检索来源文档信息')
```

**字段结构示例**:
```json
{
  "sources": [
    {
      "file_id": 123,
      "file_name": "lecture_01.pdf",
      "chunk_id": "chunk_456",
      "relevance_score": 0.85,
      "content_snippet": "这是相关内容片段..."
    }
  ],
  "query": "用户的原始问题",
  "total_chunks": 5
}
```

### 🔴 **创建DocumentChunk模型** (app/models/document_chunk.py)

**目的**: 与Chroma向量数据库同步的分块管理
```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Text, JSON
from sqlalchemy.orm import relationship
from app.models.database import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    
    # 文件关联
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False, index=True)
    global_file_id = Column(Integer, ForeignKey("global_files.id"), nullable=True, index=True)
    
    # 分块信息
    chunk_text = Column(Text, nullable=False, comment='分块文本内容')
    chunk_index = Column(Integer, nullable=False, comment='在文件中的分块序号')
    token_count = Column(Integer, nullable=True, comment='Token数量')
    
    # Chroma同步
    chroma_id = Column(String(36), unique=True, nullable=False, comment='Chroma中的唯一ID')
    
    # 元数据
    metadata = Column(JSON, nullable=True, comment='Chroma元数据')
    
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    file = relationship("File", back_populates="chunks")
    global_file = relationship("GlobalFile", back_populates="chunks")
```

### 🟡 **中优先级扩展**

#### 3. **创建GlobalFile模型** (app/models/global_file.py)

**目的**: 管理全局共享文件（FAQ、政策文档、使用手册等）
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func, Text, JSON
from sqlalchemy.orm import relationship
from app.models.database import Base

class GlobalFile(Base):
    __tablename__ = "global_files"

    id = Column(Integer, primary_key=True, index=True)
    
    # 文件信息
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    upload_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=True, index=True)
    
    # 分类管理
    category = Column(String(50), default='general', index=True, 
                     comment='分类: general, faq, policy, manual, template')
    tags = Column(JSON, nullable=True, comment='标签数组')
    description = Column(Text, nullable=True, comment='文件描述')
    
    # 权限控制
    is_active = Column(Boolean, default=True, index=True)
    is_public = Column(Boolean, default=True, index=True, comment='是否对所有用户可见')
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # RAG处理相关
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(20), default='pending', index=True)
    processing_error = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    chunk_count = Column(Integer, default=0)
    content_preview = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    creator = relationship("User", back_populates="global_files")
    chunks = relationship("DocumentChunk", back_populates="global_file", cascade="all, delete-orphan")
```

### 🟢 **低优先级补充**

#### 4. **创建AuditLog模型** (app/models/audit_log.py)

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import relationship
from app.models.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    user = relationship("User", back_populates="audit_logs")
```

#### 5. **创建SystemConfig模型** (app/models/system_config.py)

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func, Text
from sqlalchemy.orm import relationship
from app.models.database import Base

class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(50), unique=True, nullable=False)
    config_value = Column(Text, nullable=False)
    description = Column(String(200), nullable=True)
    is_public = Column(Boolean, default=False, comment='是否可公开访问')
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    updater = relationship("User")
```

---

## 🔄 关系映射更新

### **需要添加的反向关系**

#### User模型更新
```python
# 添加到user.py
global_files = relationship("GlobalFile", back_populates="creator")
audit_logs = relationship("AuditLog", back_populates="user")
```

#### File模型更新
```python
# 添加到file.py
chunks = relationship("DocumentChunk", back_populates="file", cascade="all, delete-orphan")
```

---

## 📈 实施计划

### **阶段1: 核心修复** (今日完成)
1. ✅ 扩展File模型 - 添加RAG处理字段
2. ✅ 扩展Message模型 - 添加rag_sources JSON字段
3. ✅ 创建DocumentChunk模型

### **阶段2: 功能扩展** (明日完成)
1. ✅ 创建GlobalFile模型
2. ✅ 更新关系映射
3. ✅ 数据库迁移脚本

### **阶段3: 系统完善** (后续)
1. ✅ 创建AuditLog模型
2. ✅ 创建SystemConfig模型
3. ✅ 性能优化索引

---

## 🧪 测试验证

### **模型测试**
```python
# 验证File模型扩展
file = File(original_name="test.pdf", file_hash="abc123...")

# 验证DocumentChunk关联
chunk = DocumentChunk(file_id=file.id, chroma_id="uuid-123")

# 验证Message的RAG sources
message = Message(rag_sources={"sources": [...], "query": "..."})
```

### **数据库迁移**
```python
# 生成迁移脚本
alembic revision --autogenerate -m "Add RAG support fields"

# 执行迁移
alembic upgrade head
```

---

## 📊 预期效果

### **功能提升**
- ✅ 完整的RAG文档处理流程
- ✅ 文件去重和内容预览
- ✅ 全局文件共享机制
- ✅ 系统操作审计追踪

### **性能优化**
- ✅ 单表设计减少JOIN查询
- ✅ JSON字段灵活存储RAG结果
- ✅ 合理索引提升查询效率

### **维护简化**
- ✅ 避免复杂的双表文件设计
- ✅ 与Chroma向量数据库无缝集成
- ✅ 统一的错误处理和状态管理

---

**改进总结**: 通过以上改进，SQLAlchemy模型将完全支持单表+Chroma架构，提供完整的RAG功能，同时保持设计简洁和高性能。

**预计工作量**: 2-3个工作日  
**技术风险**: 低  
**业务价值**: 高 ✅