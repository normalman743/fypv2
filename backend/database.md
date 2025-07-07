# 🗄️ 校园LLM系统数据库设计
39.108.113.103:3306
user: campus_user
password: CampusLLM123!
database：
## 📋 架构概览

### 存储策略
- **关系数据：** MySQL 8.0
- **向量数据：** Chroma 
- **文件存储：** 本地文件系统
- **缓存：** Redis（可选）

### 核心原则
- **规范化设计** - 避免数据冗余
- **字段完整** - 包含所有API需要的基础字段  
- **扩展性好** - 为后期功能预留字段
- **RAG优化** - 支持LangChain + Chroma的向量检索

---

## 🔗 MySQL数据库表结构

### 用户表 (users)
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(128),
    role VARCHAR(20) DEFAULT 'user' COMMENT 'user, admin',
    balance DECIMAL(10,2) DEFAULT 1.00,
    total_spent DECIMAL(10,2) DEFAULT 0.00,
    preferred_language VARCHAR(20) DEFAULT 'zh_CN' COMMENT 'zh_CN, en',
    preferred_theme VARCHAR(20) DEFAULT 'light' COMMENT 'light , dark ,system',
    last_opened_semester_id INT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role),
    FOREIGN KEY (last_opened_semester_id) REFERENCES semesters(id) ON DELETE SET NULL
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 邀请码表 (invite_codes)
```sql
CREATE TABLE invite_codes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(20) UNIQUE NOT NULL,
    description VARCHAR(200) NULL COMMENT '邀请码用途描述',
    is_used BOOLEAN DEFAULT FALSE COMMENT '是否已使用',
    used_by INT NULL COMMENT '使用者用户ID',
    used_at DATETIME NULL COMMENT '使用时间',
    expires_at DATETIME NULL COMMENT '过期时间',
    is_active BOOLEAN DEFAULT TRUE,
    created_by INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (used_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_code (code),
    INDEX idx_is_used (is_used),
    INDEX idx_is_active (is_active),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 学期表 (semesters)
```sql
CREATE TABLE semesters (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    start_date DATETIME,
    end_date DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_code (code),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 课程表 (courses)
```sql
CREATE TABLE courses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) NOT NULL,
    description TEXT,
    semester_id INT NOT NULL,
    user_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (semester_id) REFERENCES semesters(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_course_per_user_semester (code, semester_id, user_id),
    INDEX idx_user_id (user_id),
    INDEX idx_semester_id (semester_id)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 文件夹表 (folders)
```sql
CREATE TABLE folders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    folder_type VARCHAR(20) NOT NULL COMMENT 'outline, tutorial, lecture, exam, assignment, others',
    course_id INT NOT NULL,
    is_default BOOLEAN DEFAULT FALSE COMMENT '是否为系统默认文件夹',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_folder_per_course (name, course_id),
    INDEX idx_course_id (course_id),
    INDEX idx_folder_type (folder_type)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 文件表 (files) - 优化版
```sql
-- 1. 新增物理文件表
CREATE TABLE physical_files (
    id INT PRIMARY KEY AUTO_INCREMENT,
    file_hash VARCHAR(64) UNIQUE NOT NULL COMMENT 'SHA256哈希',
    file_size INT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    storage_path VARCHAR(500) NOT NULL COMMENT '实际存储路径',
    first_uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reference_count INT DEFAULT 0 COMMENT '引用计数',
    
    INDEX idx_file_hash (file_hash)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. files表
CREATE TABLE files (
    id INT PRIMARY KEY AUTO_INCREMENT,
    physical_file_id INT NOT NULL COMMENT '指向物理文件',
    
    -- 用户层面的文件信息
    original_name VARCHAR(255) NOT NULL COMMENT '用户上传时的文件名',
    file_type VARCHAR(50) NOT NULL,
    
    -- 关联字段
    course_id INT NULL,
    folder_id INT NULL,
    user_id INT NOT NULL,
    
    -- RAG处理相关（共享）
    is_processed BOOLEAN DEFAULT FALSE,
    processing_status VARCHAR(20) DEFAULT 'pending',
    processing_error TEXT NULL,
    processed_at DATETIME NULL,
    chunk_count INT DEFAULT 0,
    content_preview TEXT NULL,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (physical_file_id) REFERENCES physical_files(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    INDEX idx_physical_file_id (physical_file_id),
    INDEX idx_user_id (user_id),
    INDEX idx_course_id (course_id),
    INDEX idx_file_type (file_type)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 全局文件表 (global_files) - 新增
```sql
CREATE TABLE global_files (
    id INT PRIMARY KEY AUTO_INCREMENT,
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    file_size INT,
    mime_type VARCHAR(100),
    upload_path VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64) NULL,
    
    -- 分类管理
    category VARCHAR(50) DEFAULT 'general' COMMENT '分类: general, faq, policy, manual, template',
    tags JSON NULL COMMENT '标签数组',
    description TEXT NULL COMMENT '文件描述',
    
    -- 权限控制
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT TRUE COMMENT '是否对所有用户可见',
    created_by INT NOT NULL,
    
    -- RAG处理相关
    is_processed BOOLEAN DEFAULT FALSE,
    processing_status VARCHAR(20) DEFAULT 'pending',
    processing_error TEXT NULL,
    processed_at DATETIME NULL,
    chunk_count INT DEFAULT 0,
    content_preview TEXT NULL,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_category (category),
    INDEX idx_is_active (is_active),
    INDEX idx_is_public (is_public),
    INDEX idx_created_by (created_by),
    INDEX idx_file_hash (file_hash),
    INDEX idx_processing_status (processing_status)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 文档分块表 (document_chunks) - 与Chroma同步
```sql
CREATE TABLE document_chunks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    physical_file_id INT NULL COMMENT '指向普通物理文件',
    global_file_id INT NULL COMMENT '指向全局文件',
    chunk_text LONGTEXT NOT NULL,
    chunk_index INT,
    token_count INT,
    chroma_id VARCHAR(36) UNIQUE NOT NULL,
    metadata JSON NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (physical_file_id) REFERENCES physical_files(id) ON DELETE CASCADE,
    INDEX idx_physical_file_id (physical_file_id),
    INDEX idx_chroma_id (chroma_id),
    
    -- 确保只能关联一种文件
    CONSTRAINT chk_file_source CHECK (
        (physical_file_id IS NOT NULL AND global_file_id IS NULL) OR
        (physical_file_id IS NULL AND global_file_id IS NOT NULL)
    )
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 聊天表 (chats)
```sql
CREATE TABLE chats (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    chat_type VARCHAR(20) NOT NULL COMMENT 'general, course',
    course_id INT NULL,
    user_id INT NOT NULL,
    custom_prompt TEXT,
    
    -- RAG配置
    rag_enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用RAG检索',
    max_context_length INT DEFAULT 4000 COMMENT '最大上下文长度',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    INDEX idx_user_id (user_id),
    INDEX idx_course_id (course_id),
    INDEX idx_chat_type (chat_type),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 消息表 (messages)
```sql
CREATE TABLE messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    chat_id INT NOT NULL,
    content LONGTEXT NOT NULL,
    role VARCHAR(20) NOT NULL COMMENT 'user, assistant, system',
    
    -- AI相关字段
    model_name VARCHAR(50) NULL COMMENT '使用的模型名称',
    tokens_used INT,
    cost DECIMAL(10,4),
    response_time_ms INT NULL COMMENT '响应时间（毫秒）',
    
    -- RAG相关
    rag_sources JSON NULL COMMENT 'RAG检索的来源文档',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE,
    
    INDEX idx_chat_id (chat_id),
    INDEX idx_role (role),
    INDEX idx_created_at (created_at),
    INDEX idx_model_name (model_name)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 消息文件关联表 (message_files)
```sql
CREATE TABLE message_files (
    id INT PRIMARY KEY AUTO_INCREMENT,
    message_id INT NOT NULL,
    file_id INT NOT NULL,
    
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_message_file (message_id, file_id),
    INDEX idx_message_id (message_id),
    INDEX idx_file_id (file_id)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 🎯 Chroma向量数据库设计

### Collection命名规范
```python
# 课程相关文档
collection_name = f"course_{course_id}_user_{user_id}"

# 全局文档
collection_name = f"global_{category}"

# 消息附件（临时）
collection_name = f"temp_message_{message_id}"
```

### 元数据结构
```python
# 课程文件元数据
metadata = {
    "file_id": int,
    "course_id": int,
    "folder_type": str,
    "file_type": str,
    "user_id": int,
    "chunk_index": int,
    "source_file": str,
    "created_at": str
}

# 全局文件元数据
metadata = {
    "global_file_id": int,
    "category": str,
    "tags": list,
    "is_public": bool,
    "chunk_index": int,
    "source_file": str,
    "created_at": str
}
```

---

## 📊 性能优化索引

### 复合索引
```sql
-- 用户课程查询优化
CREATE INDEX idx_courses_user_semester ON courses(user_id, semester_id, created_at);

-- 聊天查询优化
CREATE INDEX idx_chats_user_updated ON chats(user_id, updated_at DESC);
CREATE INDEX idx_chats_course_updated ON chats(course_id, updated_at DESC);

-- 消息查询优化
CREATE INDEX idx_messages_chat_created ON messages(chat_id, created_at ASC);

-- 文件查询优化
CREATE INDEX idx_files_user_course ON files(user_id, course_id, created_at DESC);
CREATE INDEX idx_files_folder_status ON files(folder_id, processing_status);

-- 分块查询优化
CREATE INDEX idx_chunks_file_index ON document_chunks(file_id, chunk_index);
CREATE INDEX idx_chunks_global_index ON document_chunks(global_file_id, chunk_index);
```

### 统计缓存表
```sql
-- 课程统计缓存（可选）
CREATE TABLE course_stats (
    course_id INT PRIMARY KEY,
    file_count INT DEFAULT 0,
    processed_file_count INT DEFAULT 0,
    chat_count INT DEFAULT 0,
    message_count INT DEFAULT 0,
    total_chunks INT DEFAULT 0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 用户统计缓存（可选）
CREATE TABLE user_stats (
    user_id INT PRIMARY KEY,
    total_files INT DEFAULT 0,
    total_chats INT DEFAULT 0,
    total_messages INT DEFAULT 0,
    total_tokens_used BIGINT DEFAULT 0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 🔧 数据库配置建议

### MySQL配置优化
```ini
[mysqld]
# 基础配置
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci
default-time-zone='+08:00'

# 性能优化
innodb_buffer_pool_size=1G
innodb_log_file_size=256M
innodb_flush_log_at_trx_commit=2
innodb_file_per_table=1

# 全文搜索（用于内容预览搜索）
ft_min_word_len=1
ft_boolean_syntax='+ -><()~*:""&|'
```

### 备份策略
```bash
# 每日备份脚本
mysqldump --single-transaction \
  --routines --triggers \
  --databases campus_llm > backup_$(date +%Y%m%d).sql

# Chroma数据备份
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz ./chroma_db/
```

---

## 📈 数据迁移和扩展

### 从现有设计迁移
```sql
-- 1. 添加新字段
ALTER TABLE files ADD COLUMN file_hash VARCHAR(64) NULL;
ALTER TABLE files ADD COLUMN content_preview TEXT NULL;
ALTER TABLE files ADD COLUMN processing_error TEXT NULL;
ALTER TABLE files ADD COLUMN processed_at DATETIME NULL;
ALTER TABLE files ADD COLUMN chunk_count INT DEFAULT 0;

-- 2. 创建新表
-- （执行上面的CREATE TABLE语句）

-- 3. 迁移现有向量数据
-- （如果有的话，需要重新处理所有文件）
```

### 分片策略（未来扩展）
```sql
-- 按用户分片messages表
CREATE TABLE messages_user_1 LIKE messages;
CREATE TABLE messages_user_2 LIKE messages;
-- ...

-- 按时间分片（如果消息量很大）
CREATE TABLE messages_2025_q1 LIKE messages;
CREATE TABLE messages_2025_q2 LIKE messages;
-- ...
```

这个设计支持：
1. ✅ LangChain + Chroma集成
2. ✅ 动态RAG检索（按课程/全局分类）
3. ✅ 文件去重和缓存
4. ✅ 完整的权限控制
5. ✅ 性能优化
6. ✅ 扩展性预留
