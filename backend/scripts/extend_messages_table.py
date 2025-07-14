#!/usr/bin/env python3
"""
扩展messages表字段 - 兼容MySQL版本
"""

import os
import sys
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

def extend_messages_table():
    """扩展messages表字段"""
    engine = create_engine(settings.database_url)
    
    print("🔄 扩展messages表字段...")
    
    with engine.connect() as conn:
        # 检查现有字段
        result = conn.execute(text("DESCRIBE messages"))
        existing_fields = {row[0] for row in result}
        print(f"现有字段: {existing_fields}")
        
        # 需要添加的字段
        fields_to_add = [
            ("context_size", "ALTER TABLE messages ADD COLUMN context_size INT NULL COMMENT '上下文字符数';"),
            ("direct_file_count", "ALTER TABLE messages ADD COLUMN direct_file_count INT DEFAULT 0 COMMENT '直接引用文件数';"),
            ("rag_source_count", "ALTER TABLE messages ADD COLUMN rag_source_count INT DEFAULT 0 COMMENT 'RAG检索源数量';")
        ]
        
        for field_name, sql in fields_to_add:
            if field_name not in existing_fields:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"✅ 添加字段 {field_name} 成功")
                except Exception as e:
                    print(f"❌ 添加字段 {field_name} 失败: {e}")
            else:
                print(f"⚠️  字段 {field_name} 已存在，跳过")

if __name__ == "__main__":
    extend_messages_table()
    print("✅ Messages表扩展完成！")