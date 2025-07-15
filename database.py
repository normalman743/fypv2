#!/usr/bin/env python3
"""
Campus LLM Database Analysis Tool
校园LLM数据库分析工具

完整分析数据库结构，包括表结构、外键关系、索引等信息
"""

import pymysql
import json
from datetime import datetime


# 校园LLM数据库配置
campus_db_config = {
    'host': "39.108.113.103",
    'port': 3306,
    'user': "campus_user",
    'password': "CampusLLM123!",
    'database': "campus_llm_db",
    'charset': 'utf8mb4'
}


def get_connection():
    """获取数据库连接"""
    return pymysql.connect(**campus_db_config)


def get_table_structure():
    """获取所有表的完整结构信息"""
    conn = get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 获取所有表名
            cursor.execute("SHOW TABLES")
            tables = [row[f'Tables_in_{campus_db_config["database"]}'] for row in cursor.fetchall()]
            
            table_info = {}
            
            for table in tables:
                # 获取表结构
                cursor.execute(f"DESCRIBE `{table}`")
                columns = cursor.fetchall()
                
                # 获取表的创建语句（包含索引信息）
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                create_sql = cursor.fetchone()['Create Table']
                
                # 获取表状态信息
                cursor.execute(f"SHOW TABLE STATUS LIKE '{table}'")
                status = cursor.fetchone()
                
                table_info[table] = {
                    'columns': columns,
                    'create_sql': create_sql,
                    'engine': status['Engine'],
                    'collation': status['Collation'],
                    'rows': status['Rows'],
                    'data_length': status['Data_length'],
                    'auto_increment': status['Auto_increment']
                }
            
            return table_info
            
    finally:
        conn.close()


def get_foreign_keys():
    """获取所有外键关系"""
    conn = get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    TABLE_NAME as table_name,
                    COLUMN_NAME as column_name,
                    CONSTRAINT_NAME as constraint_name,
                    REFERENCED_TABLE_NAME as referenced_table,
                    REFERENCED_COLUMN_NAME as referenced_column
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                WHERE REFERENCED_TABLE_SCHEMA = %s
                AND REFERENCED_TABLE_NAME IS NOT NULL
                ORDER BY TABLE_NAME, CONSTRAINT_NAME
            """, (campus_db_config['database'],))
            
            return cursor.fetchall()
            
    finally:
        conn.close()


def get_indexes():
    """获取所有索引信息"""
    conn = get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    TABLE_NAME,
                    INDEX_NAME,
                    COLUMN_NAME,
                    SEQ_IN_INDEX,
                    NON_UNIQUE,
                    INDEX_TYPE
                FROM INFORMATION_SCHEMA.STATISTICS 
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX
            """, (campus_db_config['database'],))
            
            indexes = cursor.fetchall()
            
            # 按表和索引分组
            index_by_table = {}
            for idx in indexes:
                table = idx['TABLE_NAME']
                index_name = idx['INDEX_NAME']
                
                if table not in index_by_table:
                    index_by_table[table] = {}
                
                if index_name not in index_by_table[table]:
                    index_by_table[table][index_name] = {
                        'columns': [],
                        'unique': idx['NON_UNIQUE'] == 0,
                        'type': idx['INDEX_TYPE']
                    }
                
                index_by_table[table][index_name]['columns'].append(idx['COLUMN_NAME'])
            
            return index_by_table
            
    finally:
        conn.close()


def get_table_data_samples():
    """获取每个表的数据样本"""
    conn = get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SHOW TABLES")
            tables = [row[f'Tables_in_{campus_db_config["database"]}'] for row in cursor.fetchall()]
            
            samples = {}
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM `{table}`")
                    count = cursor.fetchone()['count']
                    
                    cursor.execute(f"SELECT * FROM `{table}` LIMIT 3")
                    sample_data = cursor.fetchall()
                    
                    samples[table] = {
                        'total_rows': count,
                        'sample_data': sample_data
                    }
                    
                except Exception as e:
                    samples[table] = {
                        'total_rows': 0,
                        'sample_data': [],
                        'error': str(e)
                    }
            
            return samples
            
    finally:
        conn.close()


