import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.invite_code import InviteCode
from app.core.security import get_password_hash, create_access_token
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

client = TestClient(app)

def setup_module(module):
    # 每次测试前重建数据库
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    
    # 创建管理员用户
    admin_user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass"),
        role="admin"
    )
    db.add(admin_user)
    
    # 创建普通用户
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass"),
        role="user"
    )
    db.add(user)
    
    # 创建测试邀请码
    invite_code = InviteCode(
        code="TEST2025",
        description="测试邀请码",
        is_used=False,
        expires_at=datetime.now() + timedelta(days=30)
    )
    db.add(invite_code)
    
    db.commit()
    db.close()

def teardown_module(module):
    # 测试后清理数据库
    Base.metadata.drop_all(bind=engine)

def get_admin_token():
    """获取管理员token"""
    token = create_access_token(data={"sub": 1})  # 假设管理员ID为1
    return token

def get_user_token():
    """获取普通用户token"""
    token = create_access_token(data={"sub": 2})  # 假设用户ID为2
    return token

# 邀请码管理相关测试
class TestInviteCodes:
    def test_create_invite_code_success(self):
        """测试创建邀请码"""
        token = get_admin_token()
        resp = client.post("/api/v1/invite-codes", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "description": "学生注册专用",
                              "expires_at": "2025-12-31T23:59:59Z"
                          })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "invite_code" in data["data"]
        invite_code = data["data"]["invite_code"]
        assert "id" in invite_code
        assert "code" in invite_code
        assert "created_at" in invite_code

    def test_create_invite_code_no_auth(self):
        """测试无认证不能创建邀请码"""
        resp = client.post("/api/v1/invite-codes", 
                          json={
                              "description": "学生注册专用",
                              "expires_at": "2025-12-31T23:59:59Z"
                          })
        assert resp.status_code == 401

    def test_create_invite_code_not_admin(self):
        """测试非管理员不能创建邀请码"""
        token = get_user_token()
        resp = client.post("/api/v1/invite-codes", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "description": "学生注册专用",
                              "expires_at": "2025-12-31T23:59:59Z"
                          })
        assert resp.status_code == 403
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    def test_create_invite_code_missing_fields(self):
        """测试缺少必填字段"""
        token = get_admin_token()
        resp = client.post("/api/v1/invite-codes", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "description": "学生注册专用"
                              # 缺少expires_at
                          })
        assert resp.status_code == 422

    def test_get_invite_codes_success(self):
        """测试获取邀请码列表"""
        token = get_admin_token()
        resp = client.get("/api/v1/invite-codes", 
                         headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "invite_codes" in data["data"]
        assert len(data["data"]["invite_codes"]) > 0
        
        invite_code = data["data"]["invite_codes"][0]
        assert "id" in invite_code
        assert "code" in invite_code
        assert "description" in invite_code
        assert "is_used" in invite_code
        assert "expires_at" in invite_code
        assert "created_at" in invite_code

    def test_get_invite_codes_no_auth(self):
        """测试无认证不能获取邀请码列表"""
        resp = client.get("/api/v1/invite-codes")
        assert resp.status_code == 401

    def test_get_invite_codes_not_admin(self):
        """测试非管理员不能获取邀请码列表"""
        token = get_user_token()
        resp = client.get("/api/v1/invite-codes", 
                         headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    def test_update_invite_code_success(self):
        """测试更新邀请码"""
        token = get_admin_token()
        resp = client.put("/api/v1/invite-codes/1", 
                         headers={"Authorization": f"Bearer {token}"},
                         json={
                             "description": "新描述",
                             "expires_at": "2026-01-01T00:00:00Z"
                         })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "invite_code" in data["data"]
        invite_code = data["data"]["invite_code"]
        assert "id" in invite_code
        assert "updated_at" in invite_code

    def test_update_invite_code_no_auth(self):
        """测试无认证不能更新邀请码"""
        resp = client.put("/api/v1/invite-codes/1", 
                         json={
                             "description": "新描述",
                             "expires_at": "2026-01-01T00:00:00Z"
                         })
        assert resp.status_code == 401

    def test_update_invite_code_not_admin(self):
        """测试非管理员不能更新邀请码"""
        token = get_user_token()
        resp = client.put("/api/v1/invite-codes/1", 
                         headers={"Authorization": f"Bearer {token}"},
                         json={
                             "description": "新描述",
                             "expires_at": "2026-01-01T00:00:00Z"
                         })
        assert resp.status_code == 403
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    def test_update_invite_code_not_found(self):
        """测试更新不存在的邀请码"""
        token = get_admin_token()
        resp = client.put("/api/v1/invite-codes/999", 
                         headers={"Authorization": f"Bearer {token}"},
                         json={
                             "description": "新描述",
                             "expires_at": "2026-01-01T00:00:00Z"
                         })
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVITE_CODE_NOT_FOUND"

    def test_delete_invite_code_success(self):
        """测试删除邀请码"""
        token = get_admin_token()
        resp = client.delete("/api/v1/invite-codes/1", 
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_delete_invite_code_no_auth(self):
        """测试无认证不能删除邀请码"""
        resp = client.delete("/api/v1/invite-codes/1")
        assert resp.status_code == 401

    def test_delete_invite_code_not_admin(self):
        """测试非管理员不能删除邀请码"""
        token = get_user_token()
        resp = client.delete("/api/v1/invite-codes/1", 
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    def test_delete_invite_code_not_found(self):
        """测试删除不存在的邀请码"""
        token = get_admin_token()
        resp = client.delete("/api/v1/invite-codes/999", 
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVITE_CODE_NOT_FOUND"

# 系统配置相关测试
class TestSystemConfig:
    def test_get_system_config_success(self):
        """测试获取系统配置"""
        token = get_admin_token()
        resp = client.get("/api/v1/system/config", 
                         headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "config" in data["data"]

    def test_get_system_config_no_auth(self):
        """测试无认证不能获取系统配置"""
        resp = client.get("/api/v1/system/config")
        assert resp.status_code == 401

    def test_get_system_config_not_admin(self):
        """测试非管理员不能获取系统配置"""
        token = get_user_token()
        resp = client.get("/api/v1/system/config", 
                         headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    def test_update_system_config_success(self):
        """测试更新系统配置"""
        token = get_admin_token()
        resp = client.put("/api/v1/system/config", 
                         headers={"Authorization": f"Bearer {token}"},
                         json={
                             "max_file_size": 10485760,
                             "allowed_file_types": ["pdf", "docx", "txt"],
                             "ai_model": "gpt-4",
                             "rag_enabled": True
                         })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "config" in data["data"]

    def test_update_system_config_no_auth(self):
        """测试无认证不能更新系统配置"""
        resp = client.put("/api/v1/system/config", 
                         json={
                             "max_file_size": 10485760
                         })
        assert resp.status_code == 401

    def test_update_system_config_not_admin(self):
        """测试非管理员不能更新系统配置"""
        token = get_user_token()
        resp = client.put("/api/v1/system/config", 
                         headers={"Authorization": f"Bearer {token}"},
                         json={
                             "max_file_size": 10485760
                         })
        assert resp.status_code == 403
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

# 审计日志相关测试
class TestAuditLogs:
    def test_get_audit_logs_success(self):
        """测试获取操作日志"""
        token = get_admin_token()
        resp = client.get("/api/v1/audit-logs", 
                         headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "logs" in data["data"]

    def test_get_audit_logs_no_auth(self):
        """测试无认证不能获取操作日志"""
        resp = client.get("/api/v1/audit-logs")
        assert resp.status_code == 401

    def test_get_audit_logs_not_admin(self):
        """测试非管理员不能获取操作日志"""
        token = get_user_token()
        resp = client.get("/api/v1/audit-logs", 
                         headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    def test_get_audit_logs_with_filters(self):
        """测试带过滤条件的操作日志"""
        token = get_admin_token()
        resp = client.get("/api/v1/audit-logs", 
                         headers={"Authorization": f"Bearer {token}"},
                         params={
                             "user_id": 1,
                             "action": "login",
                             "start_date": "2025-01-01",
                             "end_date": "2025-12-31"
                         })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "logs" in data["data"] 