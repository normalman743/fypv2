import pymysql

# 目标数据库配置
target_db_config = {
    'host': "39.108.113.103",
    'port': 3306,
    'user': "ask_optism",
    'password': "123456",
    'database': "ask_optism",
    'charset': 'utf8mb4'
}




# 源数据库配置
source_db_config = {
    'host': 'optism.co',
    'port': 3306,
    'user': 'landgreen_user',
    'password': '4ClIjnx?F?b8z_JN3++F+z}l+',
    'database': 'optism_api',
    'charset': 'utf8mb4'
}

def get_db_schema(db='source'):
    """
    获取数据库表结构
    :param db: 'source' 或 'target'，默认 'source'
    :return: {table: [(col_name, col_type), ...], ...}
    """
    config = source_db_config if db == 'source' else target_db_config
    conn = pymysql.connect(**config)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES;")
            tables = [row[0] for row in cursor.fetchall()]
            schema = {}
            for table in tables:
                cursor.execute(f"DESCRIBE `{table}`;")
                columns = [(col[0], col[1]) for col in cursor.fetchall()]
                schema[table] = columns
            return schema
    finally:
        conn.close()

def get_table_sample_data(table_name, limit=5, db='source'):
    """
    获取表的示例数据
    :param table_name: 表名
    :param limit: 返回的行数限制
    :param db: 'source' 或 'target'，默认 'source'
    :return: 示例数据
    """
    config = source_db_config if db == 'source' else target_db_config
    conn = pymysql.connect(**config)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(f"SELECT * FROM `{table_name}` LIMIT {limit};")
            return cursor.fetchall()
    finally:
        conn.close()

def analyze_drupal_content():
    """
    分析Drupal内容结构，重点关注文章相关的表
    """
    print("=== 分析Drupal数据库结构 ===\n")
    
    # 1. 查看node表的基本信息
    print("1. Node表 (内容节点)")
    node_data = get_table_sample_data('node_field_data', 10)
    for item in node_data:
        print(f"  ID: {item['nid']}, 类型: {item['type']}, 标题: {item['title']}, 状态: {item['status']}")
    print()
    
    # 2. 查看文章内容（body）
    print("2. 文章内容 (node__body)")
    body_data = get_table_sample_data('node__body', 3)
    for item in body_data:
        content_preview = item['body_value'][:200] + "..." if len(item['body_value']) > 200 else item['body_value']
        print(f"  Node ID: {item['entity_id']}")
        print(f"  内容预览: {content_preview}")
        print(f"  格式: {item['body_format']}")
        print()
    
    # 3. 查看分类信息
    print("3. 分类信息 (taxonomy_term_field_data)")
    category_data = get_table_sample_data('taxonomy_term_field_data', 10)
    for item in category_data:
        print(f"  分类ID: {item['tid']}, 名称: {item['name']}, 词汇表: {item['vid']}")
    print()
    
    # 4. 查看文章的分类关联
    print("4. 文章分类关联 (node__field_category)")
    node_category_data = get_table_sample_data('node__field_category', 10)
    for item in node_category_data:
        print(f"  文章ID: {item['entity_id']}, 分类ID: {item['field_category_target_id']}")
    print()
    
    # 5. 查看段落内容
    print("5. 段落内容 (paragraphs_item_field_data)")
    paragraph_data = get_table_sample_data('paragraphs_item_field_data', 5)
    for item in paragraph_data:
        print(f"  段落ID: {item['id']}, 类型: {item['type']}, 父级ID: {item['parent_id']}, 父级类型: {item['parent_type']}")
    print()

def analyze_paragraph_content():
    """
    详细分析段落内容
    """
    print("=== 详细分析段落内容 ===\n")
    
    # 查看段落的文本内容
    print("1. 段落文本内容 (paragraph__field_text)")
    try:
        text_data = get_table_sample_data('paragraph__field_text', 5)
        for item in text_data:
            content_preview = item['field_text_value'][:300] + "..." if len(item['field_text_value']) > 300 else item['field_text_value']
            print(f"  段落ID: {item['entity_id']}")
            print(f"  内容: {content_preview}")
            print(f"  格式: {item['field_text_format']}")
            print()
    except Exception as e:
        print(f"  获取段落文本失败: {e}")
    
    # 查看段落的纯文本内容  
    print("2. 段落纯文本内容 (paragraph__field_text_plain)")
    try:
        plain_text_data = get_table_sample_data('paragraph__field_text_plain', 5)
        for item in plain_text_data:
            content_preview = item['field_text_plain_value'][:300] + "..." if len(item['field_text_plain_value']) > 300 else item['field_text_plain_value']
            print(f"  段落ID: {item['entity_id']}")
            print(f"  纯文本内容: {content_preview}")
            print()
    except Exception as e:
        print(f"  获取段落纯文本失败: {e}")
    
    # 查看段落标题
    print("3. 段落标题 (paragraph__field_title)")
    try:
        title_data = get_table_sample_data('paragraph__field_title', 10)
        for item in title_data:
            print(f"  段落ID: {item['entity_id']}, 标题: {item['field_title_value']}")
    except Exception as e:
        print(f"  获取段落标题失败: {e}")
    print()

