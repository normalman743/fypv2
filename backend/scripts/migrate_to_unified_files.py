#!/usr/bin/env python3
"""
数据库迁移脚本: 合并 files 和 global_files 表
将现有的 global_files 数据迁移到 files 表，并添加新的字段
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Boolean, JSON, Index
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.models.database import Base, engine
from app.models.file import File
from app.models.global_file import GlobalFile


def backup_tables(engine):
    """备份原始表"""
    print("🔄 创建备份表...")
    
    backup_queries = [
        "CREATE TABLE IF NOT EXISTS files_backup AS SELECT * FROM files;",
        "CREATE TABLE IF NOT EXISTS global_files_backup AS SELECT * FROM global_files;",
        "CREATE TABLE IF NOT EXISTS document_chunks_backup AS SELECT * FROM document_chunks;"
    ]
    
    with engine.connect() as conn:
        for query in backup_queries:
            try:
                conn.execute(text(query))
                conn.commit()
                print(f"✅ 备份完成: {query.split()[5]}")
            except Exception as e:
                print(f"⚠️  备份警告: {e}")


def add_new_columns_to_files(engine):
    """为 files 表添加新字段 - 兼容MySQL 5.x版本"""
    print("🔄 为 files 表添加新字段...")
    
    # 首先检查哪些字段已存在
    with engine.connect() as conn:
        # 获取现有字段列表
        result = conn.execute(text("DESCRIBE files"))
        existing_columns = {row[0] for row in result}
        print(f"现有字段: {existing_columns}")
    
    # 需要添加的字段定义
    new_columns = [
        ("scope", "ALTER TABLE files ADD COLUMN scope VARCHAR(20) DEFAULT 'course';"),
        ("visibility", "ALTER TABLE files ADD COLUMN visibility VARCHAR(20) DEFAULT 'private';"),
        ("is_shareable", "ALTER TABLE files ADD COLUMN is_shareable BOOLEAN DEFAULT TRUE;"),
        ("share_settings", "ALTER TABLE files ADD COLUMN share_settings JSON NULL;"),
        ("tags", "ALTER TABLE files ADD COLUMN tags JSON NULL;"),
        ("description", "ALTER TABLE files ADD COLUMN description TEXT NULL;"),
        ("file_size", "ALTER TABLE files ADD COLUMN file_size INT NULL;"),
        ("mime_type", "ALTER TABLE files ADD COLUMN mime_type VARCHAR(100) NULL;"),
        ("file_hash", "ALTER TABLE files ADD COLUMN file_hash VARCHAR(64) NULL;"),
        ("updated_at", "ALTER TABLE files ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;")
    ]
    
    with engine.connect() as conn:
        for column_name, query in new_columns:
            if column_name not in existing_columns:
                try:
                    conn.execute(text(query))
                    conn.commit()
                    print(f"✅ 添加字段 {column_name} 成功")
                except Exception as e:
                    print(f"❌ 添加字段 {column_name} 失败: {e}")
            else:
                print(f"⚠️  字段 {column_name} 已存在，跳过")


def migrate_global_files_to_files(engine):
    """迁移 global_files 数据到 files 表"""
    print("🔄 迁移 global_files 数据到 files 表...")
    
    # 查询要迁移的数据
    migrate_query = """
    INSERT INTO files (
        physical_file_id, original_name, file_type, scope, visibility,
        user_id, is_processed, processing_status, processing_error, 
        processed_at, chunk_count, content_preview, created_at, updated_at,
        file_size, mime_type, file_hash, tags, description, is_shareable
    )
    SELECT 
        -- 尝试通过 file_hash 找到对应的 physical_file_id，如果找不到则创建新的
        COALESCE(pf.id, 0) as physical_file_id,
        gf.original_name,
        COALESCE(
            CASE 
                WHEN gf.mime_type LIKE '%pdf%' THEN 'pdf'
                WHEN gf.mime_type LIKE '%doc%' THEN 'doc'
                WHEN gf.mime_type LIKE '%text%' THEN 'txt'
                ELSE 'unknown'
            END, 'unknown'
        ) as file_type,
        'global' as scope,
        CASE WHEN gf.is_public = 1 THEN 'public' ELSE 'private' END as visibility,
        gf.created_by as user_id,
        gf.is_processed,
        gf.processing_status,
        gf.processing_error,
        gf.processed_at,
        gf.chunk_count,
        gf.content_preview,
        gf.created_at,
        gf.updated_at,
        gf.file_size,
        gf.mime_type,
        gf.file_hash,
        gf.tags,
        gf.description,
        gf.is_active as is_shareable
    FROM global_files gf
    LEFT JOIN physical_files pf ON pf.file_hash = gf.file_hash
    WHERE gf.id NOT IN (
        SELECT DISTINCT gf2.id 
        FROM global_files gf2 
        INNER JOIN files f ON f.file_hash = gf2.file_hash 
        WHERE f.scope = 'global'
    );
    """
    
    with engine.connect() as conn:
        try:
            result = conn.execute(text(migrate_query))
            conn.commit()
            print(f"✅ 成功迁移 {result.rowcount} 条 global_files 记录")
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            return False
    
    return True


def create_missing_physical_files(engine):
    """为没有对应 physical_file 的记录创建物理文件记录"""
    print("🔄 创建缺失的 physical_files 记录...")
    
    # 为 physical_file_id = 0 的记录创建对应的 physical_files
    create_physical_files_query = """
    INSERT INTO physical_files (file_hash, file_size, mime_type, storage_path, first_uploaded_at, reference_count)
    SELECT DISTINCT
        f.file_hash,
        f.file_size,
        f.mime_type,
        CONCAT('global/', f.file_hash, '_', f.original_name) as storage_path,
        f.created_at as first_uploaded_at,
        1 as reference_count
    FROM files f
    WHERE f.physical_file_id = 0 AND f.file_hash IS NOT NULL
    AND f.file_hash NOT IN (SELECT file_hash FROM physical_files WHERE file_hash IS NOT NULL);
    """
    
    # 更新 files 表中的 physical_file_id
    update_physical_file_ids_query = """
    UPDATE files f
    INNER JOIN physical_files pf ON pf.file_hash = f.file_hash
    SET f.physical_file_id = pf.id
    WHERE f.physical_file_id = 0 AND f.file_hash IS NOT NULL;
    """
    
    with engine.connect() as conn:
        try:
            # 创建缺失的 physical_files
            result1 = conn.execute(text(create_physical_files_query))
            conn.commit()
            print(f"✅ 创建了 {result1.rowcount} 条 physical_files 记录")
            
            # 更新 physical_file_id
            result2 = conn.execute(text(update_physical_file_ids_query))
            conn.commit()
            print(f"✅ 更新了 {result2.rowcount} 条 files 记录的 physical_file_id")
            
        except Exception as e:
            print(f"❌ 创建 physical_files 失败: {e}")


def update_document_chunks(engine):
    """更新 document_chunks 表，将 global_file_id 迁移到新的 files 表"""
    print("🔄 更新 document_chunks 表...")
    
    # 为 document_chunks 添加新的 file_id 字段
    add_file_id_query = "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS file_id INT NULL;"
    
    # 更新 document_chunks 的 file_id
    update_chunks_query = """
    UPDATE document_chunks dc
    INNER JOIN files f ON f.file_hash = (
        SELECT gf.file_hash 
        FROM global_files gf 
        WHERE gf.id = dc.global_file_id
    )
    SET dc.file_id = f.id
    WHERE dc.global_file_id IS NOT NULL AND f.scope = 'global';
    """
    
    # 为已有的课程文件也设置 file_id
    update_course_chunks_query = """
    UPDATE document_chunks dc
    INNER JOIN files f ON f.physical_file_id = dc.physical_file_id
    SET dc.file_id = f.id
    WHERE dc.file_id IS NULL AND dc.physical_file_id IS NOT NULL;
    """
    
    with engine.connect() as conn:
        try:
            conn.execute(text(add_file_id_query))
            conn.commit()
            print("✅ 添加 file_id 字段")
            
            result1 = conn.execute(text(update_chunks_query))
            conn.commit()
            print(f"✅ 更新了 {result1.rowcount} 条全局文件的 chunks")
            
            result2 = conn.execute(text(update_course_chunks_query))
            conn.commit()
            print(f"✅ 更新了 {result2.rowcount} 条课程文件的 chunks")
            
        except Exception as e:
            print(f"❌ 更新 document_chunks 失败: {e}")


def create_indexes(engine):
    """创建新的索引以优化查询性能"""
    print("🔄 创建优化索引...")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_files_scope_visibility ON files(scope, visibility);",
        "CREATE INDEX IF NOT EXISTS idx_files_owner_course ON files(user_id, course_id);",
        "CREATE INDEX IF NOT EXISTS idx_files_hash ON files(file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_document_chunks_file_id ON document_chunks(file_id);"
    ]
    
    with engine.connect() as conn:
        for index_query in indexes:
            try:
                conn.execute(text(index_query))
                conn.commit()
                print(f"✅ 创建索引成功")
            except Exception as e:
                print(f"⚠️  索引可能已存在: {e}")


def create_file_sharing_tables(engine):
    """创建文件共享相关的新表"""
    print("🔄 创建文件共享表...")
    
    file_shares_table = """
    CREATE TABLE IF NOT EXISTS file_shares (
        id INT AUTO_INCREMENT PRIMARY KEY,
        file_id INT NOT NULL,
        shared_with_type VARCHAR(20) NOT NULL,
        shared_with_id INT NULL,
        permission_level VARCHAR(20) DEFAULT 'read',
        can_reshare BOOLEAN DEFAULT FALSE,
        download_allowed BOOLEAN DEFAULT TRUE,
        expires_at DATETIME NULL,
        shared_by INT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_accessed DATETIME NULL,
        access_count INT DEFAULT 0,
        
        INDEX idx_share_target (shared_with_type, shared_with_id),
        INDEX idx_file_permissions (file_id, permission_level),
        FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
        FOREIGN KEY (shared_by) REFERENCES users(id)
    );
    """
    
    file_access_logs_table = """
    CREATE TABLE IF NOT EXISTS file_access_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        file_id INT NOT NULL,
        user_id INT NOT NULL,
        action VARCHAR(20) NOT NULL,
        access_via VARCHAR(20) DEFAULT 'direct',
        ip_address VARCHAR(45) NULL,
        user_agent TEXT NULL,
        accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        
        INDEX idx_file_access (file_id, accessed_at),
        INDEX idx_user_access (user_id, accessed_at),
        FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """
    
    with engine.connect() as conn:
        try:
            conn.execute(text(file_shares_table))
            conn.commit()
            print("✅ 创建 file_shares 表")
            
            conn.execute(text(file_access_logs_table))
            conn.commit()
            print("✅ 创建 file_access_logs 表")
            
        except Exception as e:
            print(f"⚠️  表可能已存在: {e}")


def verify_migration(engine):
    """验证迁移结果"""
    print("🔄 验证迁移结果...")
    
    verification_queries = [
        ("文件总数", "SELECT COUNT(*) as count FROM files;"),
        ("全局文件数", "SELECT COUNT(*) as count FROM files WHERE scope = 'global';"),
        ("课程文件数", "SELECT COUNT(*) as count FROM files WHERE scope = 'course';"),
        ("原 global_files 数", "SELECT COUNT(*) as count FROM global_files;"),
        ("chunks 更新数", "SELECT COUNT(*) as count FROM document_chunks WHERE file_id IS NOT NULL;")
    ]
    
    with engine.connect() as conn:
        print("\n📊 迁移统计:")
        for desc, query in verification_queries:
            try:
                result = conn.execute(text(query)).fetchone()
                print(f"  {desc}: {result[0]}")
            except Exception as e:
                print(f"  {desc}: 查询失败 - {e}")


def main():
    """主迁移流程"""
    print("🚀 开始数据库迁移：合并 files 和 global_files 表")
    print(f"数据库连接: {settings.database_url}")
    print(f"迁移时间: {datetime.now()}")
    print("=" * 60)
    
    try:
        # 1. 备份原始表
        backup_tables(engine)
        
        # 2. 为 files 表添加新字段
        add_new_columns_to_files(engine)
        
        # 3. 迁移 global_files 数据
        if migrate_global_files_to_files(engine):
            print("✅ global_files 迁移成功")
        else:
            print("❌ global_files 迁移失败，停止迁移")
            return
        
        # 4. 创建缺失的 physical_files
        create_missing_physical_files(engine)
        
        # 5. 更新 document_chunks
        update_document_chunks(engine)
        
        # 6. 创建优化索引
        create_indexes(engine)
        
        # 7. 创建文件共享表
        create_file_sharing_tables(engine)
        
        # 8. 验证迁移结果
        verify_migration(engine)
        
        print("\n" + "=" * 60)
        print("🎉 数据库迁移完成！")
        print("\n📝 后续步骤:")
        print("1. 更新代码中的模型定义")
        print("2. 重构相关的 service 和 API")
        print("3. 测试迁移后的功能")
        print("4. 备份表可以在确认无误后删除")
        
    except Exception as e:
        print(f"\n❌ 迁移过程中出现错误: {e}")
        print("💡 建议: 检查备份表，必要时可以回滚")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()