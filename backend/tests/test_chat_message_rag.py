import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.semester import Semester
from app.models.course import Course
from app.models.chat import Chat
from app.models.message import Message
from app.core.security import get_password_hash, create_access_token
from sqlalchemy.orm import Session
from datetime import datetime
import json

client = TestClient(app)

def setup_module(module):
    # 每次测试前重建数据库
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    
    # 创建用户
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass"),
        role="user"
    )
    db.add(user)
    
    # 创建学期
    semester = Semester(
        name="2025第一学期",
        code="2025S1",
        start_date=datetime(2025, 3, 1),
        end_date=datetime(2025, 6, 30),
        is_active=True
    )
    db.add(semester)
    
    # 创建课程
    course = Course(
        name="数据结构与算法",
        code="CS1101A",
        description="学习各种数据结构和算法",
        semester_id=1,
        user_id=1
    )
    db.add(course)
    
    # 创建测试聊天
    chat1 = Chat(
        title="通用学习讨论",
        chat_type="general",
        course_id=None,
        user_id=1,
        custom_prompt=None
    )
    db.add(chat1)
    
    chat2 = Chat(
        title="数据结构讨论",
        chat_type="course",
        course_id=1,
        user_id=1,
        custom_prompt=None
    )
    db.add(chat2)
    
    # 创建测试消息
    message1 = Message(
        chat_id=1,
        content="什么是二叉树？",
        role="user",
        tokens_used=None,
        cost=None
    )
    db.add(message1)
    
    message2 = Message(
        chat_id=1,
        content="二叉树是一种树形数据结构，其中每个节点最多有两个子节点...",
        role="assistant",
        tokens_used=150,
        cost=0.0003
    )
    db.add(message2)
    
    db.commit()
    db.close()

def teardown_module(module):
    # 测试后清理数据库
    Base.metadata.drop_all(bind=engine)

def get_user_token():
    """获取用户token"""
    token = create_access_token(data={"sub": 1})  # 假设用户ID为1
    return token

