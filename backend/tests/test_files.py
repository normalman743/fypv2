import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.semester import Semester
from app.models.course import Course
from app.models.folder import Folder
from app.models.file import File
from app.core.security import get_password_hash, create_access_token
from sqlalchemy.orm import Session
from datetime import datetime
import io

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
    
    # 创建文件夹
    folder = Folder(
        name="讲座",
        folder_type="lecture",
        course_id=1,
        is_default=False
    )
    db.add(folder)
    
    # 创建测试文件
    test_file = File(
        original_name="数据结构第一讲.pdf",
        file_type="course_material",
        file_size=2048000,
        mime_type="application/pdf",
        course_id=1,
        folder_id=1,
        user_id=1,
        is_processed=True,
        processing_status="completed"
    )
    db.add(test_file)
    
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

    def test_get_course_folders_no_auth(self):
        """测试无认证不能获取文件夹"""
        resp = client.get("/api/v1/courses/1/folders")
        assert resp.status_code == 401

    def test_create_folder_success(self):
        """测试创建文件夹"""
        token = get_user_token()
        resp = client.post("/api/v1/courses/1/folders",
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "name": "材料",
                              "folder_type": "material"
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
                              "name": "材料",
                              "folder_type": "material"
                          })
        assert resp.status_code == 401

    def test_create_folder_duplicate_name(self):
        """测试创建重复名称文件夹"""
        token = get_user_token()
        resp = client.post("/api/v1/courses/1/folders",
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "name": "讲座",  # 已存在的名称
                              "folder_type": "lecture"
                          })
        assert resp.status_code == 400
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "FOLDER_NAME_EXISTS"

# 文件管理相关测试
class TestFiles:
    def test_upload_file_success(self):
        """测试上传文件"""
        token = get_user_token()
        test_content = b"This is a test PDF content"
        test_file = ("test.pdf", io.BytesIO(test_content), "application/pdf")
        
        resp = client.post("/api/v1/files/upload",
                          headers={"Authorization": f"Bearer {token}"},
                          files={"file": test_file},
                          data={"course_id": 1, "folder_id": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "file" in data["data"]
        file_data = data["data"]["file"]
        assert "id" in file_data
        assert "original_name" in file_data
        assert file_data["original_name"] == "test.pdf"

    def test_upload_file_no_auth(self):
        """测试无认证不能上传文件"""
        test_content = b"This is a test content"
        test_file = ("test.txt", io.BytesIO(test_content), "text/plain")
        
        resp = client.post("/api/v1/files/upload",
                          files={"file": test_file},
                          data={"course_id": 1, "folder_id": 1})
        assert resp.status_code == 401

    def test_get_folder_files_success(self):
        """测试获取文件夹文件"""
        token = get_user_token()
        resp = client.get("/api/v1/folders/1/files",
                         headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "files" in data["data"]
        assert len(data["data"]["files"]) > 0
        file_data = data["data"]["files"][0]
        assert "id" in file_data
        assert "original_name" in file_data
        assert "folder" in file_data

    def test_get_folder_files_no_auth(self):
        """测试无认证不能获取文件"""
        resp = client.get("/api/v1/folders/1/files")
        assert resp.status_code == 401

    def test_get_file_preview_success(self):
        """测试获取文件预览"""
        token = get_user_token()
        resp = client.get("/api/v1/files/1/preview",
                         headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "id" in data["data"]
        assert "original_name" in data["data"]

    def test_get_file_preview_no_auth(self):
        """测试无认证不能预览文件"""
        resp = client.get("/api/v1/files/1/preview")
        assert resp.status_code == 401

    def test_download_file_success(self):
        """测试下载文件"""
        token = get_user_token()
        resp = client.get("/api/v1/files/1/download",
                         headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "attachment" in resp.headers.get("content-disposition", "").lower()

    def test_download_file_no_auth(self):
        """测试无认证不能下载文件"""
        resp = client.get("/api/v1/files/1/download")
        assert resp.status_code == 401

    def test_delete_file_success(self):
        """测试删除文件"""
        token = get_user_token()
        resp = client.delete("/api/v1/files/1",
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_delete_file_no_auth(self):
        """测试无认证不能删除文件"""
        resp = client.delete("/api/v1/files/1")
        assert resp.status_code == 401 