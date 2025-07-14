#!/usr/bin/env python3
"""
创建缺失的数据库表
"""

import os
import sys
from sqlalchemy import create_engine, text

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def create_missing_tables():
    """创建缺失的数据库表"""
    engine = create_engine(settings.database_url)
    
    print("🔄 创建缺失的数据库表...")
    
    # 1. 创建消息文件引用表
    message_file_references_sql = """
    CREATE TABLE IF NOT EXISTS message_file_references (
        id INT AUTO_INCREMENT PRIMARY KEY,
        message_id INT NOT NULL,
        file_id INT NOT NULL,
        reference_type ENUM('file', 'folder') NOT NULL DEFAULT 'file',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        
        INDEX idx_message_refs (message_id),
        INDEX idx_file_refs (file_id, reference_type),
        FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 2. 创建通用权限表
    permissions_sql = """
    CREATE TABLE IF NOT EXISTS permissions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        
        -- 资源标识
        resource_type VARCHAR(50) NOT NULL,
        resource_id VARCHAR(100) NOT NULL,
        
        -- 主体标识  
        subject_type VARCHAR(50) NOT NULL,
        subject_id VARCHAR(100) NOT NULL,
        
        -- 权限定义
        action VARCHAR(50) NOT NULL,
        effect ENUM('allow', 'deny') DEFAULT 'allow',
        
        -- 条件和管理
        conditions JSON NULL,
        metadata JSON NULL,
        granted_by INT NULL,
        granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME NULL,
        is_active BOOLEAN DEFAULT TRUE,
        
        -- 索引优化
        INDEX idx_resource (resource_type, resource_id),
        INDEX idx_subject (subject_type, subject_id),
        INDEX idx_action (action),
        INDEX idx_active_permissions (is_active, expires_at),
        
        FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 3. 创建角色表
    roles_sql = """
    CREATE TABLE IF NOT EXISTS roles (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        scope_type VARCHAR(50) DEFAULT 'global',
        scope_id VARCHAR(100) NULL,
        is_system BOOLEAN DEFAULT FALSE,
        is_active BOOLEAN DEFAULT TRUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        
        INDEX idx_name (name),
        INDEX idx_scope (scope_type, scope_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 4. 创建主体-角色关联表
    subject_roles_sql = """
    CREATE TABLE IF NOT EXISTS subject_roles (
        id INT AUTO_INCREMENT PRIMARY KEY,
        subject_type VARCHAR(50) NOT NULL,
        subject_id VARCHAR(100) NOT NULL,
        role_id INT NOT NULL,
        scope_type VARCHAR(50) NULL,
        scope_id VARCHAR(100) NULL,
        assigned_by INT NULL,
        assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME NULL,
        is_active BOOLEAN DEFAULT TRUE,
        
        INDEX idx_subject_role (subject_type, subject_id, role_id),
        INDEX idx_scope (scope_type, scope_id),
        INDEX idx_active (is_active, expires_at),
        
        FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 5. 扩展messages表
    extend_messages_sql = [
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS context_size INT NULL COMMENT '上下文字符数';",
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS direct_file_count INT DEFAULT 0 COMMENT '直接引用文件数';",
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS rag_source_count INT DEFAULT 0 COMMENT 'RAG检索源数量';"
    ]
    
    tables_to_create = [
        ("消息文件引用表", message_file_references_sql),
        ("通用权限表", permissions_sql),
        ("角色表", roles_sql),
        ("主体角色关联表", subject_roles_sql)
    ]
    
    with engine.connect() as conn:
        # 创建表
        for table_name, sql in tables_to_create:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"✅ 创建{table_name}成功")
            except Exception as e:
                print(f"⚠️  创建{table_name}失败或已存在: {e}")
        
        # 扩展messages表
        print("\n🔄 扩展messages表字段...")
        for sql in extend_messages_sql:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"✅ 扩展字段成功")
            except Exception as e:
                print(f"⚠️  扩展字段失败或已存在: {e}")
    
    print("\n🔄 插入系统默认角色...")
    insert_default_roles(engine)
    
    print("\n🔄 验证表创建结果...")
    verify_tables(engine)

def insert_default_roles(engine):
    """插入系统默认角色"""
    
    default_roles = [
        ('admin', '系统管理员', True),
        ('course_owner', '课程所有者', True),
        ('course_collaborator', '课程协作者', True),
        ('course_member', '课程成员', True),
        ('file_owner', '文件所有者', True)
    ]
    
    with engine.connect() as conn:
        for role_name, description, is_system in default_roles:
            try:
                # 检查是否已存在
                result = conn.execute(text(
                    "SELECT COUNT(*) FROM roles WHERE name = :name"
                ), {"name": role_name})
                
                if result.fetchone()[0] == 0:
                    conn.execute(text(
                        "INSERT INTO roles (name, description, is_system) VALUES (:name, :desc, :is_system)"
                    ), {"name": role_name, "desc": description, "is_system": is_system})
                    print(f"✅ 插入角色: {role_name}")
                else:
                    print(f"⚠️  角色已存在: {role_name}")
            except Exception as e:
                print(f"❌ 插入角色失败 {role_name}: {e}")
        
        conn.commit()

def verify_tables(engine):
    """验证表创建结果"""
    
    tables_to_verify = [
        'message_file_references',
        'permissions', 
        'roles',
        'subject_roles'
    ]
    
    with engine.connect() as conn:
        print("\n📊 表创建验证:")
        for table in tables_to_verify:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                print(f"  ✅ {table}: {count} 条记录")
            except Exception as e:
                print(f"  ❌ {table}: 验证失败 - {e}")
        
        # 验证messages表扩展字段
        print("\n📊 Messages表字段验证:")
        result = conn.execute(text("DESCRIBE messages"))
        message_fields = [row[0] for row in result]
        
        new_fields = ['context_size', 'direct_file_count', 'rag_source_count']
        for field in new_fields:
            if field in message_fields:
                print(f"  ✅ messages.{field}: 存在")
            else:
                print(f"  ❌ messages.{field}: 缺失")

if __name__ == "__main__":
    create_missing_tables()
    print("\n🎉 数据库表创建完成！")