def get_complete_article_structure():
    """
    获取完整的文章结构
    """
    print("=== 完整文章结构分析 ===\n")
    
    # 查看一个完整的文章示例
    config = source_db_config
    conn = pymysql.connect(**config)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 获取一个英文文章
            cursor.execute("""
                SELECT nfd.nid, nfd.title, nfd.langcode, nfd.type, nfd.created, nfd.changed
                FROM node_field_data nfd 
                WHERE nfd.type = 'article' AND nfd.langcode = 'en' AND nfd.status = 1
                LIMIT 1
            """)
            article = cursor.fetchone()
            
            if article:
                nid = article['nid']
                print(f"分析文章: {article['title']} (ID: {nid})")
                print(f"语言: {article['langcode']}, 类型: {article['type']}")
                print()
                
                # 获取文章正文
                cursor.execute("""
                    SELECT body_value, body_summary, body_format 
                    FROM node__body 
                    WHERE entity_id = %s AND langcode = 'en'
                """, (nid,))
                body = cursor.fetchone()
                if body:
                    print("文章正文预览:")
                    content_preview = body['body_value'][:500] + "..." if len(body['body_value']) > 500 else body['body_value']
                    print(f"  {content_preview}")
                    print(f"  格式: {body['body_format']}")
                    print()
                
                # 获取文章分类
                cursor.execute("""
                    SELECT nc.field_category_target_id, ttfd.name as category_name
                    FROM node__field_category nc
                    JOIN taxonomy_term_field_data ttfd ON nc.field_category_target_id = ttfd.tid
                    WHERE nc.entity_id = %s AND nc.langcode = 'en' AND ttfd.langcode = 'en'
                """, (nid,))
                categories = cursor.fetchall()
                if categories:
                    print("文章分类:")
                    for cat in categories:
                        print(f"  分类ID: {cat['field_category_target_id']}, 名称: {cat['category_name']}")
                    print()
                
                # 获取文章段落
                cursor.execute("""
                    SELECT ns.field_sections_target_id as paragraph_id, 
                           pifd.type as paragraph_type,
                           pifd.parent_field_name
                    FROM node__field_sections ns
                    JOIN paragraphs_item_field_data pifd ON ns.field_sections_target_id = pifd.id
                    WHERE ns.entity_id = %s AND ns.langcode = 'en'
                    ORDER BY ns.delta
                """, (nid,))
                paragraphs = cursor.fetchall()
                if paragraphs:
                    print("文章段落:")
                    for para in paragraphs:
                        print(f"  段落ID: {para['paragraph_id']}, 类型: {para['paragraph_type']}, 字段: {para['parent_field_name']}")
                    print()
    finally:
        conn.close()

def analyze_paragraph_language_issue():
    """
    专门分析段落语言分离问题
    """
    print("=== 分析段落语言分离问题 ===\n")
    
    config = source_db_config
    conn = pymysql.connect(**config)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 1. 找一个有中英文版本的文章
            cursor.execute("""
                SELECT nfd.nid, nfd.title, nfd.langcode
                FROM node_field_data nfd 
                WHERE nfd.type = 'article' AND nfd.status = 1
                AND nfd.nid IN (
                    SELECT nid FROM node_field_data 
                    WHERE type = 'article' AND status = 1 AND langcode = 'en'
                    AND nid IN (
                        SELECT nid FROM node_field_data 
                        WHERE type = 'article' AND status = 1 AND langcode = 'zh-hant'
                    )
                )
                ORDER BY nfd.nid, nfd.langcode
                LIMIT 4
            """)
            articles = cursor.fetchall()
            
            if articles:
                nid = articles[0]['nid']
                print(f"分析文章 ID: {nid}")
                for art in articles:
                    if art['nid'] == nid:
                        print(f"  {art['langcode']}: {art['title']}")
                print()
                
                # 2. 查看段落表关联方式
                cursor.execute("""
                    SELECT DISTINCT 
                        pifd.id as paragraph_id,
                        pifd.type as paragraph_type,
                        pifd.parent_id,
                        pifd.parent_type,
                        pifd.parent_field_name,
                        pifd.langcode
                    FROM paragraphs_item_field_data pifd
                    WHERE pifd.parent_id = %s
                    AND pifd.parent_type = 'node'
                    ORDER BY pifd.langcode, pifd.id
                """, (str(nid),))
                paragraphs = cursor.fetchall()
                
                print("段落关联信息:")
                for para in paragraphs:
                    print(f"  段落ID: {para['paragraph_id']}, 语言: {para['langcode']}, 类型: {para['paragraph_type']}, 父级: {para['parent_id']}")
                print()
                
                # 3. 查看段落内容
                for para in paragraphs:
                    cursor.execute("""
                        SELECT field_text_value 
                        FROM paragraph__field_text 
                        WHERE entity_id = %s
                        LIMIT 1
                    """, (para['paragraph_id'],))
                    text_result = cursor.fetchone()
                    
                    if text_result and text_result['field_text_value']:
                        content = text_result['field_text_value'][:150] + "..." if len(text_result['field_text_value']) > 150 else text_result['field_text_value']
                        print(f"段落 {para['paragraph_id']} ({para['langcode']}):")
                        print(f"  内容: {content}")
                        print()
                
                # 4. 查看node__field_sections关联
                cursor.execute("""
                    SELECT entity_id, field_sections_target_id, delta, langcode
                    FROM node__field_sections
                    WHERE entity_id = %s
                    ORDER BY langcode, delta
                """, (nid,))
                sections = cursor.fetchall()
                
                print("文章段落关联 (node__field_sections):")
                for sec in sections:
                    print(f"  文章: {sec['entity_id']}, 段落ID: {sec['field_sections_target_id']}, 位置: {sec['delta']}, 语言: {sec['langcode']}")
                print()
                
    finally:
        conn.close()

if __name__ == "__main__":
    # 打印数据库表结构
    schema = get_db_schema(db="fyp")
    for table, columns in schema.items():
        print(f"表: {table}")
        for col_name, col_type in columns:
            print(f"  - {col_name}: {col_type}")
        print()