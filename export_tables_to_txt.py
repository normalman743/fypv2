#!/usr/bin/env python3
"""
Export each database table to separate txt files
每个表导出到单独的txt文件
"""

import pymysql
import json
import os
from datetime import datetime
from backend.app.core.config import settings
from urllib.parse import urlparse, unquote

def parse_mysql_url(url):
    """Parse MySQL connection URL"""
    if url.startswith('mysql+pymysql://'):
        url = url.replace('mysql+pymysql://', '')
    elif url.startswith('mysql://'):
        url = url.replace('mysql://', '')
    parsed = urlparse(f"//{url}", scheme='mysql')
    user = unquote(parsed.username) if parsed.username else ''
    password = unquote(parsed.password) if parsed.password else ''
    host = parsed.hostname or 'localhost'
    port = parsed.port or 3306
    database = parsed.path.lstrip('/') if parsed.path else ''
    return {
        'host': host,
        'port': port,
        'user': user,
        'password': password,
        'database': database,
        'charset': 'utf8mb4'
    }

def get_connection():
    """获取数据库连接"""
    database_url = settings.database_url
    db_config = parse_mysql_url(database_url)
    return pymysql.connect(**db_config)

def ensure_output_dir():
    """确保输出目录存在"""
    output_dir = "databaseinfo"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"✅ Created directory: {output_dir}")
    return output_dir

def get_all_tables(cursor):
    """获取所有表名"""
    cursor.execute("SHOW TABLES")
    tables = [list(row.values())[0] for row in cursor.fetchall()]
    return sorted(tables)

def export_table_to_txt(cursor, table_name, output_dir):
    """导出单个表的数据到txt文件"""
    try:
        # 获取表结构
        cursor.execute(f"DESCRIBE `{table_name}`")
        columns = cursor.fetchall()
        
        # 获取表数据
        cursor.execute(f"SELECT * FROM `{table_name}`")
        rows = cursor.fetchall()
        
        # 获取行数
        cursor.execute(f"SELECT COUNT(*) as count FROM `{table_name}`")
        row_count = cursor.fetchone()['count']
        
        # 准备输出内容
        output_data = {
            "table_name": table_name,
            "row_count": row_count,
            "columns": columns,
            "data": []
        }
        
        # 转换数据（处理datetime等特殊类型）
        for row in rows:
            cleaned_row = {}
            for key, value in row.items():
                if isinstance(value, datetime):
                    cleaned_row[key] = value.isoformat()
                elif value is None:
                    cleaned_row[key] = None
                else:
                    cleaned_row[key] = str(value)
            output_data["data"].append(cleaned_row)
        
        # 写入文件
        output_file = os.path.join(output_dir, f"{table_name}.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported {table_name}: {row_count} rows → {output_file}")
        return True, row_count
        
    except Exception as e:
        print(f"❌ Error exporting {table_name}: {str(e)}")
        return False, 0

def create_summary_file(output_dir, table_stats):
    """创建汇总文件"""
    summary_file = os.path.join(output_dir, "_summary.txt")
    
    summary_data = {
        "export_time": datetime.now().isoformat(),
        "total_tables": len(table_stats),
        "tables": table_stats
    }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 Summary saved to: {summary_file}")

def main():
    """主函数"""
    print("🏫 Starting database export...")
    print(f"⏰ Export time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 创建输出目录
    output_dir = ensure_output_dir()
    
    # 连接数据库
    conn = get_connection()
    table_stats = []
    
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 获取所有表
            tables = get_all_tables(cursor)
            print(f"\n📋 Found {len(tables)} tables to export\n")
            
            # 导出每个表
            for table_name in tables:
                success, row_count = export_table_to_txt(cursor, table_name, output_dir)
                table_stats.append({
                    "table": table_name,
                    "success": success,
                    "rows": row_count
                })
            
            # 创建汇总文件
            create_summary_file(output_dir, table_stats)
            
            # 打印统计信息
            success_count = sum(1 for stat in table_stats if stat["success"])
            total_rows = sum(stat["rows"] for stat in table_stats)
            
            print(f"""
🎉 Export Complete!

📊 Statistics:
- Total tables: {len(tables)}
- Successfully exported: {success_count}
- Failed: {len(tables) - success_count}
- Total rows exported: {total_rows:,}

📁 Output directory: {output_dir}/
            """)
            
    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()