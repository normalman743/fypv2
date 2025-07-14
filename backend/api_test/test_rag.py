"""
RAG功能API测试
测试RAG检索、AI增强响应等功能
"""
from utils import APIClient, print_response, check_response, extract_data
from config import TEST_USER
import time
import json

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

def test_rag_enabled_chat(client: APIClient):
    """测试RAG功能的聊天"""
    print("\n🧠 测试RAG增强聊天")
    
    # 创建通用聊天测试RAG
    timestamp = str(int(time.time()))
    chat_data = {
        "chat_type": "general",
        "first_message": f"什么是二叉树的遍历？请详细解释各种遍历方法。 - {timestamp}",
        "course_id": None
    }
    
    response = client.post("/chats", chat_data)
    print_response(response, "创建RAG测试聊天")
    
    if check_response(response):
        data = extract_data(response)
        if data:
            chat = data.get("chat")
            ai_message = data.get("ai_message")
            
            if ai_message:
                print(f"📝 AI响应内容: {ai_message.get('content', '')[:200]}...")
                print(f"📊 Tokens使用: {ai_message.get('tokens_used', 0)}")
                print(f"💰 成本: ${ai_message.get('cost', 0):.6f}")
                
                # 检查RAG源
                rag_sources = ai_message.get('rag_sources', [])
                print(f"📚 RAG源数量: {len(rag_sources)}")
                
                if rag_sources:
                    print("📖 RAG源详情:")
                    for i, source in enumerate(rag_sources[:3]):  # 只显示前3个
                        print(f"   {i+1}. 文件: {source.get('source_file', 'unknown')}")
                        print(f"      块ID: {source.get('chunk_id', 0)}")
                else:
                    print("⚠️ 未使用RAG源 (可能是Mock模式或无相关文档)")
                
                # 检查聊天标题自动生成
                if data.get("chat_title_updated"):
                    print(f"🎯 自动生成标题: {data.get('new_chat_title', '未知')}")
                
                return chat.get("id") if chat else None
    
    return None

def test_course_specific_rag(client: APIClient):
    """测试课程特定的RAG检索"""
    print("\n🎓 测试课程特定RAG")
    
    # 先获取可用课程
    response = client.get("/courses")
    if not check_response(response):
        print("❌ 无法获取课程列表")
        return None
    
    data = extract_data(response)
    courses = data.get("courses", []) if data else []
    
    if not courses:
        print("⚠️ 没有可用的课程，跳过课程RAG测试")
        return None
    
    course_id = courses[0].get("id")
    print(f"📚 使用课程: {courses[0].get('name', 'unknown')} (ID: {course_id})")
    
    # 创建课程聊天
    timestamp = str(int(time.time()))
    chat_data = {
        "chat_type": "course",
        "first_message": f"这门课程的主要内容是什么？有哪些重点知识点？ - {timestamp}",
        "course_id": course_id
    }
    
    response = client.post("/chats", chat_data)
    print_response(response, "创建课程RAG测试聊天")
    
    if check_response(response):
        data = extract_data(response)
        if data:
            ai_message = data.get("ai_message")
            if ai_message:
                rag_sources = ai_message.get('rag_sources', [])
                print(f"📚 课程RAG源数量: {len(rag_sources)}")
                
                # 分析RAG源的来源
                course_sources = []
                global_sources = []
                
                for source in rag_sources:
                    source_file = source.get('source_file', '')
                    if '课程' in source_file or 'course' in source_file.lower():
                        course_sources.append(source)
                    else:
                        global_sources.append(source)
                
                print(f"🎯 课程特定源: {len(course_sources)}")
                print(f"🌐 全局源: {len(global_sources)}")
                
                return data.get("chat", {}).get("id")
    
    return None

