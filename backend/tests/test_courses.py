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
    
    db.commit()
    db.close()

def teardown_module(module):
    # 测试后清理数据库
    Base.metadata.drop_all(bind=engine)

def get_user_token():
    """获取用户token"""
    token = create_access_token(data={"sub": 1})  # 假设用户ID为1
    return token

# 课程管理相关测试
class TestCourses:
    def test_get_courses_success(self):
        """测试获取课程列表"""
        resp = client.get("/api/v1/courses")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "courses" in data["data"]
        assert len(data["data"]["courses"]) > 0
        course = data["data"]["courses"][0]
        assert "id" in course
        assert "name" in course
        assert "code" in course
        assert "description" in course
        assert "semester_id" in course
        assert "user_id" in course
        assert "created_at" in course
        assert "semester" in course
        assert "stats" in course

    def test_get_courses_with_semester_filter(self):
        """测试按学期筛选课程"""
        resp = client.get("/api/v1/courses?semester_id=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "courses" in data["data"]
        # 验证所有课程都属于指定学期
        for course in data["data"]["courses"]:
            assert course["semester_id"] == 1

    def test_get_courses_empty_semester(self):
        """测试获取不存在的学期课程"""
        resp = client.get("/api/v1/courses?semester_id=999")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "courses" in data["data"]
        assert len(data["data"]["courses"]) == 0

    def test_create_course_success(self):
        """测试创建课程"""
        token = get_user_token()
        resp = client.post("/api/v1/courses", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "name": "计算机网络",
                              "code": "CS2201A",
                              "description": "学习网络协议和架构",
                              "semester_id": 1
                          })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "course" in data["data"]
        assert "id" in data["data"]["course"]
        assert "created_at" in data["data"]["course"]

    def test_create_course_no_auth(self):
        """测试无认证不能创建课程"""
        resp = client.post("/api/v1/courses", 
                          json={
                              "name": "计算机网络",
                              "code": "CS2201A",
                              "description": "学习网络协议和架构",
                              "semester_id": 1
                          })
        assert resp.status_code == 401

    def test_create_course_duplicate_code(self):
        """测试创建重复课程代码"""
        token = get_user_token()
        resp = client.post("/api/v1/courses", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "name": "重复课程",
                              "code": "CS1101A",  # 已存在的代码
                              "description": "重复的课程",
                              "semester_id": 1
                          })
        assert resp.status_code == 400
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "COURSE_CODE_EXISTS"

    def test_create_course_invalid_semester(self):
        """测试创建课程时学期不存在"""
        token = get_user_token()
        resp = client.post("/api/v1/courses", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "name": "无效学期课程",
                              "code": "CS9999A",
                              "description": "学期不存在的课程",
                              "semester_id": 999
                          })
        assert resp.status_code == 400
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "SEMESTER_NOT_FOUND"

    def test_create_course_missing_fields(self):
        """测试缺少必填字段"""
        token = get_user_token()
        resp = client.post("/api/v1/courses", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={
                              "name": "不完整课程"
                              # 缺少code, semester_id
                          })
        assert resp.status_code == 422

    def test_update_course_success(self):
        """测试更新课程"""
        token = get_user_token()
        resp = client.put("/api/v1/courses/1", 
                         headers={"Authorization": f"Bearer {token}"},
                         json={
                             "name": "数据结构与算法-更新",
                             "description": "更新后的课程描述"
                         })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "course" in data["data"]
        assert "id" in data["data"]["course"]
        assert "updated_at" in data["data"]["course"]

    def test_update_course_no_auth(self):
        """测试无认证不能更新课程"""
        resp = client.put("/api/v1/courses/1", 
                         json={
                             "name": "未授权更新"
                         })
        assert resp.status_code == 401

    def test_update_course_not_owner(self):
        """测试非课程所有者不能更新"""
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
        resp = client.put("/api/v1/courses/1", 
                         headers={"Authorization": f"Bearer {token}"},
                         json={
                             "name": "非所有者更新"
                         })
        assert resp.status_code == 403
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "FORBIDDEN"

    def test_update_course_not_found(self):
        """测试更新不存在的课程"""
        token = get_user_token()
        resp = client.put("/api/v1/courses/999", 
                         headers={"Authorization": f"Bearer {token}"},
                         json={
                             "name": "不存在的课程"
                         })
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "COURSE_NOT_FOUND"

    def test_delete_course_success(self):
        """测试删除课程"""
        # Ensure course exists by creating a new one for this test
        token = get_user_token()
        create_resp = client.post("/api/v1/courses", 
                                headers={"Authorization": f"Bearer {token}"},
                                json={
                                    "name": "Delete Test Course",
                                    "code": "DELETE_TEST",
                                    "description": "Course for delete test",
                                    "semester_id": 1
                                })
        assert create_resp.status_code == 200
        course_id = create_resp.json()["data"]["course"]["id"]
        
        resp = client.delete(f"/api/v1/courses/{course_id}", 
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_delete_course_no_auth(self):
        """测试无认证不能删除课程"""
        resp = client.delete("/api/v1/courses/1")
        assert resp.status_code == 401

    def test_delete_course_not_owner(self):
        """测试非课程所有者不能删除"""
        # 创建另一个用户
        db: Session = SessionLocal()
        other_user = User(
            username="otheruser2",
            email="other2@example.com", 
            hashed_password=get_password_hash("otherpass"),
            role="user"
        )
        db.add(other_user)
        db.commit()
        db.close()
        
        token = create_access_token(data={"sub": 2})  # 其他用户ID
        resp = client.delete("/api/v1/courses/1", 
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "FORBIDDEN"

    def test_delete_course_not_found(self):
        """测试删除不存在的课程"""
        token = get_user_token()
        resp = client.delete("/api/v1/courses/999", 
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "COURSE_NOT_FOUND"