def analyze_constraints():
    """分析约束和关系"""
    conn = get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 检查约束
            cursor.execute("""
                SELECT 
                    TABLE_NAME,
                    CONSTRAINT_NAME,
                    CONSTRAINT_TYPE
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
                WHERE CONSTRAINT_SCHEMA = %s
                ORDER BY TABLE_NAME, CONSTRAINT_TYPE
            """, (campus_db_config['database'],))
            
            return cursor.fetchall()
            
    finally:
        conn.close()


def generate_markdown_analysis():
    """生成Markdown格式的数据库分析报告"""
    md_content = []
    
    md_content.append("# 🏫 Campus LLM Database Analysis Report")
    md_content.append("")
    md_content.append(f"- **Database**: {campus_db_config['database']}")
    md_content.append(f"- **Host**: {campus_db_config['host']}")
    md_content.append(f"- **Analysis Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_content.append("")
    
    # 获取数据
    table_structures = get_table_structure()
    foreign_keys = get_foreign_keys()
    indexes = get_indexes()
    constraints = analyze_constraints()
    samples = get_table_data_samples()
    
    # 1. 表结构分析
    md_content.append("## 📋 1. TABLE STRUCTURES")
    md_content.append("")
    
    for table_name, info in table_structures.items():
        md_content.append(f"### 🔹 Table: {table_name}")
        md_content.append(f"- **Engine**: {info['engine']}")
        md_content.append(f"- **Rows**: {info['rows']}")
        md_content.append(f"- **Auto_increment**: {info['auto_increment']}")
        md_content.append("")
        
        md_content.append("| Field | Type | Null | Key | Default | Extra |")
        md_content.append("|-------|------|------|-----|---------|-------|")
        
        for col in info['columns']:
            null_info = "YES" if col['Null'] == 'YES' else "NO"
            key_info = col['Key'] or ""
            default_info = str(col['Default']) if col['Default'] is not None else ""
            extra_info = col['Extra'] or ""
            
            md_content.append(f"| {col['Field']} | {col['Type']} | {null_info} | {key_info} | {default_info} | {extra_info} |")
        
        md_content.append("")
    
    # 2. 外键关系分析
    md_content.append("## 🔗 2. FOREIGN KEY RELATIONSHIPS")
    md_content.append("")
    
    if foreign_keys:
        md_content.append("| Child Table | Child Column | Parent Table | Parent Column | Constraint Name |")
        md_content.append("|-------------|--------------|--------------|---------------|-----------------|")
        
        for fk in foreign_keys:
            md_content.append(f"| {fk['table_name']} | {fk['column_name']} | {fk['referenced_table']} | {fk['referenced_column']} | {fk['constraint_name']} |")
    else:
        md_content.append("No foreign keys found")
    
    md_content.append("")
    
    # 3. 索引分析
    md_content.append("## 📊 3. INDEXES")
    md_content.append("")
    
    for table_name, table_indexes in indexes.items():
        md_content.append(f"### Table: {table_name}")
        md_content.append("")
        
        for index_name, index_info in table_indexes.items():
            unique_str = "UNIQUE" if index_info['unique'] else "INDEX"
            columns_str = ", ".join(index_info['columns'])
            md_content.append(f"- **{unique_str}** `{index_name}` ({columns_str}) [{index_info['type']}]")
        
        md_content.append("")
    
    # 4. 约束分析
    md_content.append("## 🔒 4. CONSTRAINTS")
    md_content.append("")
    
    constraint_by_table = {}
    for constraint in constraints:
        table = constraint['TABLE_NAME']
        if table not in constraint_by_table:
            constraint_by_table[table] = []
        constraint_by_table[table].append(constraint)
    
    for table_name, table_constraints in constraint_by_table.items():
        md_content.append(f"### Table: {table_name}")
        md_content.append("")
        
        for constraint in table_constraints:
            md_content.append(f"- **{constraint['CONSTRAINT_TYPE']}**: {constraint['CONSTRAINT_NAME']}")
        
        md_content.append("")
    
    # 5. 数据样本分析
    md_content.append("## 📈 5. DATA SAMPLES")
    md_content.append("")
    
    md_content.append("| Table | Rows | Sample Fields |")
    md_content.append("|-------|------|---------------|")
    
    for table_name, sample_info in samples.items():
        if 'error' in sample_info:
            md_content.append(f"| {table_name} | ERROR | {sample_info['error']} |")
        else:
            sample_fields = ""
            if sample_info['sample_data'] and sample_info['total_rows'] > 0:
                first_row = sample_info['sample_data'][0]
                fields = list(first_row.keys())[:5]
                sample_fields = ", ".join(fields)
            
            md_content.append(f"| {table_name} | {sample_info['total_rows']} | {sample_fields} |")
    
    md_content.append("")
    
    # 6. 依赖关系图
    md_content.append("## 🌐 6. DEPENDENCY GRAPH")
    md_content.append("")
    md_content.append("Tables dependency order (for safe deletion):")
    md_content.append("")
    
    # 根据外键关系确定删除顺序
    fk_relations = {}
    for fk in foreign_keys:
        child_table = fk['table_name']
        parent_table = fk['referenced_table']
        
        if child_table not in fk_relations:
            fk_relations[child_table] = set()
        fk_relations[child_table].add(parent_table)
    
    # 找出没有外键依赖的表（叶子节点）
    all_tables = set(table_structures.keys())
    dependent_tables = set(fk_relations.keys())
    independent_tables = all_tables - dependent_tables
    
    md_content.append(f"- **Level 0 (Independent)**: {', '.join(sorted(independent_tables))}")
    
    level = 1
    remaining_tables = dependent_tables.copy()
    
    while remaining_tables:
        current_level = []
        for table in list(remaining_tables):
            dependencies = fk_relations[table]
            if not dependencies or dependencies.issubset(all_tables - remaining_tables):
                current_level.append(table)
        
        if current_level:
            md_content.append(f"- **Level {level}**: {', '.join(sorted(current_level))}")
            for table in current_level:
                remaining_tables.remove(table)
            level += 1
        else:
            md_content.append(f"- **Level {level} (Circular dependencies)**: {', '.join(sorted(remaining_tables))}")
            break
    
    md_content.append("")
    
    # 7. 字段长度限制
    md_content.append("## 📏 7. FIELD LENGTH LIMITS")
    md_content.append("")
    md_content.append("Password and hash fields:")
    md_content.append("")
    
    password_fields = []
    for table_name, info in table_structures.items():
        for col in info['columns']:
            if 'password' in col['Field'].lower() or 'hash' in col['Field'].lower():
                password_fields.append(f"- **{table_name}.{col['Field']}**: {col['Type']}")
    
    if password_fields:
        md_content.extend(password_fields)
    else:
        md_content.append("No password/hash fields found")
    
    md_content.append("")
    md_content.append("---")
    md_content.append("✅ **Analysis Complete!**")
    
    return "\n".join(md_content)


def export_schema_json():
    """导出数据库schema为JSON格式"""
    schema_data = {
        'database': campus_db_config['database'],
        'analysis_time': datetime.now().isoformat(),
        'tables': get_table_structure(),
        'foreign_keys': get_foreign_keys(),
        'indexes': get_indexes(),
        'constraints': analyze_constraints(),
        'data_samples': get_table_data_samples()
    }
    
    filename = f"campus_llm_schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(schema_data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"📄 Schema exported to: {filename}")
    return filename


if __name__ == "__main__":
    try:
        print("🏫 Starting Campus LLM Database Analysis...")
        
        # 生成Markdown报告
        print("📝 Generating markdown analysis...")
        markdown_content = generate_markdown_analysis()
        
        # 保存到markdown文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        md_filename = f"campus_llm_database_analysis_{timestamp}.md"
        
        with open(md_filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ Markdown analysis saved to: {md_filename}")
        
        # 导出JSON schema
        print("💾 Exporting schema to JSON...")
        json_filename = export_schema_json()
        
        print(f"""
🎉 Analysis Complete!

Generated files:
📄 Markdown Report: {md_filename}
📊 JSON Schema: {json_filename}

The markdown file contains a detailed analysis of the database structure,
including tables, foreign keys, indexes, constraints, and dependency graph.
        """)
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()