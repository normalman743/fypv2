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
    message = Message(
        chat_id=1,
        content="测试消息",
        role="user",
        tokens_used=None,
        cost=None
    )
    db.add(message)
    
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
                              "file_ids": []
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

        # Check user message
        user_message = data["data"]["user_message"]
        assert user_message["content"] == "崇基学院体育馆的开放时间是什么时候"
        assert user_message["role"] == "user"
        assert "file_attachments" in user_message
        
        # Check AI message
        ai_message = data["data"]["ai_message"]
        assert ai_message["role"] == "assistant"
        assert "tokens_used" in ai_message
        assert "cost" in ai_message
        assert "rag_sources" in ai_message

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
                              "file_ids": []
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

    def test_create_chat_invalid_course(self):
        """测试创建聊天时课程不存在"""
        token = get_user_token()
        resp = client.post("/api/v1/chats",
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "chat_type": "course",
                              "first_message": "测试消息",
                              "course_id": 999
                          })
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "COURSE_NOT_FOUND"

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
        # 先创建一个新聊天
        token = get_user_token()
        create_resp = client.post("/api/v1/chats",
                                 headers={"Authorization": f"Bearer {token}"},
                                 json={
                                     "chat_type": "general",
                                     "first_message": "删除测试聊天",
                                     "course_id": None
                                 })
        assert create_resp.status_code == 200
        chat_id = create_resp.json()["data"]["chat"]["id"]
        
        resp = client.delete(f"/api/v1/chats/{chat_id}",
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