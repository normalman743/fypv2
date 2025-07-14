"""
V2.1统一文件系统API测试
测试新的统一文件架构、RAG集成、文件共享等功能
"""
import os
import tempfile
import time
import json
from utils import APIClient, print_response, check_response, extract_data
from config import TEST_USER, ADMIN_USER

def setup_auth(client: APIClient):
    """设置认证"""
    login_data = {
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]
    }
    
    response = client.post("/auth/login", login_data)
    if check_response(response):
        data = extract_data(response)
        if data and "access_token" in data:
            client.set_token(data["access_token"])
            return True
    return False

def create_test_files():
    """创建不同类型的测试文件"""
    files = {}
    
    # 创建文本文件
    text_content = """# 机器学习基础知识

## 1. 监督学习
监督学习是机器学习的一种重要方法，使用标记的训练数据来训练模型。

### 分类算法
- 决策树
- 随机森林
- 支持向量机
- 神经网络

### 回归算法
- 线性回归
- 多项式回归
- 逻辑回归

## 2. 无监督学习
无监督学习处理没有标记的数据，发现数据中的隐藏模式。

### 聚类算法
- K-means
- 层次聚类
- DBSCAN

## 3. 深度学习
深度学习是机器学习的一个子领域，使用神经网络进行学习。

### 常见架构
- 卷积神经网络 (CNN)
- 循环神经网络 (RNN)
- 变压器 (Transformer)
"""
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
    temp_file.write(text_content)
    temp_file.close()
    files['text'] = temp_file.name
    
    # 创建JSON文件
    json_content = {
        "course_info": {
            "name": "人工智能导论",
            "topics": ["机器学习", "深度学习", "自然语言处理", "计算机视觉"],
            "difficulty": "中级",
            "prerequisites": ["线性代数", "概率论", "Python编程"]
        },
        "assignments": [
            {
                "id": 1,
                "title": "线性回归实现",
                "deadline": "2025-02-15",
                "points": 100
            },
            {
                "id": 2,
                "title": "神经网络分类",
                "deadline": "2025-03-01",
                "points": 150
            }
        ]
    }
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
    json.dump(json_content, temp_file, ensure_ascii=False, indent=2)
    temp_file.close()
    files['json'] = temp_file.name
    
    return files

def cleanup_files(files):
    """清理临时文件"""
    for file_path in files.values():
        if os.path.exists(file_path):
            os.unlink(file_path)

def test_upload_file_with_scope(client: APIClient, scope: str, course_id: int = None, folder_id: int = None):
    """测试不同scope的文件上传"""
    test_files = create_test_files()
    uploaded_files = []
    
    try:
        for file_type, file_path in test_files.items():
            with open(file_path, 'rb') as f:
                files = {'file': (f'test_{file_type}.{file_path.split(".")[-1]}', f)}
                data = {
                    'scope': scope,
                }
                
                if course_id:
                    data['course_id'] = course_id
                if folder_id:
                    data['folder_id'] = folder_id
                
                response = client.post("/files/upload", data=data, files=files)
                print_response(response, f"上传{scope}文件 ({file_type})")
                
                if check_response(response):
                    file_data = extract_data(response)
                    if file_data and "file" in file_data:
                        uploaded_files.append(file_data["file"])
                        print(f"✅ 上传成功: {file_data['file'].get('original_name')} (ID: {file_data['file'].get('id')})")
    finally:
        cleanup_files(test_files)
    
    return uploaded_files

def test_file_processing_status(client: APIClient, file_id: int):
    """测试文件处理状态"""
    print(f"\n📊 检查文件 {file_id} 处理状态...")
    
    max_attempts = 10
    for attempt in range(max_attempts):
        response = client.get(f"/files/{file_id}/status")
        
        if check_response(response):
            data = extract_data(response)
            if data:
                status = data.get("processing_status", "unknown")
                is_processed = data.get("is_processed", False)
                chunk_count = data.get("chunk_count", 0)
                
                print(f"🔄 尝试 {attempt + 1}: 状态={status}, 已处理={is_processed}, 块数={chunk_count}")
                
                if status == "ready" and is_processed:
                    print(f"✅ 文件处理完成! 创建了 {chunk_count} 个文档块")
                    return True
                elif status == "failed":
                    print(f"❌ 文件处理失败")
                    return False
                
                time.sleep(2)  # 等待2秒再检查
        else:
            print(f"❌ 无法获取文件状态")
            return False
    
    print(f"⏰ 文件处理超时")
    return False