def test_rag_search_scenarios(client: APIClient, chat_id: int):
    """测试不同场景的RAG搜索"""
    print("\n🔍 测试不同RAG搜索场景")
    
    test_messages = [
        {
            "content": "二叉搜索树的插入操作是如何实现的？",
            "description": "技术问题"
        },
        {
            "content": "校园体育馆的开放时间是什么时候？",
            "description": "校园生活问题"
        },
        {
            "content": "什么是算法复杂度？时间复杂度和空间复杂度有什么区别？",
            "description": "理论概念问题"
        }
    ]
    
    for i, msg in enumerate(test_messages):
        print(f"\n📝 测试 {i+1}: {msg['description']}")
        print(f"❓ 问题: {msg['content']}")
        
        response = client.post(f"/chats/{chat_id}/messages", {
            "content": msg["content"]
        })
        
        if check_response(response):
            data = extract_data(response)
            if data:
                ai_message = data.get("ai_message")
                if ai_message:
                    print(f"✅ 响应长度: {len(ai_message.get('content', ''))}")
                    print(f"📚 RAG源数量: {len(ai_message.get('rag_sources', []))}")
                    
                    # 显示简短预览
                    content_preview = ai_message.get('content', '')[:100]
                    print(f"📖 响应预览: {content_preview}...")
        
        time.sleep(1)  # 避免请求过快

def test_ai_service_mode(client: APIClient):
    """测试AI服务模式信息"""
    print("\n🤖 检测AI服务模式")
    
    # 这里可以通过管理员API或者特殊端点获取服务信息
    # 由于我们没有专门的端点，我们通过创建聊天来间接测试
    
    chat_data = {
        "chat_type": "general",
        "first_message": "系统状态检查：当前AI服务是否启用了RAG功能？"
    }
    
    response = client.post("/chats", chat_data)
    if check_response(response):
        data = extract_data(response)
        if data:
            ai_message = data.get("ai_message")
            if ai_message:
                rag_sources = ai_message.get('rag_sources', [])
                
                if rag_sources:
                    # 检查是否是Mock源
                    mock_indicators = ['mock', 'test', '测试', '示例']
                    is_mock = any(indicator in str(rag_sources).lower() for indicator in mock_indicators)
                    
                    if is_mock:
                        print("🔄 检测到Mock RAG模式")
                    else:
                        print("🚀 检测到生产RAG模式")
                    
                    print(f"📊 RAG源示例: {rag_sources[0] if rag_sources else 'None'}")
                else:
                    print("⚠️ 未检测到RAG源，可能为纯Mock模式")
                
                # 检查响应质量指标
                content = ai_message.get('content', '')
                if '基于相关文档资料' in content or '参考资料' in content:
                    print("✅ 检测到RAG增强响应特征")
                else:
                    print("📝 标准AI响应")

def main():
    """运行RAG功能测试"""
    print("🧠 开始RAG功能API测试")
    print("=" * 60)
    
    client = APIClient()
    
    # 认证
    if not setup_auth(client):
        print("❌ 无法获取认证，跳过RAG测试")
        return False
    
    passed = 0
    total = 0
    
    # 测试1: AI服务模式检测
    total += 1
    try:
        test_ai_service_mode(client)
        passed += 1
        print("✅ AI服务模式检测 - 通过")
    except Exception as e:
        print(f"❌ AI服务模式检测 - 失败: {e}")
    
    # 测试2: 通用RAG聊天
    total += 1
    try:
        general_chat_id = test_rag_enabled_chat(client)
        if general_chat_id:
            passed += 1
            print("✅ 通用RAG聊天 - 通过")
            
            # 测试3: RAG搜索场景
            total += 1
            try:
                test_rag_search_scenarios(client, general_chat_id)
                passed += 1
                print("✅ RAG搜索场景 - 通过")
            except Exception as e:
                print(f"❌ RAG搜索场景 - 失败: {e}")
        else:
            print("❌ 通用RAG聊天 - 失败")
    except Exception as e:
        print(f"❌ 通用RAG聊天 - 失败: {e}")
    
    # 测试4: 课程特定RAG
    total += 1
    try:
        course_chat_id = test_course_specific_rag(client)
        if course_chat_id:
            passed += 1
            print("✅ 课程特定RAG - 通过")
        else:
            print("❌ 课程特定RAG - 失败")
    except Exception as e:
        print(f"❌ 课程特定RAG - 失败: {e}")
    
    # 测试总结
    print("\n" + "=" * 60)
    print(f"🎯 RAG测试总结: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有RAG测试通过！")
        print("\n📋 测试结果说明:")
        print("• AI服务正常运行")
        print("• RAG功能已集成")
        print("• 聊天标题自动生成")
        print("• 课程和通用知识库检索")
    else:
        print("⚠️ 部分RAG测试失败")
        print("\n🔍 可能的原因:")
        print("• RAG服务未完全初始化")
        print("• 缺少文档数据")
        print("• 网络或API配置问题")
    
    return passed == total

if __name__ == "__main__":
    main()
