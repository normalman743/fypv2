#!/usr/bin/env python3
"""
修复文件哈希值 - 将 physical_files 中的哈希值同步到 files 表
"""

import os
import sys
from sqlalchemy import create_engine, text

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def fix_file_hashes():
    """修复文件哈希值"""
    engine = create_engine(settings.database_url)
    
    print("🔄 修复文件哈希值...")
    
    with engine.connect() as conn:
        # 1. 统计需要修复的文件数量
        count_query = """
        SELECT COUNT(*) as count 
        FROM files f 
        INNER JOIN physical_files pf ON f.physical_file_id = pf.id 
        WHERE f.file_hash IS NULL AND pf.file_hash IS NOT NULL;
        """
        
        result = conn.execute(text(count_query)).fetchone()
        need_fix_count = result[0]
        
        print(f"📊 发现 {need_fix_count} 个文件需要修复哈希值")
        
        if need_fix_count == 0:
            print("✅ 所有文件哈希值已经正确，无需修复")
            return
        
        # 2. 更新 files 表的 file_hash 字段
        print("🔄 同步哈希值从 physical_files 到 files...")
        
        update_query = """
        UPDATE files f 
        INNER JOIN physical_files pf ON f.physical_file_id = pf.id 
        SET f.file_hash = pf.file_hash,
            f.file_size = pf.file_size,
            f.mime_type = pf.mime_type
        WHERE f.file_hash IS NULL AND pf.file_hash IS NOT NULL;
        """
        
        result = conn.execute(text(update_query))
        conn.commit()
        
        print(f"✅ 成功更新了 {result.rowcount} 个文件的哈希值")
        
        # 3. 验证修复结果
        print("🔄 验证修复结果...")
        
        verification_queries = [
            ("总文件数", "SELECT COUNT(*) FROM files;"),
            ("有哈希值的文件数", "SELECT COUNT(*) FROM files WHERE file_hash IS NOT NULL;"),
            ("无哈希值的文件数", "SELECT COUNT(*) FROM files WHERE file_hash IS NULL;"),
            ("相同哈希值的文件组数", """
                SELECT COUNT(*) FROM (
                    SELECT file_hash, COUNT(*) as cnt 
                    FROM files 
                    WHERE file_hash IS NOT NULL 
                    GROUP BY file_hash 
                    HAVING cnt > 1
                ) AS duplicates;
            """)
        ]
        
        print("\n📊 修复后统计:")
        for desc, query in verification_queries:
            try:
                result = conn.execute(text(query)).fetchone()
                print(f"  {desc}: {result[0]}")
            except Exception as e:
                print(f"  {desc}: 查询失败 - {e}")
        
        # 4. 显示一些示例数据
        print("\n📋 文件哈希示例:")
        sample_query = """
        SELECT f.id, f.original_name, f.file_hash, f.scope 
        FROM files f 
        WHERE f.file_hash IS NOT NULL 
        LIMIT 5;
        """
        
        results = conn.execute(text(sample_query)).fetchall()
        for row in results:
            print(f"  ID: {row[0]}, 名称: {row[1]}, 哈希: {row[2][:16]}..., 作用域: {row[3]}")

if __name__ == "__main__":
    fix_file_hashes()
    print("\n✅ 文件哈希值修复完成！")