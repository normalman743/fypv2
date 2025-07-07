"""
聊天API测试
测试创建聊天、发送消息、获取消息等功能
"""
from utils import APIClient, print_response, check_response, extract_data
from config import TEST_USER, ADMIN_USER
import time

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

def test_get_chats(client: APIClient):
    """测试获取聊天列表"""
    response = client.get("/chats")
    print_response(response, "获取聊天列表")
    
    if check_response(response):
        data = extract_data(response)
        return data.get("chats", []) if data else []
    return []

def test_create_general_chat(client: APIClient):
    """测试创建通用聊天"""
    timestamp = str(int(time.time()))
    chat_data = {
        "chat_type": "general",
        "first_message": f"你好，这是一条测试消息 - {timestamp}",
        "custom_prompt": "你是一个友好的AI助手"
    }
    
    response = client.post("/chats", chat_data)
    print_response(response, "创建通用聊天")
    
    if check_response(response):
        data = extract_data(response)
        return data.get("chat") if data else None
    return None

def test_create_course_chat(client: APIClient, course_id: int):
    """测试创建课程聊天"""
    timestamp = str(int(time.time()))
    chat_data = {
        "chat_type": "course",
        "first_message": f"请帮我解答关于这门课程的问题 - {timestamp}",
        "course_id": course_id,
        "custom_prompt": "你是这门课程的专业助教"
    }
    
    response = client.post("/chats", chat_data)
    print_response(response, "创建课程聊天")
    
    if check_response(response):
        data = extract_data(response)
        return data.get("chat") if data else None
    return None

def test_get_chat_messages(client: APIClient, chat_id: int):
    """测试获取聊天消息"""
    response = client.get(f"/chats/{chat_id}/messages")
    print_response(response, "获取聊天消息")
    
    if check_response(response):
        data = extract_data(response)
        return data.get("messages", []) if data else []
    return None

def test_send_message(client: APIClient, chat_id: int):
    """测试发送消息"""
    timestamp = str(int(time.time()))
    message_data = {
        "content": f"这是一条新的测试消息 - {timestamp}",
        "file_ids": []
    }
    
    response = client.post(f"/chats/{chat_id}/messages", message_data)
    print_response(response, "发送消息")
    
    if check_response(response):
        data = extract_data(response)
        # 返回用户消息用于后续测试（如编辑消息）
        return data.get("user_message") if data else None
    return None

def test_send_message_with_files(client: APIClient, chat_id: int, file_ids: list):
    """测试发送带文件的消息"""
    timestamp = str(int(time.time()))
    message_data = {
        "content": f"这是一条包含文件的测试消息 - {timestamp}",
        "file_ids": file_ids
    }
    
    response = client.post(f"/chats/{chat_id}/messages", message_data)
    print_response(response, "发送带文件的消息")
    
    if check_response(response):
        data = extract_data(response)
        # 返回用户消息用于后续测试
        return data.get("user_message") if data else None
    return None

def test_update_chat(client: APIClient, chat_id: int):
    """测试更新聊天标题"""
    timestamp = str(int(time.time()))
    update_data = {
        "title": f"更新后的聊天标题 - {timestamp}"
    }
    
    response = client.put(f"/chats/{chat_id}", update_data)
    print_response(response, "更新聊天标题")
    return check_response(response)

def test_edit_message(client: APIClient, message_id: int):
    """测试编辑消息"""
    timestamp = str(int(time.time()))
    edit_data = {
        "content": f"这是编辑后的消息内容 - {timestamp}"
    }
    
    response = client.put(f"/messages/{message_id}", edit_data)
    print_response(response, "编辑消息")
    return check_response(response)

def test_delete_message(client: APIClient, message_id: int):
    """测试删除消息"""
    response = client.delete(f"/messages/{message_id}")
    print_response(response, "删除消息")
    return check_response(response)

def test_delete_chat(client: APIClient, chat_id: int):
    """测试删除聊天"""
    response = client.delete(f"/chats/{chat_id}")
    print_response(response, "删除聊天")
    return check_response(response)

def get_test_course_id(client: APIClient):
    """获取测试课程ID"""
    response = client.get("/courses")
    if check_response(response):
        data = extract_data(response)
        courses = data.get("courses", []) if data else []
        if courses:
            return courses[0].get("id")
    return None

def main():
    """运行聊天测试"""
    print("💬 开始聊天API测试")
    
    client = APIClient()
    
    # 认证
    if not setup_auth(client):
        print("❌ 无法获取认证，跳过聊天测试")
        return False
    
    passed = 0
    total = 0
    
    # 测试获取聊天列表
    total += 1
    initial_chats = test_get_chats(client)
    if initial_chats is not None:
        passed += 1
        print("✅ 获取聊天列表 - 通过")
        print(f"💭 当前有 {len(initial_chats)} 个聊天")
    else:
        print("❌ 获取聊天列表 - 失败")
    
    # 测试创建通用聊天
    print("\n--- 测试通用聊天功能 ---")
    total += 1
    general_chat = test_create_general_chat(client)
    if general_chat:
        passed += 1
        print("✅ 创建通用聊天 - 通过")
        
        chat_id = general_chat.get("id")
        if chat_id:
            # 测试获取聊天消息
            total += 1
            messages = test_get_chat_messages(client, chat_id)
            if messages is not None:
                passed += 1
                print("✅ 获取聊天消息 - 通过")
                print(f"📝 聊天中有 {len(messages)} 条消息")
            else:
                print("❌ 获取聊天消息 - 失败")
            
            # 测试发送消息
            total += 1
            new_message = test_send_message(client, chat_id)
            if new_message:
                passed += 1
                print("✅ 发送消息 - 通过")
                
                message_id = new_message.get("id")
                if message_id:
                    # 测试编辑消息
                    total += 1
                    if test_edit_message(client, message_id):
                        passed += 1
                        print("✅ 编辑消息 - 通过")
                    else:
                        print("❌ 编辑消息 - 失败")
            else:
                print("❌ 发送消息 - 失败")
            
            # 测试更新聊天标题
            total += 1
            if test_update_chat(client, chat_id):
                passed += 1
                print("✅ 更新聊天标题 - 通过")
            else:
                print("❌ 更新聊天标题 - 失败")
    else:
        print("❌ 创建通用聊天 - 失败")
    
    # 测试课程聊天功能
    print("\n--- 测试课程聊天功能 ---")
    course_id = get_test_course_id(client)
    if course_id:
        total += 1
        course_chat = test_create_course_chat(client, course_id)
        if course_chat:
            passed += 1
            print("✅ 创建课程聊天 - 通过")
            
            course_chat_id = course_chat.get("id")
            if course_chat_id:
                # 测试在课程聊天中发送消息
                total += 1
                course_message = test_send_message(client, course_chat_id)
                if course_message:
                    passed += 1
                    print("✅ 课程聊天发送消息 - 通过")
                else:
                    print("❌ 课程聊天发送消息 - 失败")
        else:
            print("❌ 创建课程聊天 - 失败")
    else:
        print("⚠️ 没有找到课程，跳过课程聊天测试")
    
    # 清理测试数据（删除创建的聊天）
    print("\n--- 清理测试数据 ---")
    if general_chat and general_chat.get("id"):
        total += 1
        if test_delete_chat(client, general_chat["id"]):
            passed += 1
            print("✅ 删除通用聊天 - 通过")
        else:
            print("❌ 删除通用聊天 - 失败")
    
    print(f"\n📊 聊天API测试结果: {passed}/{total} 通过")
    return passed == total if total > 0 else False

if __name__ == "__main__":
    main()