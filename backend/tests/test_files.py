import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.semester import Semester
from app.models.course import Course
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
    
    # 创建课程
    course = Course(
        name="数据结构与算法",
        code="CS1101A",
        description="学习各种数据结构和算法",
        semester_id=1,
        user_id=1
    )
    db.add(course)
    
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
        """测试获取课程下所有文件夹"""
        resp = client.get("/api/v1/courses/1/folders")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "folders" in data["data"]

    def test_get_course_folders_course_not_found(self):
        """测试获取不存在的课程文件夹"""
        resp = client.get("/api/v1/courses/999/folders")
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "COURSE_NOT_FOUND"

    def test_create_folder_success(self):
        """测试新建课程文件夹"""
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

    def test_create_folder_missing_fields(self):
        """测试缺少必填字段"""
        token = get_user_token()
        resp = client.post("/api/v1/courses/1/folders", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "name": "讲座"
                              # 缺少folder_type
                          })
        assert resp.status_code == 422

# 文件管理相关测试
class TestFiles:
    def test_upload_file_success(self):
        """测试上传文件"""
        token = get_user_token()
        file_content = b"test file content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        data = {"course_id": "1", "folder_id": "1"}
        
        resp = client.post("/api/v1/files/upload", 
                          headers={"Authorization": f"Bearer {token}"},
                          files=files,
                          data=data)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "file" in data["data"]
        file_data = data["data"]["file"]
        assert "id" in file_data
        assert "original_name" in file_data
        assert "file_type" in file_data
        assert "file_size" in file_data
        assert "mime_type" in file_data
        assert "course_id" in file_data
        assert "folder_id" in file_data
        assert "user_id" in file_data
        assert "is_processed" in file_data
        assert "processing_status" in file_data
        assert "created_at" in file_data

    def test_upload_file_no_auth(self):
        """测试无认证不能上传文件"""
        file_content = b"test file content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        data = {"course_id": "1", "folder_id": "1"}
        
        resp = client.post("/api/v1/files/upload", 
                          files=files,
                          data=data)
        assert resp.status_code == 401

    def test_upload_file_missing_file(self):
        """测试缺少文件"""
        token = get_user_token()
        data = {"course_id": "1", "folder_id": "1"}
        
        resp = client.post("/api/v1/files/upload", 
                          headers={"Authorization": f"Bearer {token}"},
                          data=data)
        assert resp.status_code == 422

    def test_get_folder_files_success(self):
        """测试获取文件夹下所有文件"""
        resp = client.get("/api/v1/folders/1/files")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "files" in data["data"]

    def test_get_folder_files_not_found(self):
        """测试获取不存在的文件夹文件"""
        resp = client.get("/api/v1/folders/999/files")
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "FOLDER_NOT_FOUND"

    def test_download_file_success(self):
        """测试下载文件"""
        resp = client.get("/api/v1/files/1/download")
        # 如果文件不存在，应该返回404
        if resp.status_code == 404:
            data = resp.json()
            assert data["success"] is False
            assert data["error"]["code"] == "FILE_NOT_FOUND"
        else:
            assert resp.status_code == 200
            # 检查响应头
            assert "Content-Disposition" in resp.headers
            assert "attachment" in resp.headers["Content-Disposition"]

    def test_preview_file_success(self):
        """测试文件预览"""
        resp = client.get("/api/v1/files/1/preview")
        # 如果文件不存在，应该返回404
        if resp.status_code == 404:
            data = resp.json()
            assert data["success"] is False
            assert data["error"]["code"] == "FILE_NOT_FOUND"
        else:
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert "id" in data["data"]
            assert "original_name" in data["data"]
            assert "file_type" in data["data"]
            assert "file_size" in data["data"]
            assert "mime_type" in data["data"]
            assert "created_at" in data["data"]

    def test_delete_file_success(self):
        """测试删除文件"""
        token = get_user_token()
        resp = client.delete("/api/v1/files/1", 
                           headers={"Authorization": f"Bearer {token}"})
        # 如果文件不存在，应该返回404
        if resp.status_code == 404:
            data = resp.json()
            assert data["success"] is False
            assert data["error"]["code"] == "FILE_NOT_FOUND"
        else:
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True

    def test_delete_file_no_auth(self):
        """测试无认证不能删除文件"""
        resp = client.delete("/api/v1/files/1")
        assert resp.status_code == 401

# 全局文件管理相关测试（可选功能）
class TestGlobalFiles:
    def test_get_global_files_success(self):
        """测试获取全局文件列表"""
        resp = client.get("/api/v1/global-files")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "files" in data["data"]

    def test_upload_global_file_success(self):
        """测试上传全局文件"""
        token = get_user_token()
        file_content = b"global test file content"
        files = {"file": ("global_test.pdf", io.BytesIO(file_content), "application/pdf")}
        
        resp = client.post("/api/v1/global-files/upload", 
                          headers={"Authorization": f"Bearer {token}"},
                          files=files)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "file" in data["data"]

    def test_delete_global_file_success(self):
        """测试删除全局文件"""
        token = get_user_token()
        resp = client.delete("/api/v1/global-files/1", 
                           headers={"Authorization": f"Bearer {token}"})
        # 如果文件不存在，应该返回404
        if resp.status_code == 404:
            data = resp.json()
            assert data["success"] is False
            assert data["error"]["code"] == "FILE_NOT_FOUND"
        else:
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True 