"""
测试文件夹和文件上下文功能
"""
import pytest
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
headers = {"Content-Type": "application/json"}

# 全局变量存储测试数据
test_data = {
    "user": None,
    "semester": None,
    "course": None,
    "folder": None,
    "files": [],
    "chat": None
}


class TestFolderFileContext:
    """测试文件夹和文件上下文功能"""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """设置测试数据"""
        # 1. 创建用户
        user_data = {
            "username": "test_context_user",
            "email": "test_context@example.com",
            "password": "testpass123"
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/register", json=user_data)
        assert response.status_code == 200
        test_data["user"] = response.json()["data"]
        
        # 获取token
        login_data = {"username": user_data["username"], "password": user_data["password"]}
        response = requests.post(f"{BASE_URL}/api/v1/login", json=login_data)
        assert response.status_code == 200
        token = response.json()["data"]["access_token"]
        global headers
        headers["Authorization"] = f"Bearer {token}"
        
        # 2. 创建学期
        semester_data = {"name": "测试学期", "code": "TEST2025"}
        response = requests.post(f"{BASE_URL}/api/v1/semesters", json=semester_data, headers=headers)
        assert response.status_code == 200
        test_data["semester"] = response.json()["data"]
        
        # 3. 创建课程
        course_data = {
            "name": "数据结构与算法",
            "code": "CS301",
            "description": "测试课程",
            "semester_id": test_data["semester"]["id"]
        }
        response = requests.post(f"{BASE_URL}/api/v1/courses", json=course_data, headers=headers)
        assert response.status_code == 200
        test_data["course"] = response.json()["data"]
        
        # 4. 创建文件夹
        folder_data = {
            "name": "测试文件夹",
            "folder_type": "lecture",
            "course_id": test_data["course"]["id"]
        }
        response = requests.post(f"{BASE_URL}/api/v1/folders", json=folder_data, headers=headers)
        assert response.status_code == 200
        test_data["folder"] = response.json()["data"]
        
        # 5. 上传测试文件到文件夹
        test_files = [
            {"name": "test1.txt", "content": "这是第一个测试文件的内容，包含数据结构的基本概念。"},
            {"name": "test2.txt", "content": "这是第二个测试文件的内容，包含算法复杂度分析。"}
        ]
        
        for file_info in test_files:
            # 创建临时文件
            temp_file_path = f"/tmp/{file_info['name']}"
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                f.write(file_info['content'])
            
            # 上传文件
            with open(temp_file_path, 'rb') as file:
                files = {"file": (file_info['name'], file, 'text/plain')}
                data = {
                    "course_id": test_data["course"]["id"],
                    "folder_id": test_data["folder"]["id"]
                }
                response = requests.post(
                    f"{BASE_URL}/api/v1/files/upload",
                    files=files,
                    data=data,
                    headers={"Authorization": headers["Authorization"]}
                )
                assert response.status_code == 200
                test_data["files"].append(response.json()["data"])
        
        yield
        
        # 清理测试数据
        try:
            # 删除聊天
            if test_data["chat"]:
                requests.delete(f"{BASE_URL}/api/v1/chats/{test_data['chat']['id']}", headers=headers)
            
            # 删除文件
            for file_data in test_data["files"]:
                requests.delete(f"{BASE_URL}/api/v1/files/{file_data['id']}", headers=headers)
            
            # 删除文件夹
            if test_data["folder"]:
                requests.delete(f"{BASE_URL}/api/v1/folders/{test_data['folder']['id']}", headers=headers)
            
            # 删除课程
            if test_data["course"]:
                requests.delete(f"{BASE_URL}/api/v1/courses/{test_data['course']['id']}", headers=headers)
            
            # 删除学期
            if test_data["semester"]:
                requests.delete(f"{BASE_URL}/api/v1/semesters/{test_data['semester']['id']}", headers=headers)
        except Exception as e:
            print(f"清理测试数据时出错: {e}")
    
    def test_create_chat_with_folder_context(self):
        """测试创建聊天时使用文件夹上下文"""
        chat_data = {
            "chat_type": "course",
            "first_message": "请总结这个文件夹中的所有内容",
            "course_id": test_data["course"]["id"],
            "folder_ids": [test_data["folder"]["id"]]
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/chats", json=chat_data, headers=headers)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        assert "chat" in result["data"]
        assert "ai_message" in result["data"]
        
        # 保存聊天数据
        test_data["chat"] = result["data"]["chat"]
        
        # 验证AI响应包含文件夹内容
        ai_content = result["data"]["ai_message"]["content"]
        assert "数据结构" in ai_content or "算法" in ai_content
        
        print(f"✅ 创建聊天时使用文件夹上下文成功")
        print(f"AI响应: {ai_content}")
    
    def test_create_chat_with_mixed_context(self):
        """测试创建聊天时混合使用文件和文件夹上下文"""
        chat_data = {
            "chat_type": "course",
            "first_message": "请基于提供的文件分析数据结构的概念",
            "course_id": test_data["course"]["id"],
            "file_ids": [test_data["files"][0]["id"]],  # 第一个文件
            "folder_ids": [test_data["folder"]["id"]]    # 整个文件夹
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/chats", json=chat_data, headers=headers)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        
        # 验证AI响应
        ai_content = result["data"]["ai_message"]["content"]
        assert len(ai_content) > 0
        
        print(f"✅ 创建聊天时混合使用文件和文件夹上下文成功")
        print(f"AI响应: {ai_content}")
    
    def test_send_message_with_folder_context(self):
        """测试发送消息时使用文件夹上下文"""
        # 先创建一个基本聊天
        chat_data = {
            "chat_type": "course",
            "first_message": "Hello",
            "course_id": test_data["course"]["id"]
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/chats", json=chat_data, headers=headers)
        assert response.status_code == 200
        chat_id = response.json()["data"]["chat"]["id"]
        
        # 发送带文件夹上下文的消息
        message_data = {
            "content": "请分析这个文件夹中的文件内容",
            "folder_ids": [test_data["folder"]["id"]]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/chats/{chat_id}/messages",
            json=message_data,
            headers=headers
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        assert "ai_message" in result["data"]
        
        # 验证AI响应
        ai_content = result["data"]["ai_message"]["content"]
        assert len(ai_content) > 0
        
        print(f"✅ 发送消息时使用文件夹上下文成功")
        print(f"AI响应: {ai_content}")
    
    def test_permission_validation(self):
        """测试权限验证"""
        # 创建另一个用户
        other_user_data = {
            "username": "other_user",
            "email": "other@example.com",
            "password": "testpass123"
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/register", json=other_user_data)
        assert response.status_code == 200
        
        # 获取另一个用户的token
        login_data = {"username": "other_user", "password": "testpass123"}
        response = requests.post(f"{BASE_URL}/api/v1/login", json=login_data)
        assert response.status_code == 200
        other_token = response.json()["data"]["access_token"]
        other_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {other_token}"
        }
        
        # 尝试使用其他用户的文件夹创建聊天
        chat_data = {
            "chat_type": "general",
            "first_message": "测试权限",
            "folder_ids": [test_data["folder"]["id"]]
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/chats", json=chat_data, headers=other_headers)
        assert response.status_code == 403  # 应该被拒绝
        
        print(f"✅ 权限验证测试通过")
    
    def test_empty_folder_handling(self):
        """测试空文件夹处理"""
        # 创建空文件夹
        empty_folder_data = {
            "name": "空文件夹",
            "folder_type": "assignment",
            "course_id": test_data["course"]["id"]
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/folders", json=empty_folder_data, headers=headers)
        assert response.status_code == 200
        empty_folder = response.json()["data"]
        
        # 尝试使用空文件夹创建聊天
        chat_data = {
            "chat_type": "course",
            "first_message": "这个文件夹里有什么内容？",
            "course_id": test_data["course"]["id"],
            "folder_ids": [empty_folder["id"]]
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/chats", json=chat_data, headers=headers)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        
        # 清理空文件夹
        requests.delete(f"{BASE_URL}/api/v1/folders/{empty_folder['id']}", headers=headers)
        
        print(f"✅ 空文件夹处理测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])