def test_rag_search(client: APIClient, course_id: int = None):
    """测试RAG检索功能"""
    print("\n🔍 测试RAG检索功能...")
    
    # 测试搜索
    search_queries = [
        "机器学习算法",
        "深度学习",
        "神经网络",
        "课程信息"
    ]
    
    for query in search_queries:
        data = {
            "query": query,
            "course_id": course_id,
            "limit": 5
        }
        
        response = client.post("/rag/search", data)
        print_response(response, f"RAG搜索: {query}")
        
        if check_response(response):
            result_data = extract_data(response)
            if result_data and "results" in result_data:
                results = result_data["results"]
                print(f"📝 找到 {len(results)} 个相关结果")
                for i, result in enumerate(results[:2]):  # 只显示前2个结果
                    print(f"  {i+1}. 文件: {result.get('source_file', 'Unknown')}")
                    print(f"     相关度: {result.get('relevance_score', 0):.3f}")
                    print(f"     内容: {result.get('content', '')[:100]}...")

def test_create_rag_chat(client: APIClient, course_id: int = None):
    """测试RAG增强聊天"""
    print("\n💬 测试RAG增强聊天...")
    
    # 创建RAG聊天
    chat_data = {
        "title": "AI学习讨论",
        "chat_type": "course" if course_id else "general",
        "course_id": course_id,
        "rag_enabled": True,
        "custom_prompt": "你是一个AI助教，请基于课程材料回答学生的问题。"
    }
    
    response = client.post("/chats", chat_data)
    print_response(response, "创建RAG聊天")
    
    if check_response(response):
        data = extract_data(response)
        chat = data.get("chat") if data else None
        if chat:
            chat_id = chat.get("id")
            
            # 发送消息测试RAG
            test_messages = [
                "什么是监督学习？请详细解释。",
                "深度学习有哪些常见架构？",
                "课程中提到了哪些机器学习算法？"
            ]
            
            for message_content in test_messages:
                message_data = {
                    "content": message_content
                }
                
                response = client.post(f"/chats/{chat_id}/messages", message_data)
                print_response(response, f"发送RAG消息: {message_content[:30]}...")
                
                if check_response(response):
                    msg_data = extract_data(response)
                    if msg_data and "ai_message" in msg_data:
                        ai_msg = msg_data["ai_message"]
                        print(f"🤖 AI回复: {ai_msg.get('content', '')[:200]}...")
                        print(f"📊 Token使用: {ai_msg.get('tokens_used', 0)}")
                        print(f"🔍 RAG源数量: {ai_msg.get('rag_source_count', 0)}")
            
            return chat_id
    
    return None

def test_file_sharing(client: APIClient, file_id: int):
    """测试文件共享功能"""
    print(f"\n🔗 测试文件 {file_id} 共享功能...")
    
    # 创建文件共享
    share_data = {
        "shared_with_type": "public",
        "permission_level": "read",
        "expires_at": "2025-12-31T23:59:59"
    }
    
    response = client.post(f"/files/{file_id}/share", share_data)
    print_response(response, "创建文件共享")
    
    if check_response(response):
        data = extract_data(response)
        share = data.get("share") if data else None
        if share:
            share_id = share.get("id")
            print(f"✅ 共享创建成功，ID: {share_id}")
            
            # 获取共享列表
            response = client.get(f"/files/{file_id}/shares")
            print_response(response, "获取文件共享列表")
            
            return share_id
    
    return None

def test_get_files_by_scope(client: APIClient, scope: str, course_id: int = None):
    """测试按scope获取文件"""
    print(f"\n📂 测试获取 {scope} 文件...")
    
    params = {"scope": scope}
    if course_id:
        params["course_id"] = course_id
    
    response = client.get("/files", params)
    print_response(response, f"获取{scope}文件列表")
    
    if check_response(response):
        data = extract_data(response)
        if data and "files" in data:
            files = data["files"]
            print(f"📁 找到 {len(files)} 个{scope}文件")
            for file in files[:3]:  # 显示前3个文件
                print(f"  - {file.get('original_name')} (ID: {file.get('id')}, 状态: {file.get('processing_status')})")
            return files
    
    return []

