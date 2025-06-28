import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.database import SessionLocal, Base, engine
from app.models.user import User
from app.core.security import get_password_hash, create_access_token
from sqlalchemy.orm import Session
import os
import tempfile
from app.models.invite_code import InviteCode
from datetime import datetime, timedelta

client = TestClient(app)

def setup_module(module):
    # 每次测试前重建数据库
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    # 插入一个已存在用户
    user = User(
        username="existuser",
        email="exist@example.com",
        hashed_password=get_password_hash("existpass"),
        role="user"
    )
    db.add(user)
    # 插入测试邀请码
    code = InviteCode(
        code='INVITE2025',
        description='测试邀请码',
        is_used=False,
        expires_at=datetime.now() + timedelta(days=30)
    )
    db.add(code)
    db.commit()
    db.close()

def teardown_module(module):
    # 测试后清理数据库
    Base.metadata.drop_all(bind=engine)

def get_auth_token(username="existuser"):
    """获取认证token的辅助函数"""
    token = create_access_token(data={"sub": 1})  # 假设用户ID为1
    return token

# 注册相关测试
class TestRegister:
    def test_register_success(self):
        resp = client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123",
            "invite_code": "INVITE2025"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "user" in data["data"]
        assert data["data"]["user"]["email"] == "newuser@example.com"
        assert data["data"]["user"]["username"] == "newuser"
        assert data["data"]["user"]["role"] == "user"

    def test_register_duplicate_username(self):
        resp = client.post("/api/v1/auth/register", json={
            "email": "other@example.com",
            "username": "existuser",
            "password": "password123",
            "invite_code": "INVITE2025"
        })
        assert resp.status_code == 400
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "USERNAME_EXISTS"

    def test_register_duplicate_email(self):
        resp = client.post("/api/v1/auth/register", json={
            "email": "exist@example.com",
            "username": "otheruser",
            "password": "password123",
            "invite_code": "INVITE2025"
        })
        assert resp.status_code == 400
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "EMAIL_EXISTS"

    def test_register_invalid_invite_code(self):
        resp = client.post("/api/v1/auth/register", json={
            "email": "invfail@example.com",
            "username": "invfail",
            "password": "password123",
            "invite_code": "WRONGCODE"
        })
        assert resp.status_code == 400
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_INVITE_CODE"

    def test_register_missing_fields(self):
        resp = client.post("/api/v1/auth/register", json={
            "email": "miss@example.com",
            "password": "password123",
            "invite_code": "INVITE2025"
        })
        assert resp.status_code == 422  # FastAPI自动校验

# 登录相关测试
class TestLogin:
    def test_login_success(self):
        # 先注册
        client.post("/api/v1/auth/register", json={
            "email": "logintest@example.com",
            "username": "logintest",
            "password": "password123",
            "invite_code": "INVITE2025"
        })
        resp = client.post("/api/v1/auth/login", json={
            "username": "logintest",
            "password": "password123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert data["data"]["user"]["username"] == "logintest"

    def test_login_wrong_password(self):
        resp = client.post("/api/v1/auth/login", json={
            "username": "existuser",
            "password": "wrongpass"
        })
        assert resp.status_code == 400
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_CREDENTIALS"

    def test_login_user_not_exist(self):
        resp = client.post("/api/v1/auth/login", json={
            "username": "notexist",
            "password": "password123"
        })
        assert resp.status_code == 400
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_CREDENTIALS"

    def test_login_missing_fields(self):
        resp = client.post("/api/v1/auth/login", json={
            "username": "existuser"
        })
        assert resp.status_code == 422

# 获取用户信息相关测试
class TestGetMe:
    def test_get_me_success(self):
        token = get_auth_token()
        resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "id" in data["data"]
        assert "username" in data["data"]
        assert "email" in data["data"]
        assert "role" in data["data"]
        assert "balance" in data["data"]
        assert "total_spent" in data["data"]

    def test_get_me_no_token(self):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "UNAUTHORIZED"

    def test_get_me_invalid_token(self):
        resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"})
        assert resp.status_code == 401
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "UNAUTHORIZED"

# 更新用户信息相关测试
class TestUpdateMe:
    def test_update_me_success(self):
        token = get_auth_token()
        resp = client.put("/api/v1/auth/me", 
                         headers={"Authorization": f"Bearer {token}"},
                         json={
                             "username": "new_username",
                             "preferred_language": "en",
                             "preferred_theme": "dark"
                         })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["username"] == "new_username"
        assert data["data"]["preferred_language"] == "en"
        assert data["data"]["preferred_theme"] == "dark"

    def test_update_me_partial_fields(self):
        token = get_auth_token()
        resp = client.put("/api/v1/auth/me", 
                         headers={"Authorization": f"Bearer {token}"},
                         json={
                             "preferred_language": "zh_CN"
                         })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["preferred_language"] == "zh_CN"

    def test_update_me_no_token(self):
        resp = client.put("/api/v1/auth/me", json={"username": "new_username"})
        assert resp.status_code == 401
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "UNAUTHORIZED"

    def test_update_me_duplicate_username(self):
        # 先创建另一个用户
        client.post("/api/v1/auth/register", json={
            "email": "other@example.com",
            "username": "otheruser",
            "password": "password123",
            "invite_code": "INVITE2025"
        })
        
        token = get_auth_token()
        resp = client.put("/api/v1/auth/me", 
                         headers={"Authorization": f"Bearer {token}"},
                         json={"username": "otheruser"})
        assert resp.status_code == 400
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "USERNAME_EXISTS"

# 登出相关测试
class TestLogout:
    def test_logout_success(self):
        token = get_auth_token()
        resp = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["message"] == "已成功登出"

    def test_logout_no_token(self):
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 401
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "UNAUTHORIZED"

    def test_logout_invalid_token(self):
        resp = client.post("/api/v1/auth/logout", headers={"Authorization": "Bearer invalid_token"})
        assert resp.status_code == 401
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "UNAUTHORIZED"
