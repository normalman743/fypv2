import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.semester import Semester
from app.models.course import Course
from app.models.folder import Folder
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
    
    # 创建测试课程
    course = Course(
        name="数据结构与算法",
        code="CS1101A",
        description="学习各种数据结构和算法",
        semester_id=1,
        user_id=1
    )
    db.add(course)
    
    # 创建默认文件夹
    folder = Folder(
        name="课程大纲",
        folder_type="outline",
        course_id=1,
        is_default=True
    )
    db.add(folder)
    
    db.commit()
    db.close()

def teardown_module(module):
    # 测试后清理数据库
    Base.metadata.drop_all(bind=engine)

def get_user_token():
    """获取用户token"""
    token = create_access_token(data={"sub": 1})  # 假设用户ID为1
    return token

# 文件夹管理相关测试
class TestFolders:
    def test_get_course_folders_success(self):
        """测试获取课程文件夹"""
        token = get_user_token()
        resp = client.get("/api/v1/courses/1/folders",
                         headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "folders" in data["data"]
        assert len(data["data"]["folders"]) > 0
        folder = data["data"]["folders"][0]
        assert "id" in folder
        assert "name" in folder
        assert "folder_type" in folder
        assert "course_id" in folder
        assert "is_default" in folder
        assert "created_at" in folder
        assert "stats" in folder
        assert "file_count" in folder["stats"]

    def test_get_course_folders_no_auth(self):
        """测试无认证不能获取文件夹"""
        resp = client.get("/api/v1/courses/1/folders")
        assert resp.status_code == 401

    def test_get_course_folders_not_owner(self):
        """测试非课程所有者不能获取文件夹"""
        # 创建另一个用户
        db: Session = SessionLocal()
        other_user = User(
            username="otheruser",
            email="other@example.com",
            hashed_password=get_password_hash("otherpass"),
            role="user"
        )
        db.add(other_user)
        db.commit()
        db.close()
        
        token = create_access_token(data={"sub": 2})  # 其他用户ID
        resp = client.get("/api/v1/courses/1/folders",
                         headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "COURSE_NOT_FOUND"

    def test_get_course_folders_not_found(self):
        """测试获取不存在的课程文件夹"""
        token = get_user_token()
        resp = client.get("/api/v1/courses/999/folders",
                         headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "COURSE_NOT_FOUND"

    def test_create_folder_success(self):
        """测试创建文件夹"""
        token = get_user_token()
        resp = client.post("/api/v1/courses/1/folders",
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "name": "讲座",
                              "folder_type": "lecture"
                          })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "folder" in data["data"]
        assert "id" in data["data"]["folder"]
        assert "created_at" in data["data"]["folder"]

    def test_create_folder_no_auth(self):
        """测试无认证不能创建文件夹"""
        resp = client.post("/api/v1/courses/1/folders",
                          json={
                              "name": "讲座",
                              "folder_type": "lecture"
                          })
        assert resp.status_code == 401

    def test_create_folder_not_owner(self):
        """测试非课程所有者不能创建文件夹"""
        token = create_access_token(data={"sub": 2})  # 其他用户ID
        resp = client.post("/api/v1/courses/1/folders",
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "name": "讲座",
                              "folder_type": "lecture"
                          })
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "COURSE_NOT_FOUND"

    def test_create_folder_duplicate_name(self):
        """测试创建重复名称文件夹"""
        token = get_user_token()
        resp = client.post("/api/v1/courses/1/folders",
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "name": "课程大纲",  # 已存在的名称
                              "folder_type": "outline"
                          })
        assert resp.status_code == 400
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "FOLDER_NAME_EXISTS"

    def test_create_folder_missing_fields(self):
        """测试缺少必填字段"""
        token = get_user_token()
        resp = client.post("/api/v1/courses/1/folders",
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "name": "不完整文件夹"
                              # 缺少folder_type
                          })
        assert resp.status_code == 422

    def test_delete_folder_success(self):
        """测试删除文件夹"""
        # 先创建一个新文件夹
        token = get_user_token()
        create_resp = client.post("/api/v1/courses/1/folders",
                                 headers={"Authorization": f"Bearer {token}"},
                                 json={
                                     "name": "Delete Test Folder",
                                     "folder_type": "material"
                                 })
        assert create_resp.status_code == 200
        folder_id = create_resp.json()["data"]["folder"]["id"]
        
        resp = client.delete(f"/api/v1/folders/{folder_id}",
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_delete_folder_no_auth(self):
        """测试无认证不能删除文件夹"""
        resp = client.delete("/api/v1/folders/1")
        assert resp.status_code == 401

    def test_delete_folder_not_owner(self):
        """测试非课程所有者不能删除文件夹"""
        token = create_access_token(data={"sub": 2})  # 其他用户ID
        resp = client.delete("/api/v1/folders/1",
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "FORBIDDEN"

    def test_delete_folder_default(self):
        """测试不能删除默认文件夹"""
        token = get_user_token()
        resp = client.delete("/api/v1/folders/1",  # 默认文件夹
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 400
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "FOLDER_IS_DEFAULT"

    def test_delete_folder_not_found(self):
        """测试删除不存在的文件夹"""
        token = get_user_token()
        resp = client.delete("/api/v1/folders/999",
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "FOLDER_NOT_FOUND"