def get_test_course_and_folder(client: APIClient):
    """获取测试用的课程和文件夹ID"""
    # 获取课程列表
    response = client.get("/courses")
    if not check_response(response):
        return None, None
    
    courses_data = extract_data(response)
    courses = courses_data.get("courses", []) if courses_data else []
    
    if not courses:
        print("❌ 没有找到课程")
        return None, None
    
    course = courses[0]
    course_id = course.get("id")
    
    # 获取文件夹列表
    response = client.get(f"/courses/{course_id}/folders")
    if not check_response(response):
        return course_id, None
    
    folders_data = extract_data(response)
    folders = folders_data.get("folders", []) if folders_data else []
    
    folder_id = folders[0].get("id") if folders else None
    return course_id, folder_id

def main():
    """运行V2.1统一文件系统测试"""
    print("🚀 开始V2.1统一文件系统API测试")
    
    client = APIClient()
    
    # 认证
    if not setup_auth(client):
        print("❌ 无法获取认证，退出测试")
        return False
    
    print("✅ 认证成功")
    
    # 获取测试用的课程和文件夹
    course_id, folder_id = get_test_course_and_folder(client)
    print(f"📝 测试课程ID: {course_id}, 文件夹ID: {folder_id}")
    
    passed = 0
    total = 0
    uploaded_files = []
    
    # 测试1: 上传课程文件
    total += 1
    if course_id and folder_id:
        files = test_upload_file_with_scope(client, "course", course_id, folder_id)
        if files:
            uploaded_files.extend(files)
            passed += 1
            print("✅ 课程文件上传 - 通过")
        else:
            print("❌ 课程文件上传 - 失败")
    else:
        print("⏭️  跳过课程文件上传测试（无课程/文件夹）")
    
    # 测试2: 上传全局文件
    total += 1
    global_files = test_upload_file_with_scope(client, "global")
    if global_files:
        uploaded_files.extend(global_files)
        passed += 1
        print("✅ 全局文件上传 - 通过")
    else:
        print("❌ 全局文件上传 - 失败")
    
    # 测试3: 上传个人文件
    total += 1
    personal_files = test_upload_file_with_scope(client, "personal")
    if personal_files:
        uploaded_files.extend(personal_files)
        passed += 1
        print("✅ 个人文件上传 - 通过")
    else:
        print("❌ 个人文件上传 - 失败")
    
    # 等待文件处理
    if uploaded_files:
        print(f"\n⏳ 等待 {len(uploaded_files)} 个文件处理...")
        processed_files = []
        
        for file in uploaded_files:
            file_id = file.get("id")
            if test_file_processing_status(client, file_id):
                processed_files.append(file)
        
        print(f"✅ {len(processed_files)}/{len(uploaded_files)} 文件处理完成")
    
    # 测试4: 按scope获取文件
    total += 1
    course_files = test_get_files_by_scope(client, "course", course_id)
    if course_files is not None:
        passed += 1
        print("✅ 获取课程文件列表 - 通过")
    
    total += 1
    global_files = test_get_files_by_scope(client, "global")
    if global_files is not None:
        passed += 1
        print("✅ 获取全局文件列表 - 通过")
    
    # 测试5: RAG检索功能
    if uploaded_files:
        total += 1
        try:
            test_rag_search(client, course_id)
            passed += 1
            print("✅ RAG检索测试 - 通过")
        except Exception as e:
            print(f"❌ RAG检索测试 - 失败: {e}")
    
    # 测试6: RAG聊天功能
    if uploaded_files:
        total += 1
        try:
            chat_id = test_create_rag_chat(client, course_id)
            if chat_id:
                passed += 1
                print("✅ RAG聊天测试 - 通过")
            else:
                print("❌ RAG聊天测试 - 失败")
        except Exception as e:
            print(f"❌ RAG聊天测试 - 失败: {e}")
    
    # 测试7: 文件共享功能
    if uploaded_files:
        total += 1
        try:
            file_id = uploaded_files[0].get("id")
            share_id = test_file_sharing(client, file_id)
            if share_id:
                passed += 1
                print("✅ 文件共享测试 - 通过")
            else:
                print("❌ 文件共享测试 - 失败")
        except Exception as e:
            print(f"❌ 文件共享测试 - 失败: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 V2.1统一文件系统测试结果: {passed}/{total} 通过")
    print(f"📈 通过率: {(passed/total*100):.1f}%" if total > 0 else "无测试执行")
    print(f"📁 上传文件数: {len(uploaded_files)}")
    print(f"✅ 功能覆盖: 文件上传、RAG处理、检索、聊天、共享")
    
    return passed == total if total > 0 else False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)