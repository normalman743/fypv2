"""
Course模块API集成测试 - 基于FastAPI最佳实践

测试覆盖Course模块的11个API端点：
- 学期管理 (管理员权限): 6个API
- 课程管理 (用户权限): 5个API

测试重点：
- 权限验证 (AdminDep vs UserDep)
- 业务逻辑验证 (学期时间、课程唯一性等)
- 数据关联 (学期-课程关系)
- 错误场景覆盖
- 响应格式验证
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from src.course.models import Semester, Course
from src.auth.models import User
from .conftest import assert_success_response, assert_error_response


class TestSemesterManagementAPI:
    """学期管理API测试 - 需要管理员权限"""
    
    @pytest.fixture
    def sample_semester_data(self):
        """标准学期创建数据"""
        return {
            "name": "2025第三学期",
            "code": "2025S3",
            "start_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=150)).isoformat()
        }
    
    @pytest.fixture
    def sample_semester(self, db_session: Session, admin_user: User):
        """创建测试学期"""
        semester = Semester(
            name="测试学期2025",
            code="TEST2025",
            start_date=datetime.utcnow() + timedelta(days=10),
            end_date=datetime.utcnow() + timedelta(days=120),
            is_active=True
        )
        db_session.add(semester)
        db_session.commit()
        db_session.refresh(semester)
        
        # 返回字典以避免DetachedInstanceError
        return {
            "id": semester.id,
            "name": semester.name,
            "code": semester.code,
            "start_date": semester.start_date,
            "end_date": semester.end_date,
            "is_active": semester.is_active
        }
    
    # ========== GET /api/v1/semesters - 获取学期列表 ==========
    
    def test_get_semesters_success_empty(self, client: TestClient, user_headers: dict):
        """测试获取空学期列表"""
        response = client.get("/api/v1/semesters", headers=user_headers)
        
        assert_success_response(response, ["semesters"])
        data = response.json()["data"]
        assert isinstance(data["semesters"], list)
        assert len(data["semesters"]) == 0
        assert "获取学期列表成功" in response.json()["message"]
    
    def test_get_semesters_success_with_data(self, client: TestClient, user_headers: dict, 
                                           db_session: Session, admin_user: User):
        """测试获取有数据的学期列表"""
        # 创建多个学期，包含不同状态
        semesters = []
        for i in range(3):
            semester = Semester(
                name=f"学期{i+1}",
                code=f"SEM{i+1:02d}",
                start_date=datetime.utcnow() + timedelta(days=i*30),
                end_date=datetime.utcnow() + timedelta(days=i*30 + 90),
                is_active=(i < 2)  # 前两个活跃，最后一个不活跃
            )
            semesters.append(semester)
            db_session.add(semester)
        db_session.commit()
        
        response = client.get("/api/v1/semesters", headers=user_headers)
        
        assert_success_response(response, ["semesters"])
        data = response.json()["data"]
        
        # 只返回活跃学期，按开始时间倒序
        assert len(data["semesters"]) == 2
        semester_codes = [s["code"] for s in data["semesters"]]
        assert "SEM03" not in semester_codes  # 不活跃的不返回
        
        # 验证排序（按开始时间倒序）
        start_dates = [s["start_date"] for s in data["semesters"]]
        assert start_dates[0] >= start_dates[1]
        
        # 验证数据结构
        semester = data["semesters"][0]
        expected_fields = ["id", "name", "code", "start_date", "end_date", 
                          "is_active", "created_at", "updated_at"]
        for field in expected_fields:
            assert field in semester
    
    def test_get_semesters_unauthorized(self, client: TestClient):
        """测试未认证访问学期列表"""
        response = client.get("/api/v1/semesters")
        assert_error_response(response, 403, "HTTP_403")
    
    # ========== POST /api/v1/semesters - 创建学期 ==========
    
    def test_create_semester_success(self, client: TestClient, admin_headers: dict, 
                                   sample_semester_data: dict):
        """测试创建学期成功"""
        response = client.post("/api/v1/semesters", 
                             headers=admin_headers, 
                             json=sample_semester_data)
        
        assert_success_response(response, ["semester"], expected_status=201)
        
        data = response.json()["data"]
        assert "id" in data["semester"]
        assert "created_at" in data["semester"]
        assert response.json()["message"] == "学期创建成功"
    
    def test_create_semester_duplicate_code(self, client: TestClient, admin_headers: dict,
                                          sample_semester: dict, sample_semester_data: dict):
        """测试创建重复学期代码"""
        sample_semester_data["code"] = sample_semester["code"]
        
        response = client.post("/api/v1/semesters",
                             headers=admin_headers,
                             json=sample_semester_data)
        
        assert_error_response(response, 409, "SEMESTER_CODE_EXISTS")
        assert sample_semester["code"] in response.json()["error"]["message"]
    
    def test_create_semester_invalid_date_range(self, client: TestClient, admin_headers: dict):
        """测试创建学期 - 结束时间早于开始时间"""
        invalid_data = {
            "name": "无效时间学期", 
            "code": "INVALID01",
            "start_date": (datetime.utcnow() + timedelta(days=100)).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=50)).isoformat()  # 早于开始时间
        }
        
        response = client.post("/api/v1/semesters",
                             headers=admin_headers,
                             json=invalid_data)
        
        # 这个错误应该在Pydantic验证层捕获
        assert response.status_code == 422
    
    def test_create_semester_missing_required_fields(self, client: TestClient, admin_headers: dict):
        """测试创建学期 - 缺少必需字段"""
        incomplete_data = {
            "name": "不完整学期"
            # 缺少 code, start_date, end_date
        }
        
        response = client.post("/api/v1/semesters",
                             headers=admin_headers,
                             json=incomplete_data)
        
        assert response.status_code == 422
    
    def test_create_semester_unauthorized_user(self, client: TestClient, user_headers: dict,
                                             sample_semester_data: dict):
        """测试非管理员创建学期"""
        response = client.post("/api/v1/semesters",
                             headers=user_headers,
                             json=sample_semester_data)
        
        assert_error_response(response, 403, "ADMIN_REQUIRED")
    
    def test_create_semester_no_auth(self, client: TestClient, sample_semester_data: dict):
        """测试未认证创建学期"""
        response = client.post("/api/v1/semesters", json=sample_semester_data)
        assert_error_response(response, 403, "HTTP_403")
    
    # ========== GET /api/v1/semesters/{semester_id} - 获取学期详情 ==========
    
    def test_get_semester_success(self, client: TestClient, user_headers: dict,
                                sample_semester: dict):
        """测试获取学期详情成功"""
        response = client.get(f"/api/v1/semesters/{sample_semester["id"]}",
                             headers=user_headers)
        
        assert_success_response(response, ["semester"])
        
        data = response.json()["data"]
        semester = data["semester"]
        assert semester["id"] == sample_semester["id"]
        assert semester["name"] == sample_semester["name"]
        assert semester["code"] == sample_semester["code"]
        assert semester["is_active"] is True
    
    def test_get_semester_not_found(self, client: TestClient, user_headers: dict):
        """测试获取不存在的学期"""
        response = client.get("/api/v1/semesters/99999", headers=user_headers)
        assert_error_response(response, 404, "SEMESTER_NOT_FOUND")
    
    def test_get_semester_inactive(self, client: TestClient, user_headers: dict,
                                 db_session: Session):
        """测试获取已停用的学期"""
        inactive_semester = Semester(
            name="停用学期",
            code="INACTIVE01",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=90),
            is_active=False
        )
        db_session.add(inactive_semester)
        db_session.commit()
        db_session.refresh(inactive_semester)
        
        response = client.get(f"/api/v1/semesters/{inactive_semester.id}",
                             headers=user_headers)
        
        assert_error_response(response, 404, "SEMESTER_NOT_FOUND")
    
    # ========== PUT /api/v1/semesters/{semester_id} - 更新学期 ==========
    
    def test_update_semester_success(self, client: TestClient, admin_headers: dict,
                                   sample_semester: dict):
        """测试更新学期成功"""
        update_data = {
            "name": "更新后的学期名称",
            "start_date": (datetime.utcnow() + timedelta(days=60)).isoformat()
        }
        
        response = client.put(f"/api/v1/semesters/{sample_semester["id"]}",
                            headers=admin_headers,
                            json=update_data)
        
        assert_success_response(response, ["semester"])
        
        data = response.json()["data"]
        assert "id" in data["semester"]
        assert "updated_at" in data["semester"] 
        assert response.json()["message"] == "学期更新成功"
    
    def test_update_semester_duplicate_code(self, client: TestClient, admin_headers: dict,
                                          db_session: Session, sample_semester: dict):
        """测试更新学期为重复代码"""
        # 创建另一个学期
        another_semester = Semester(
            name="另一个学期",
            code="ANOTHER01", 
            start_date=datetime.utcnow() + timedelta(days=200),
            end_date=datetime.utcnow() + timedelta(days=300),
            is_active=True
        )
        db_session.add(another_semester)
        db_session.commit()
        
        # 尝试将sample_semester的代码更新为another_semester的代码
        update_data = {"code": another_semester.code}
        
        response = client.put(f"/api/v1/semesters/{sample_semester["id"]}",
                            headers=admin_headers,
                            json=update_data)
        
        assert_error_response(response, 409, "SEMESTER_CODE_EXISTS")
    
    def test_update_semester_invalid_date_logic(self, client: TestClient, admin_headers: dict,
                                              sample_semester: dict):
        """测试更新学期 - 违反日期逻辑"""
        update_data = {
            "start_date": (datetime.utcnow() + timedelta(days=200)).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=100)).isoformat()  # 早于开始时间
        }
        
        response = client.put(f"/api/v1/semesters/{sample_semester["id"]}",
                            headers=admin_headers,
                            json=update_data)
        
        assert_error_response(response, 422, "INVALID_DATE_RANGE")
    
    def test_update_semester_not_found(self, client: TestClient, admin_headers: dict):
        """测试更新不存在的学期"""
        update_data = {"name": "不存在的学期"}
        
        response = client.put("/api/v1/semesters/99999",
                            headers=admin_headers,
                            json=update_data)
        
        assert_error_response(response, 404, "SEMESTER_NOT_FOUND")
    
    def test_update_semester_unauthorized(self, client: TestClient, user_headers: dict,
                                        sample_semester: dict):
        """测试非管理员更新学期"""
        update_data = {"name": "无权更新"}
        
        response = client.put(f"/api/v1/semesters/{sample_semester["id"]}",
                            headers=user_headers,
                            json=update_data)
        
        assert_error_response(response, 403, "ADMIN_REQUIRED")
    
    # ========== DELETE /api/v1/semesters/{semester_id} - 删除学期 ==========
    
    def test_delete_semester_success(self, client: TestClient, admin_headers: dict,
                                   sample_semester: dict, db_session: Session):
        """测试删除学期成功 (软删除)"""
        response = client.delete(f"/api/v1/semesters/{sample_semester["id"]}",
                               headers=admin_headers)
        
        assert_success_response(response, [])  # data为空对象
        assert "学期删除成功" in response.json()["message"]  # message在根级别
        
        # 验证软删除 - 重新查询数据库验证状态
        from src.course.models import Semester
        semester_obj = db_session.query(Semester).filter(
            Semester.id == sample_semester["id"]
        ).first()
        assert semester_obj is not None
        assert semester_obj.is_active is False
    
    def test_delete_semester_with_courses(self, client: TestClient, admin_headers: dict,
                                        db_session: Session, sample_semester: dict,
                                        regular_user: User):
        """测试删除有关联课程的学期 - 应该失败"""
        # 创建关联到该学期的课程
        course = Course(
            name="关联课程",
            code="LINKED01",
            description="关联到学期的课程",
            semester_id=sample_semester["id"],
            user_id=regular_user.id
        )
        db_session.add(course)
        db_session.commit()
        
        response = client.delete(f"/api/v1/semesters/{sample_semester["id"]}",
                               headers=admin_headers)
        
        assert_error_response(response, 409, "SEMESTER_HAS_COURSES")
        assert "门课程关联到此学期" in response.json()["error"]["message"]
        
        # 验证学期仍为活跃状态
        db_session.refresh(sample_semester)
        assert sample_semester["is_active"] is True
    
    def test_delete_semester_not_found(self, client: TestClient, admin_headers: dict):
        """测试删除不存在的学期"""
        response = client.delete("/api/v1/semesters/99999", headers=admin_headers)
        assert_error_response(response, 404, "SEMESTER_NOT_FOUND")
    
    def test_delete_semester_unauthorized(self, client: TestClient, user_headers: dict,
                                        sample_semester: dict):
        """测试非管理员删除学期"""
        response = client.delete(f"/api/v1/semesters/{sample_semester["id"]}",
                               headers=user_headers)
        
        assert_error_response(response, 403, "ADMIN_REQUIRED")
    
    # ========== GET /api/v1/semesters/{semester_id}/courses - 获取学期课程 ==========
    
    def test_get_semester_courses_success_empty(self, client: TestClient, user_headers: dict,
                                              sample_semester: dict):
        """测试获取学期课程 - 无课程"""
        response = client.get(f"/api/v1/semesters/{sample_semester["id"]}/courses",
                             headers=user_headers)
        
        assert_success_response(response, ["courses"])
        data = response.json()["data"]
        assert isinstance(data["courses"], list)
        assert len(data["courses"]) == 0
    
    def test_get_semester_courses_success_with_data(self, client: TestClient, user_headers: dict,
                                                  db_session: Session, sample_semester: dict,
                                                  regular_user: User, admin_user: User):
        """测试获取学期课程 - 有课程数据"""
        # 创建多个课程关联到该学期
        courses = []
        for i in range(3):
            course = Course(
                name=f"课程{i+1}",
                code=f"COURSE{i+1:02d}",
                description=f"学期课程{i+1}",
                semester_id=sample_semester["id"],
                user_id=regular_user.id if i < 2 else admin_user.id  # 不同用户的课程
            )
            courses.append(course)
            db_session.add(course)
        db_session.commit()
        
        response = client.get(f"/api/v1/semesters/{sample_semester["id"]}/courses",
                             headers=user_headers)
        
        assert_success_response(response, ["courses"])
        data = response.json()["data"]
        
        assert len(data["courses"]) == 3
        assert f"获取学期 {sample_semester["name"]} 课程列表成功" in response.json()["message"]
        
        # 验证按创建时间倒序排列
        created_ats = [c["created_at"] for c in data["courses"]]
        assert created_ats[0] >= created_ats[1] >= created_ats[2]
        
        # 验证课程数据包含学期信息
        course = data["courses"][0]
        expected_fields = ["id", "name", "code", "description", "semester_id", 
                          "user_id", "created_at", "semester", "stats"]
        for field in expected_fields:
            assert field in course
        
        # 验证学期关联信息
        assert course["semester"]["id"] == sample_semester["id"]
        assert course["semester"]["name"] == sample_semester["name"]
        assert course["semester"]["code"] == sample_semester["code"]
        
        # 验证统计信息结构
        assert "file_count" in course["stats"]
        assert "chat_count" in course["stats"]
    
    def test_get_semester_courses_semester_not_found(self, client: TestClient, user_headers: dict):
        """测试获取不存在学期的课程"""
        response = client.get("/api/v1/semesters/99999/courses", headers=user_headers)
        assert_error_response(response, 404, "SEMESTER_NOT_FOUND")


class TestCourseManagementAPI:
    """课程管理API测试 - 需要用户权限"""
    
    @pytest.fixture
    def sample_course_data(self, sample_semester: dict):
        """标准课程创建数据"""
        return {
            "name": "数据结构与算法",
            "code": "CS101A",
            "description": "学习各种数据结构和算法",
            "semester_id": sample_semester["id"]
        }
    
    @pytest.fixture
    def sample_course(self, db_session: Session, sample_semester: dict, regular_user: User):
        """创建测试课程"""
        course = Course(
            name="测试课程",
            code="TEST101",
            description="这是一个测试课程",
            semester_id=sample_semester["id"],
            user_id=regular_user.id
        )
        db_session.add(course)
        db_session.commit()
        db_session.refresh(course)
        
        # 返回字典以避免DetachedInstanceError
        return {
            "id": course.id,
            "name": course.name,
            "code": course.code,
            "description": course.description,
            "semester_id": course.semester_id,
            "user_id": course.user_id
        }
    
    @pytest.fixture
    def sample_semester(self, db_session: Session):
        """确保有可用的学期"""
        semester = Semester(
            name="课程测试学期",
            code="COURSETEST",
            start_date=datetime.utcnow() + timedelta(days=5),
            end_date=datetime.utcnow() + timedelta(days=95),
            is_active=True
        )
        db_session.add(semester)
        db_session.commit()
        db_session.refresh(semester)
        
        # 返回字典以避免DetachedInstanceError
        return {
            "id": semester.id,
            "name": semester.name,
            "code": semester.code,
            "start_date": semester.start_date,
            "end_date": semester.end_date,
            "is_active": semester.is_active
        }
    
    # ========== GET /api/v1/courses - 获取课程列表 ==========
    
    def test_get_courses_success_empty(self, client: TestClient, user_headers: dict):
        """测试获取空课程列表"""
        response = client.get("/api/v1/courses", headers=user_headers)
        
        assert_success_response(response, ["courses"])
        data = response.json()["data"]
        assert isinstance(data["courses"], list)
        assert len(data["courses"]) == 0
        assert "获取课程列表成功" in response.json()["message"]
    
    def test_get_courses_success_with_data(self, client: TestClient, user_headers: dict,
                                         db_session: Session, sample_semester: dict,
                                         regular_user: User):
        """测试获取用户课程列表"""
        # 创建用户的课程
        user_courses = []
        for i in range(2):
            course = Course(
                name=f"用户课程{i+1}",
                code=f"USER{i+1:02d}",
                description=f"用户的课程{i+1}",
                semester_id=sample_semester["id"],
                user_id=regular_user.id
            )
            user_courses.append(course)
            db_session.add(course)
        
        # 创建其他用户的课程（不应该返回）
        other_course = Course(
            name="其他用户课程",
            code="OTHER01",
            description="不应该出现在结果中",
            semester_id=sample_semester["id"],
            user_id=99999  # 不同用户
        )
        db_session.add(other_course)
        db_session.commit()
        
        response = client.get("/api/v1/courses", headers=user_headers)
        
        assert_success_response(response, ["courses"])
        data = response.json()["data"]
        
        # 只返回当前用户的课程
        assert len(data["courses"]) == 2
        for course in data["courses"]:
            assert course["user_id"] == regular_user.id
            assert course["code"] in ["USER01", "USER02"]
        
        # 验证课程包含学期信息
        course = data["courses"][0]
        assert "semester" in course
        assert course["semester"]["name"] == sample_semester["name"]
    
    def test_get_courses_filter_by_semester(self, client: TestClient, user_headers: dict,
                                          db_session: Session, regular_user: User):
        """测试按学期过滤课程"""
        # 创建两个学期
        semester1 = Semester(
            name="学期1", code="SEM1", 
            start_date=datetime.utcnow() + timedelta(days=1),
            end_date=datetime.utcnow() + timedelta(days=91),
            is_active=True
        )
        semester2 = Semester(
            name="学期2", code="SEM2",
            start_date=datetime.utcnow() + timedelta(days=100),
            end_date=datetime.utcnow() + timedelta(days=190),
            is_active=True
        )
        db_session.add_all([semester1, semester2])
        db_session.commit()
        
        # 在每个学期创建课程
        course1 = Course(name="课程1", code="C1", semester_id=semester1.id, user_id=regular_user.id)
        course2 = Course(name="课程2", code="C2", semester_id=semester2.id, user_id=regular_user.id)
        db_session.add_all([course1, course2])
        db_session.commit()
        
        # 测试按学期1过滤
        response = client.get(f"/api/v1/courses?semester_id={semester1.id}",
                             headers=user_headers)
        
        assert_success_response(response, ["courses"])
        data = response.json()["data"]
        
        assert len(data["courses"]) == 1
        assert data["courses"][0]["name"] == "课程1"
        assert data["courses"][0]["semester_id"] == semester1.id
    
    def test_get_courses_invalid_semester_filter(self, client: TestClient, user_headers: dict):
        """测试无效的学期ID过滤"""
        response = client.get("/api/v1/courses?semester_id=0", headers=user_headers)
        
        # semester_id应该有ge=1的验证
        assert response.status_code == 422
    
    def test_get_courses_unauthorized(self, client: TestClient):
        """测试未认证访问课程列表"""
        response = client.get("/api/v1/courses")
        assert_error_response(response, 403, "HTTP_403")
    
    # ========== POST /api/v1/courses - 创建课程 ==========
    
    def test_create_course_success(self, client: TestClient, user_headers: dict,
                                 sample_course_data: dict):
        """测试创建课程成功"""
        response = client.post("/api/v1/courses",
                             headers=user_headers,
                             json=sample_course_data)
        
        assert_success_response(response, ["course"], expected_status=201)
        
        data = response.json()["data"]
        assert "id" in data["course"]
        assert "created_at" in data["course"]
        assert response.json()["message"] == "课程创建成功"
    
    def test_create_course_duplicate_code_same_user_semester(self, client: TestClient, user_headers: dict,
                                                           sample_course: dict, sample_semester: dict):
        """测试同一用户在同一学期创建重复课程代码"""
        duplicate_data = {
            "name": "重复课程",
            "code": sample_course["code"],  # 相同代码
            "description": "试图创建重复代码",
            "semester_id": sample_semester["id"]  # 相同学期
        }
        
        response = client.post("/api/v1/courses",
                             headers=user_headers,
                             json=duplicate_data)
        
        assert_error_response(response, 409, "COURSE_CODE_EXISTS")
        assert sample_course["code"] in response.json()["error"]["message"]
        assert "在此学期内已存在" in response.json()["error"]["message"]
    
    def test_create_course_same_code_different_semester_allowed(self, client: TestClient, user_headers: dict,
                                                              db_session: Session, sample_course: dict):
        """测试同一用户在不同学期可以使用相同课程代码"""
        # 创建另一个学期
        another_semester = Semester(
            name="另一个学期",
            code="ANOTHER",
            start_date=datetime.utcnow() + timedelta(days=200),
            end_date=datetime.utcnow() + timedelta(days=290),
            is_active=True
        )
        db_session.add(another_semester)
        db_session.commit()
        
        same_code_data = {
            "name": "相同代码课程",
            "code": sample_course["code"],  # 相同代码
            "description": "在不同学期使用相同代码",
            "semester_id": another_semester.id  # 不同学期
        }
        
        response = client.post("/api/v1/courses",
                             headers=user_headers,
                             json=same_code_data)
        
        # 应该成功
        assert_success_response(response, ["course"], expected_status=201)
    
    def test_create_course_inactive_semester(self, client: TestClient, user_headers: dict,
                                           db_session: Session):
        """测试在停用学期创建课程"""
        inactive_semester = Semester(
            name="停用学期",
            code="INACTIVE",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=90),
            is_active=False  # 停用状态
        )
        db_session.add(inactive_semester)
        db_session.commit()
        
        course_data = {
            "name": "测试课程",
            "code": "TESTINACTIVE",
            "description": "试图在停用学期创建",
            "semester_id": inactive_semester.id
        }
        
        response = client.post("/api/v1/courses",
                             headers=user_headers,
                             json=course_data)
        
        assert_error_response(response, 400, "SEMESTER_NOT_FOUND")
        assert "学期不存在或已停用" in response.json()["error"]["message"]
    
    def test_create_course_nonexistent_semester(self, client: TestClient, user_headers: dict):
        """测试在不存在的学期创建课程"""
        course_data = {
            "name": "测试课程",
            "code": "TESTNONEXIST",
            "description": "试图在不存在的学期创建",
            "semester_id": 99999
        }
        
        response = client.post("/api/v1/courses",
                             headers=user_headers,
                             json=course_data)
        
        assert_error_response(response, 400, "SEMESTER_NOT_FOUND")
    
    def test_create_course_missing_required_fields(self, client: TestClient, user_headers: dict):
        """测试创建课程 - 缺少必需字段"""
        incomplete_data = {
            "name": "不完整课程"
            # 缺少 code, semester_id
        }
        
        response = client.post("/api/v1/courses",
                             headers=user_headers,
                             json=incomplete_data)
        
        assert response.status_code == 422
    
    def test_create_course_unauthorized(self, client: TestClient, sample_course_data: dict):
        """测试未认证创建课程"""
        response = client.post("/api/v1/courses", json=sample_course_data)
        assert_error_response(response, 403, "HTTP_403")
    
    # ========== GET /api/v1/courses/{course_id} - 获取课程详情 ==========
    
    def test_get_course_success(self, client: TestClient, user_headers: dict,
                              sample_course: dict):
        """测试获取课程详情成功"""
        response = client.get(f"/api/v1/courses/{sample_course["id"]}",
                             headers=user_headers)
        
        assert_success_response(response, ["course"])
        
        data = response.json()["data"]
        course = data["course"]
        assert course["id"] == sample_course["id"]
        assert course["name"] == sample_course.name
        assert course["code"] == sample_course["code"]
        assert course["description"] == sample_course.description
        
        # 验证包含学期信息
        assert "semester" in course
        assert course["semester"]["id"] == sample_course.semester_id
        
        # 验证包含统计信息
        assert "stats" in course
        assert "file_count" in course["stats"]
        assert "chat_count" in course["stats"]
    
    def test_get_course_not_found(self, client: TestClient, user_headers: dict):
        """测试获取不存在的课程"""
        response = client.get("/api/v1/courses/99999", headers=user_headers)
        assert_error_response(response, 404, "COURSE_NOT_FOUND")
    
    def test_get_course_access_denied(self, client: TestClient, user_headers: dict,
                                    db_session: Session, sample_semester: dict):
        """测试访问其他用户的课程"""
        # 创建属于其他用户的课程
        other_course = Course(
            name="其他用户课程",
            code="OTHER",
            description="属于其他用户",
            semester_id=sample_semester["id"],
            user_id=88888  # 不同的用户ID
        )
        db_session.add(other_course)
        db_session.commit()
        db_session.refresh(other_course)
        
        response = client.get(f"/api/v1/courses/{other_course.id}",
                             headers=user_headers)
        
        assert_error_response(response, 403, "COURSE_ACCESS_DENIED")
        assert "无权访问此课程" in response.json()["error"]["message"]
    
    # ========== PUT /api/v1/courses/{course_id} - 更新课程 ==========
    
    def test_update_course_success(self, client: TestClient, user_headers: dict,
                                 sample_course: dict):
        """测试更新课程成功"""
        update_data = {
            "name": "更新后的课程名称",
            "description": "更新后的描述"
        }
        
        response = client.put(f"/api/v1/courses/{sample_course["id"]}",
                            headers=user_headers,
                            json=update_data)
        
        assert_success_response(response, ["course"])
        
        data = response.json()["data"]
        assert "id" in data["course"]
        assert "updated_at" in data["course"]
        assert response.json()["message"] == "课程更新成功"
    
    def test_update_course_duplicate_code(self, client: TestClient, user_headers: dict,
                                        db_session: Session, sample_course: dict,
                                        sample_semester: dict, regular_user: User):
        """测试更新课程为重复代码"""
        # 创建另一个课程
        another_course = Course(
            name="另一个课程",
            code="ANOTHER",
            description="另一个测试课程",
            semester_id=sample_semester["id"],
            user_id=regular_user.id
        )
        db_session.add(another_course)
        db_session.commit()
        
        # 尝试将sample_course的代码更新为another_course的代码
        update_data = {"code": another_course.code}
        
        response = client.put(f"/api/v1/courses/{sample_course["id"]}",
                            headers=user_headers,
                            json=update_data)
        
        assert_error_response(response, 409, "COURSE_CODE_EXISTS")
    
    def test_update_course_not_found(self, client: TestClient, user_headers: dict):
        """测试更新不存在的课程"""
        update_data = {"name": "不存在的课程"}
        
        response = client.put("/api/v1/courses/99999",
                            headers=user_headers,
                            json=update_data)
        
        assert_error_response(response, 404, "COURSE_NOT_FOUND")
    
    def test_update_course_access_denied(self, client: TestClient, user_headers: dict,
                                       db_session: Session, sample_semester: dict):
        """测试更新其他用户的课程"""
        other_course = Course(
            name="其他用户课程",
            code="OTHERUSER",
            description="属于其他用户",
            semester_id=sample_semester["id"],
            user_id=77777
        )
        db_session.add(other_course)
        db_session.commit()
        db_session.refresh(other_course)
        
        update_data = {"name": "无权更新"}
        
        response = client.put(f"/api/v1/courses/{other_course.id}",
                            headers=user_headers,
                            json=update_data)
        
        assert_error_response(response, 403, "COURSE_UPDATE_DENIED")
    
    # ========== DELETE /api/v1/courses/{course_id} - 删除课程 ==========
    
    def test_delete_course_success(self, client: TestClient, user_headers: dict,
                                 sample_course: dict, db_session: Session):
        """测试删除课程成功"""
        course_id = sample_course["id"]
        
        response = client.delete(f"/api/v1/courses/{course_id}",
                               headers=user_headers)
        
        assert_success_response(response, ["message"])
        assert "课程删除成功" in response.json()["data"]["message"]
        
        # 验证物理删除 - 课程不再存在
        deleted_course = db_session.query(Course).filter(Course.id == course_id).first()
        assert deleted_course is None
    
    def test_delete_course_not_found(self, client: TestClient, user_headers: dict):
        """测试删除不存在的课程"""
        response = client.delete("/api/v1/courses/99999", headers=user_headers)
        assert_error_response(response, 404, "COURSE_NOT_FOUND")
    
    def test_delete_course_access_denied(self, client: TestClient, user_headers: dict,
                                       db_session: Session, sample_semester: dict):
        """测试删除其他用户的课程"""
        other_course = Course(
            name="其他用户课程",
            code="DELETEOTHER",
            description="无权删除",
            semester_id=sample_semester["id"],
            user_id=66666
        )
        db_session.add(other_course)
        db_session.commit()
        db_session.refresh(other_course)
        
        response = client.delete(f"/api/v1/courses/{other_course.id}",
                               headers=user_headers)
        
        assert_error_response(response, 403, "COURSE_DELETE_DENIED")


class TestCoursePermissionSecurity:
    """Course模块权限安全测试"""
    
    @pytest.fixture
    def sample_semester(self, db_session: Session):
        """测试学期"""
        semester = Semester(
            name="权限测试学期",
            code="PERMTEST",
            start_date=datetime.utcnow() + timedelta(days=1),
            end_date=datetime.utcnow() + timedelta(days=91),
            is_active=True
        )
        db_session.add(semester)
        db_session.commit()
        db_session.refresh(semester)
        
        # 返回字典以避免DetachedInstanceError
        return {
            "id": semester.id,
            "name": semester.name,
            "code": semester.code,
            "start_date": semester.start_date,
            "end_date": semester.end_date,
            "is_active": semester.is_active
        }
    
    def test_semester_admin_endpoints_require_admin_role(self, client: TestClient, user_headers: dict,
                                                       sample_semester: dict):
        """测试学期管理端点需要管理员权限"""
        admin_endpoints = [
            ("POST", "/api/v1/semesters", {"name": "test", "code": "TEST", 
                                         "start_date": datetime.utcnow().isoformat(),
                                         "end_date": (datetime.utcnow() + timedelta(days=90)).isoformat()}),
            ("PUT", f"/api/v1/semesters/{sample_semester["id"]}", {"name": "updated"}),
            ("DELETE", f"/api/v1/semesters/{sample_semester["id"]}", None),
        ]
        
        for method, endpoint, payload in admin_endpoints:
            if method == "POST":
                response = client.post(endpoint, headers=user_headers, json=payload)
            elif method == "PUT":
                response = client.put(endpoint, headers=user_headers, json=payload)
            elif method == "DELETE":
                response = client.delete(endpoint, headers=user_headers)
            
            assert_error_response(response, 403, "ADMIN_REQUIRED"), f"Failed for {method} {endpoint}"
    
    def test_all_endpoints_require_authentication(self, client: TestClient):
        """测试所有端点都需要认证"""
        endpoints = [
            ("GET", "/api/v1/semesters", None),
            ("POST", "/api/v1/semesters", {"name": "test", "code": "TEST",
                                         "start_date": datetime.utcnow().isoformat(),
                                         "end_date": (datetime.utcnow() + timedelta(days=90)).isoformat()}),
            ("GET", "/api/v1/semesters/1", None),
            ("PUT", "/api/v1/semesters/1", {"name": "updated"}),
            ("DELETE", "/api/v1/semesters/1", None),
            ("GET", "/api/v1/semesters/1/courses", None),
            ("GET", "/api/v1/courses", None),
            ("POST", "/api/v1/courses", {"name": "test", "code": "TEST", "semester_id": 1}),
            ("GET", "/api/v1/courses/1", None),
            ("PUT", "/api/v1/courses/1", {"name": "updated"}),
            ("DELETE", "/api/v1/courses/1", None),
        ]
        
        for method, endpoint, payload in endpoints:
            if method == "POST":
                response = client.post(endpoint, json=payload)
            elif method == "PUT":
                response = client.put(endpoint, json=payload)
            elif method == "DELETE":
                response = client.delete(endpoint)
            else:  # GET
                response = client.get(endpoint)
            
            assert_error_response(response, 403, "HTTP_403"), f"Failed for {method} {endpoint}"


class TestCourseDataValidation:
    """Course模块数据验证测试"""
    
    def test_semester_date_validation(self, client: TestClient, admin_headers: dict):
        """测试学期日期验证"""
        # 结束时间早于开始时间
        invalid_data = {
            "name": "无效日期学期",
            "code": "INVALID",
            "start_date": "2025-12-31T23:59:59Z",
            "end_date": "2025-01-01T00:00:00Z"
        }
        
        response = client.post("/api/v1/semesters",
                             headers=admin_headers,
                             json=invalid_data)
        
        assert response.status_code == 422
        assert "结束时间必须晚于开始时间" in str(response.content)
    
    def test_course_field_validation(self, client: TestClient, user_headers: dict,
                                   sample_semester: dict):
        """测试课程字段验证"""
        # 空课程名称
        invalid_data = {
            "name": "",  # 空名称
            "code": "VALID",
            "semester_id": sample_semester["id"]
        }
        
        response = client.post("/api/v1/courses",
                             headers=user_headers,
                             json=invalid_data)
        
        assert response.status_code == 422
    
    @pytest.fixture
    def sample_semester(self, db_session: Session):
        """确保有可用的学期"""
        semester = Semester(
            name="验证测试学期",
            code="VALIDTEST",
            start_date=datetime.utcnow() + timedelta(days=1),
            end_date=datetime.utcnow() + timedelta(days=91),
            is_active=True
        )
        db_session.add(semester)
        db_session.commit()
        db_session.refresh(semester)
        
        # 返回字典以避免DetachedInstanceError
        return {
            "id": semester.id,
            "name": semester.name,
            "code": semester.code,
            "start_date": semester.start_date,
            "end_date": semester.end_date,
            "is_active": semester.is_active
        }