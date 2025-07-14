#!/usr/bin/env python3
"""
修复 document_chunks 表，添加 file_id 字段并更新数据
"""

import os
import sys
from sqlalchemy import create_engine, text

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def fix_document_chunks():
    """修复 document_chunks 表"""
    engine = create_engine(settings.database_url)
    
    print("🔄 修复 document_chunks 表...")
    
    with engine.connect() as conn:
        # 1. 检查 file_id 字段是否存在
        result = conn.execute(text("DESCRIBE document_chunks"))
        existing_columns = {row[0] for row in result}
        
        if 'file_id' not in existing_columns:
            print("🔄 添加 file_id 字段...")
            conn.execute(text("ALTER TABLE document_chunks ADD COLUMN file_id INT NULL;"))
            conn.commit()
            print("✅ 添加 file_id 字段成功")
        else:
            print("⚠️  file_id 字段已存在")
        
        # 2. 为课程文件更新 file_id
        print("🔄 更新课程文件的 chunks...")
        update_course_chunks_query = """
        UPDATE document_chunks dc
        INNER JOIN files f ON f.physical_file_id = dc.physical_file_id
        SET dc.file_id = f.id
        WHERE dc.file_id IS NULL AND dc.physical_file_id IS NOT NULL;
        """
        
        result = conn.execute(text(update_course_chunks_query))
        conn.commit()
        print(f"✅ 更新了 {result.rowcount} 条课程文件的 chunks")
        
        # 3. 创建索引
        print("🔄 创建索引...")
        indexes = [
            "CREATE INDEX idx_files_scope_visibility ON files(scope, visibility);",
            "CREATE INDEX idx_files_owner_course ON files(user_id, course_id);", 
            "CREATE INDEX idx_files_hash ON files(file_hash);",
            "CREATE INDEX idx_document_chunks_file_id ON document_chunks(file_id);"
        ]
        
        for index_query in indexes:
            try:
                conn.execute(text(index_query))
                conn.commit()
                print(f"✅ 创建索引成功")
            except Exception as e:
                print(f"⚠️  索引可能已存在: {e}")
        
        # 4. 验证结果
        print("🔄 验证修复结果...")
        
        verification_queries = [
            ("文件总数", "SELECT COUNT(*) as count FROM files;"),
            ("全局文件数", "SELECT COUNT(*) as count FROM files WHERE scope = 'global';"),
            ("课程文件数", "SELECT COUNT(*) as count FROM files WHERE scope = 'course';"),
            ("chunks 已关联文件数", "SELECT COUNT(*) as count FROM document_chunks WHERE file_id IS NOT NULL;"),
            ("chunks 总数", "SELECT COUNT(*) as count FROM document_chunks;")
        ]
        
        print("\n📊 修复后统计:")
        for desc, query in verification_queries:
            try:
                result = conn.execute(text(query)).fetchone()
                print(f"  {desc}: {result[0]}")
            except Exception as e:
                print(f"  {desc}: 查询失败 - {e}")

if __name__ == "__main__":
    fix_document_chunks()
    print("\n✅ document_chunks 表修复完成！")