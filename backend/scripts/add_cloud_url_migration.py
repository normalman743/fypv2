#!/usr/bin/env python3
"""
数据库迁移脚本：为File表添加cloud_url字段
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate_add_cloud_url():
    """为File表添加cloud_url字段"""
    
    # 创建数据库连接
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        try:
            # 检查字段是否已存在
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM pragma_table_info('files') 
                WHERE name = 'cloud_url'
            """))
            
            if result.fetchone()[0] == 0:
                # 添加cloud_url字段
                conn.execute(text("""
                    ALTER TABLE files 
                    ADD COLUMN cloud_url VARCHAR(512)
                """))
                print("✅ 成功添加 cloud_url 字段到 files 表")
            else:
                print("ℹ️ cloud_url 字段已存在")
            
            conn.commit()
            
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    print("🔄 开始数据库迁移：添加 cloud_url 字段...")
    migrate_add_cloud_url()
    print("✅ 迁移完成！") 