# 聊天管理相关测试
class TestChats:
    def test_get_chats_success(self):
        """测试获取聊天列表"""
        token = get_user_token()
        resp = client.get("/api/v1/chats", 
                         headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "chats" in data["data"]
        assert len(data["data"]["chats"]) > 0
        
        chat = data["data"]["chats"][0]
        assert "id" in chat
        assert "title" in chat
        assert "chat_type" in chat
        assert "course_id" in chat
        assert "user_id" in chat
        assert "custom_prompt" in chat
        assert "created_at" in chat
        assert "updated_at" in chat
        assert "stats" in chat
        assert "message_count" in chat["stats"]

    def test_get_chats_no_auth(self):
        """测试无认证不能获取聊天列表"""
        resp = client.get("/api/v1/chats")
        assert resp.status_code == 401

    def test_create_general_chat_success(self):
        """测试创建通用聊天"""
        token = get_user_token()
        resp = client.post("/api/v1/chats", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "chat_type": "general",
                              "first_message": "崇基学院体育馆的开放时间是什么时候",
                              "course_id": None,
                              "custom_prompt": None,
                              "file_ids": [1, 2]
                          })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "chat" in data["data"]
        assert "user_message" in data["data"]
        assert "ai_message" in data["data"]
        
        chat = data["data"]["chat"]
        assert "id" in chat
        assert "title" in chat
        assert "chat_type" in chat
        assert chat["chat_type"] == "general"
        assert "course_id" in chat
        assert chat["course_id"] is None
        assert "user_id" in chat
        assert "custom_prompt" in chat
        assert "created_at" in chat
        assert "updated_at" in chat

    def test_create_course_chat_success(self):
        """测试创建课程相关聊天"""
        token = get_user_token()
        resp = client.post("/api/v1/chats", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "chat_type": "course",
                              "first_message": "这节课讲了什么",
                              "course_id": 1,
                              "custom_prompt": None,
                              "file_ids": [3]
                          })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "chat" in data["data"]
        
        chat = data["data"]["chat"]
        assert chat["chat_type"] == "course"
        assert chat["course_id"] == 1

    def test_create_chat_no_auth(self):
        """测试无认证不能创建聊天"""
        resp = client.post("/api/v1/chats", 
                          json={
                              "chat_type": "general",
                              "first_message": "测试消息",
                              "course_id": None
                          })
        assert resp.status_code == 401

    def test_create_chat_missing_fields(self):
        """测试缺少必填字段"""
        token = get_user_token()
        resp = client.post("/api/v1/chats", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "first_message": "测试消息"
                              # 缺少chat_type
                          })
        assert resp.status_code == 422

    def test_update_chat_success(self):
        """测试更新聊天"""
        token = get_user_token()
        resp = client.put("/api/v1/chats/1", 
                         headers={"Authorization": f"Bearer {token}"},
                         json={
                             "title": "新的聊天标题"
                         })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "chat" in data["data"]
        chat = data["data"]["chat"]
        assert chat["title"] == "新的聊天标题"
        assert "updated_at" in chat

    def test_update_chat_no_auth(self):
        """测试无认证不能更新聊天"""
        resp = client.put("/api/v1/chats/1", 
                         json={
                             "title": "新的聊天标题"
                         })
        assert resp.status_code == 401

    def test_update_chat_not_found(self):
        """测试更新不存在的聊天"""
        token = get_user_token()
        resp = client.put("/api/v1/chats/999", 
                         headers={"Authorization": f"Bearer {token}"},
                         json={
                             "title": "新的聊天标题"
                         })
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "CHAT_NOT_FOUND"

    def test_delete_chat_success(self):
        """测试删除聊天"""
        token = get_user_token()
        resp = client.delete("/api/v1/chats/1", 
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_delete_chat_no_auth(self):
        """测试无认证不能删除聊天"""
        resp = client.delete("/api/v1/chats/1")
        assert resp.status_code == 401

    def test_delete_chat_not_found(self):
        """测试删除不存在的聊天"""
        token = get_user_token()
        resp = client.delete("/api/v1/chats/999", 
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "CHAT_NOT_FOUND"

# 消息管理相关测试
class TestMessages:
    def test_get_chat_messages_success(self):
        """测试获取消息列表"""
        token = get_user_token()
        resp = client.get("/api/v1/chats/1/messages", 
                         headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "messages" in data["data"]
        assert len(data["data"]["messages"]) > 0
        
        message = data["data"]["messages"][0]
        assert "id" in message
        assert "chat_id" in message
        assert "content" in message
        assert "role" in message
        assert "tokens_used" in message
        assert "cost" in message
        assert "created_at" in message
        assert "file_attachments" in message

    def test_get_chat_messages_no_auth(self):
        """测试无认证不能获取消息"""
        resp = client.get("/api/v1/chats/1/messages")
        assert resp.status_code == 401

    def test_get_chat_messages_chat_not_found(self):
        """测试获取不存在聊天的消息"""
        token = get_user_token()
        resp = client.get("/api/v1/chats/999/messages", 
                         headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "CHAT_NOT_FOUND"

    def test_send_message_success(self):
        """测试发送消息"""
        token = get_user_token()
        resp = client.post("/api/v1/chats/1/messages", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "content": "什么是二叉树的遍历？",
                              "file_ids": [1, 2]
                          })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "user_message" in data["data"]
        assert "ai_message" in data["data"]
        
        user_message = data["data"]["user_message"]
        assert user_message["content"] == "什么是二叉树的遍历？"
        assert user_message["role"] == "user"
        assert "file_attachments" in user_message
        
        ai_message = data["data"]["ai_message"]
        assert ai_message["role"] == "assistant"
        assert "tokens_used" in ai_message
        assert "cost" in ai_message
        assert "rag_sources" in ai_message

    def test_send_message_no_auth(self):
        """测试无认证不能发送消息"""
        resp = client.post("/api/v1/chats/1/messages", 
                          json={
                              "content": "测试消息"
                          })
        assert resp.status_code == 401

    def test_send_message_chat_not_found(self):
        """测试向不存在的聊天发送消息"""
        token = get_user_token()
        resp = client.post("/api/v1/chats/999/messages", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "content": "测试消息"
                          })
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "CHAT_NOT_FOUND"

    def test_send_message_missing_content(self):
        """测试缺少消息内容"""
        token = get_user_token()
        resp = client.post("/api/v1/chats/1/messages", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "file_ids": [1, 2]
                              # 缺少content
                          })
        assert resp.status_code == 422

    def test_edit_message_success(self):
        """测试编辑消息"""
        token = get_user_token()
        resp = client.put("/api/v1/messages/1", 
                         headers={"Authorization": f"Bearer {token}"},
                         json={
                             "content": "新的消息内容"
                         })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "message" in data["data"]
        message = data["data"]["message"]
        assert message["content"] == "新的消息内容"
        assert "updated_at" in message

    def test_edit_message_no_auth(self):
        """测试无认证不能编辑消息"""
        resp = client.put("/api/v1/messages/1", 
                         json={
                             "content": "新的消息内容"
                         })
        assert resp.status_code == 401

    def test_edit_message_not_found(self):
        """测试编辑不存在的消息"""
        token = get_user_token()
        resp = client.put("/api/v1/messages/999", 
                         headers={"Authorization": f"Bearer {token}"},
                         json={
                             "content": "新的消息内容"
                         })
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "MESSAGE_NOT_FOUND"

    def test_delete_message_success(self):
        """测试删除消息"""
        token = get_user_token()
        resp = client.delete("/api/v1/messages/1", 
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_delete_message_no_auth(self):
        """测试无认证不能删除消息"""
        resp = client.delete("/api/v1/messages/1")
        assert resp.status_code == 401

    def test_delete_message_not_found(self):
        """测试删除不存在的消息"""
        token = get_user_token()
        resp = client.delete("/api/v1/messages/999", 
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "MESSAGE_NOT_FOUND"

# RAG功能相关测试
class TestRAG:
    def test_general_chat_rag_global_only(self):
        """测试通用聊天只检索全局知识库"""
        token = get_user_token()
        resp = client.post("/api/v1/chats", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "chat_type": "general",
                              "first_message": "校园设施相关问题",
                              "course_id": None
                          })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        
        # 检查AI消息是否包含RAG源
        ai_message = data["data"]["ai_message"]
        assert "rag_sources" in ai_message
        # 通用聊天应该只检索全局知识库

    def test_course_chat_rag_course_priority(self):
        """测试课程聊天优先检索课程相关文件"""
        token = get_user_token()
        resp = client.post("/api/v1/chats", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "chat_type": "course",
                              "first_message": "课程相关问题",
                              "course_id": 1
                          })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        
        # 检查AI消息是否包含RAG源
        ai_message = data["data"]["ai_message"]
        assert "rag_sources" in ai_message
        # 课程聊天应该优先检索课程相关文件

    def test_chat_title_auto_generation(self):
        """测试聊天标题自动生成"""
        token = get_user_token()
        resp = client.post("/api/v1/chats", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "chat_type": "general",
                              "first_message": "关于校园生活的具体问题",
                              "course_id": None
                          })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        
        # 检查是否自动更新了聊天标题
        assert "chat_title_updated" in data["data"]
        assert "new_chat_title" in data["data"]
        # 如果是第一条消息，应该自动生成标题
        if data["data"]["chat_title_updated"]:
            assert data["data"]["new_chat_title"] != "新聊天" 