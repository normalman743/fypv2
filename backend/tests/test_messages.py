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
    chat = Chat(
        title="测试聊天",
        chat_type="general",
        course_id=None,
        user_id=1,
        custom_prompt=None
    )
    db.add(chat)
    
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
        content="二叉树是一种树形数据结构...",
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
        assert "rag_sources" in message

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
                              "file_ids": []
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
                              "file_ids": []
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

    def test_edit_ai_message_forbidden(self):
        """测试不能编辑AI消息"""
        token = get_user_token()
        resp = client.put("/api/v1/messages/2",  # AI消息
                         headers={"Authorization": f"Bearer {token}"},
                         json={
                             "content": "新的消息内容"
                         })
        assert resp.status_code == 400
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_MESSAGE_TYPE"

    def test_delete_message_success(self):
        """测试删除消息"""
        # 先发送一条新消息
        token = get_user_token()
        send_resp = client.post("/api/v1/chats/1/messages",
                               headers={"Authorization": f"Bearer {token}"},
                               json={
                                   "content": "要删除的测试消息",
                                   "file_ids": []
                               })
        assert send_resp.status_code == 200
        message_id = send_resp.json()["data"]["user_message"]["id"]
        
        resp = client.delete(f"/api/v1/messages/{message_id}",
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