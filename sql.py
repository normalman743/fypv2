import os
import glob

def remove_drop_line_22(file_path):
    """删除SQL文件第22行的DROP命令"""
    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 检查第22行是否存在且包含DROP
        if len(lines) >= 22:
            line_22 = lines[21].strip().upper()  # 第22行，索引21
            if 'DROP' in line_22:
                print(f"删除第22行: {lines[21].strip()}")
                lines.pop(21)  # 删除第22行
                
                # 写回文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                print(f"✓ 已处理: {os.path.basename(file_path)}")
            else:
                print(f"- 第22行不是DROP命令: {os.path.basename(file_path)}")
        else:
            print(f"- 文件行数不足22行: {os.path.basename(file_path)}")
            
    except Exception as e:
        print(f"✗ 处理文件错误 {os.path.basename(file_path)}: {e}")

def process_all_sql_files(dump_dir):
    """处理指定目录下的所有campus_llm_db_*.sql文件"""
    # 查找所有匹配的SQL文件
    pattern = os.path.join(dump_dir, "campus_llm_db_*.sql")
    sql_files = glob.glob(pattern)
    
    if not sql_files:
        print(f"在 {dump_dir} 中未找到匹配的SQL文件")
        return
    
    print(f"找到 {len(sql_files)} 个SQL文件:")
    for sql_file in sorted(sql_files):
        remove_drop_line_22(sql_file)

# 使用示例
dump_directory = "/Users/mannormal/dumps/Dump20250726"
process_all_sql_files(dump_directory)