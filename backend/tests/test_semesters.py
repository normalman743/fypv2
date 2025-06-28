import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.semester import Semester
from app.core.security import get_password_hash, create_access_token
from sqlalchemy.orm import Session
from datetime import datetime

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
    normal_user = User(
        username="user",
        email="user@example.com",
        hashed_password=get_password_hash("userpass"),
        role="user"
    )
    db.add(normal_user)
    
    # 创建测试学期
    semester = Semester(
        name="2025第一学期",
        code="2025S1",
        start_date=datetime(2025, 3, 1),
        end_date=datetime(2025, 6, 30),
        is_active=True
    )
    db.add(semester)
    
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
    token = create_access_token(data={"sub": 2})  # 假设普通用户ID为2
    return token

# 学期管理相关测试
class TestSemesters:
    def test_get_semesters_success(self):
        """测试获取学期列表"""
        resp = client.get("/api/v1/semesters")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "semesters" in data["data"]
        assert len(data["data"]["semesters"]) > 0
        semester = data["data"]["semesters"][0]
        assert "id" in semester
        assert "name" in semester
        assert "code" in semester
        assert "start_date" in semester
        assert "end_date" in semester
        assert "is_active" in semester

    def test_create_semester_admin_success(self):
        """测试管理员创建学期"""
        token = get_admin_token()
        resp = client.post("/api/v1/semesters", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "name": "2025第四学期",
                              "code": "2025S4",
                              "start_date": "2025-12-01T00:00:00Z",
                              "end_date": "2026-02-28T23:59:59Z"
                          })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "semester" in data["data"]
        assert "id" in data["data"]["semester"]
        assert "created_at" in data["data"]["semester"]

    def test_create_semester_user_forbidden(self):
        """测试普通用户不能创建学期"""
        token = get_user_token()
        resp = client.post("/api/v1/semesters", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "name": "2025第四学期",
                              "code": "2025S4",
                              "start_date": "2025-12-01T00:00:00Z",
                              "end_date": "2026-02-28T23:59:59Z"
                          })
        assert resp.status_code == 403
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "FORBIDDEN"

    def test_create_semester_no_auth(self):
        """测试无认证不能创建学期"""
        resp = client.post("/api/v1/semesters", 
                          json={
                              "name": "2025第四学期",
                              "code": "2025S4",
                              "start_date": "2025-12-01T00:00:00Z",
                              "end_date": "2026-02-28T23:59:59Z"
                          })
        assert resp.status_code == 401

    def test_create_semester_duplicate_code(self):
        """测试创建重复学期代码"""
        token = get_admin_token()
        resp = client.post("/api/v1/semesters", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "name": "重复学期",
                              "code": "2025S1",  # 已存在的代码
                              "start_date": "2025-12-01T00:00:00Z",
                              "end_date": "2026-02-28T23:59:59Z"
                          })
        assert resp.status_code == 400
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "SEMESTER_CODE_EXISTS"

    def test_create_semester_missing_fields(self):
        """测试缺少必填字段"""
        token = get_admin_token()
        resp = client.post("/api/v1/semesters", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "name": "不完整学期"
                              # 缺少code, start_date, end_date
                          })
        assert resp.status_code == 422

    def test_update_semester_admin_success(self):
        """测试管理员更新学期"""
        token = get_admin_token()
        resp = client.put("/api/v1/semesters/1", 
                         headers={"Authorization": f"Bearer {token}"},
                         json={
                             "name": "2025第一学期-更新",
                             "start_date": "2025-03-01T00:00:00Z",
                             "end_date": "2025-06-30T23:59:59Z",
                             "is_active": False
                         })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "semester" in data["data"]
        assert "id" in data["data"]["semester"]
        assert "updated_at" in data["data"]["semester"]

    def test_update_semester_user_forbidden(self):
        """测试普通用户不能更新学期"""
        token = get_user_token()
        resp = client.put("/api/v1/semesters/1", 
                         headers={"Authorization": f"Bearer {token}"},
                         json={
                             "name": "2025第一学期-更新"
                         })
        assert resp.status_code == 403
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "FORBIDDEN"

    def test_update_semester_not_found(self):
        """测试更新不存在的学期"""
        token = get_admin_token()
        resp = client.put("/api/v1/semesters/999", 
                         headers={"Authorization": f"Bearer {token}"},
                         json={
                             "name": "不存在的学期"
                         })
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "SEMESTER_NOT_FOUND"

    def test_delete_semester_admin_success(self):
        """测试管理员删除学期"""
        token = get_admin_token()
        resp = client.delete("/api/v1/semesters/1", 
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_delete_semester_user_forbidden(self):
        """测试普通用户不能删除学期"""
        token = get_user_token()
        resp = client.delete("/api/v1/semesters/1", 
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "FORBIDDEN"

    def test_delete_semester_not_found(self):
        """测试删除不存在的学期"""
        token = get_admin_token()
        resp = client.delete("/api/v1/semesters/999", 
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "SEMESTER_NOT_FOUND"
