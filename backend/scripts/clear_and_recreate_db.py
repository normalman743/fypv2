#!/usr/bin/env python3
"""
清理测试数据并重新创建数据库结构
"""

import os
import sys
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

def clear_and_recreate_database():
    """清理所有测试数据并重新创建表结构"""
    engine = create_engine(settings.database_url)
    
    print("🧹 清理测试数据并重新创建数据库结构...")
    
    with engine.connect() as conn:
        # 1. 删除所有文件相关测试数据（保留用户和课程）
        tables_to_clear = [
            'document_chunks',
            'message_file_references', 
            'file_shares',
            'file_access_logs',
            'file_groups',
            'file_group_members',
            'global_files',  # 如果还存在
            'files',
            'physical_files'
        ]
        
        for table in tables_to_clear:
            try:
                conn.execute(text(f"DELETE FROM {table}"))
                print(f"✅ 清空表: {table}")
            except Exception as e:
                print(f"⚠️  表 {table} 不存在或清空失败: {e}")
        
        # 2. 重置AUTO_INCREMENT
        reset_tables = ['files', 'physical_files', 'document_chunks']
        for table in reset_tables:
            try:
                conn.execute(text(f"ALTER TABLE {table} AUTO_INCREMENT = 1"))
                print(f"✅ 重置自增ID: {table}")
            except Exception as e:
                print(f"⚠️  重置自增ID失败 {table}: {e}")
        
        # 3. 更新files表结构 - 添加新字段
        new_fields = [
            "ALTER TABLE files ADD COLUMN IF NOT EXISTS scope VARCHAR(20) NOT NULL DEFAULT 'course'",
            "ALTER TABLE files ADD COLUMN IF NOT EXISTS visibility VARCHAR(20) DEFAULT 'private'", 
            "ALTER TABLE files ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64) NULL",
            "ALTER TABLE files ADD COLUMN IF NOT EXISTS tags JSON NULL",
            "ALTER TABLE files ADD COLUMN IF NOT EXISTS is_shareable BOOLEAN DEFAULT TRUE",
            "ALTER TABLE files ADD COLUMN IF NOT EXISTS share_settings JSON NULL"
        ]
        
        print("\n🔧 更新files表结构...")
        for sql in new_fields:
            try:
                conn.execute(text(sql))
                print(f"✅ 添加字段成功")
            except Exception as e:
                print(f"⚠️  添加字段失败或已存在: {e}")
        
        # 4. 创建新索引
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_files_scope ON files(scope)",
            "CREATE INDEX IF NOT EXISTS idx_files_visibility ON files(visibility)",
            "CREATE INDEX IF NOT EXISTS idx_files_hash ON files(file_hash)",
            "CREATE INDEX IF NOT EXISTS idx_files_user_course ON files(user_id, course_id)"
        ]
        
        print("\n📊 创建索引...")
        for sql in indexes:
            try:
                conn.execute(text(sql))
                print(f"✅ 创建索引成功")
            except Exception as e:
                print(f"⚠️  创建索引失败或已存在: {e}")
        
        conn.commit()
        
        # 5. 删除global_files表（如果存在）
        try:
            conn.execute(text("DROP TABLE IF EXISTS global_files"))
            print("✅ 删除global_files表")
        except Exception as e:
            print(f"⚠️  删除global_files表失败: {e}")
        
        conn.commit()
    
    print("\n🔄 创建缺失的表...")
    create_missing_tables(engine)
    
    print("\n🔄 验证表结构...")
    verify_database_structure(engine)

def create_missing_tables(engine):
    """创建缺失的表"""
    
    # 文件共享表
    file_shares_sql = """
    CREATE TABLE IF NOT EXISTS file_shares (
        id INT AUTO_INCREMENT PRIMARY KEY,
        file_id INT NOT NULL,
        shared_with_type VARCHAR(20) NOT NULL,
        shared_with_id INT NULL,
        permission_level VARCHAR(20) DEFAULT 'read',
        expires_at DATETIME NULL,
        shared_by INT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        
        INDEX idx_file_shared (file_id),
        INDEX idx_shared_with (shared_with_type, shared_with_id),
        FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
        FOREIGN KEY (shared_by) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 消息文件引用表
    message_file_references_sql = """
    CREATE TABLE IF NOT EXISTS message_file_references (
        id INT AUTO_INCREMENT PRIMARY KEY,
        message_id INT NOT NULL,
        file_id INT NOT NULL,
        reference_type ENUM('file', 'folder') NOT NULL DEFAULT 'file',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        
        INDEX idx_message_refs (message_id),
        INDEX idx_file_refs (file_id, reference_type),
        FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
        FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 权限表
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
    
    # 角色表
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
    
    # 主体角色关联表
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
    
    tables_to_create = [
        ("文件共享表", file_shares_sql),
        ("消息文件引用表", message_file_references_sql),
        ("通用权限表", permissions_sql),
        ("角色表", roles_sql),
        ("主体角色关联表", subject_roles_sql)
    ]
    
    with engine.connect() as conn:
        for table_name, sql in tables_to_create:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"✅ 创建{table_name}成功")
            except Exception as e:
                print(f"⚠️  创建{table_name}失败或已存在: {e}")
        
        # 扩展messages表
        extend_messages_fields = [
            "ALTER TABLE messages ADD COLUMN context_size INT NULL COMMENT '上下文字符数'",
            "ALTER TABLE messages ADD COLUMN direct_file_count INT DEFAULT 0 COMMENT '直接引用文件数'", 
            "ALTER TABLE messages ADD COLUMN rag_source_count INT DEFAULT 0 COMMENT 'RAG检索源数量'"
        ]
        
        print("\n🔧 扩展messages表...")
        for sql in extend_messages_fields:
            try:
                conn.execute(text(sql))
                print(f"✅ 扩展messages表字段成功")
            except Exception as e:
                print(f"⚠️  扩展messages表字段失败或已存在: {e}")
        
        conn.commit()
        
        # 插入默认角色
        print("\n🔧 插入系统默认角色...")
        default_roles = [
            ('admin', '系统管理员', True),
            ('course_owner', '课程所有者', True),
            ('course_collaborator', '课程协作者', True),
            ('course_member', '课程成员', True),
            ('file_owner', '文件所有者', True)
        ]
        
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

def verify_database_structure(engine):
    """验证数据库结构"""
    
    tables_to_verify = [
        'files',
        'physical_files', 
        'file_shares',
        'message_file_references',
        'permissions',
        'roles',
        'subject_roles',
        'document_chunks'
    ]
    
    with engine.connect() as conn:
        print("\n📊 数据库结构验证:")
        for table in tables_to_verify:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                print(f"  ✅ {table}: {count} 条记录")
            except Exception as e:
                print(f"  ❌ {table}: 验证失败 - {e}")
        
        # 验证files表字段
        print("\n📊 Files表字段验证:")
        result = conn.execute(text("DESCRIBE files"))
        file_fields = [row[0] for row in result]
        
        required_fields = ['scope', 'visibility', 'file_hash', 'tags', 'is_shareable', 'share_settings']
        for field in required_fields:
            if field in file_fields:
                print(f"  ✅ files.{field}: 存在")
            else:
                print(f"  ❌ files.{field}: 缺失")
        
        # 验证messages表字段
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
    clear_and_recreate_database()
    print("\n🎉 数据库清理和重建完成！")