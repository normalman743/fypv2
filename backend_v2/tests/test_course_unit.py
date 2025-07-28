"""
Course模块单元测试 - Service层业务逻辑测试

基于FastAPI最佳实践，测试SemesterService和CourseService的所有方法：
- 覆盖业务逻辑、异常处理和边界条件
- 使用真实数据库环境 + 事务回滚策略确保测试隔离
- 遵循项目METHOD_EXCEPTIONS声明模式

测试覆盖：
SemesterService: 6个方法
CourseService: 5个方法
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from unittest.mock import patch
import uuid

# 导入模型
from src.course.models import Semester, Course
from src.auth.models import User

# 导入服务和schemas
from src.course.service import SemesterService, CourseService
from src.course.schemas import (
    CreateSemesterRequest, UpdateSemesterRequest,
    CreateCourseRequest, UpdateCourseRequest
)

# 导入异常
from src.shared.exceptions import (
    BadRequestError, NotFoundError, ConflictError, ForbiddenError
)


class TestSemesterService:
    """学期服务类测试"""
    
    @pytest.fixture
    def semester_service(self, db_session: Session) -> SemesterService:
        """创建SemesterService实例"""
        return SemesterService(db_session)
    
    @pytest.fixture
    def sample_semester(self, db_session: Session) -> Semester:
        """创建测试学期"""
        semester = Semester(
            name="测试学期2024",
            code="TEST2024",
            start_date=datetime.utcnow() + timedelta(days=30),
            end_date=datetime.utcnow() + timedelta(days=120),
            is_active=True
        )
        db_session.add(semester)
        db_session.commit()
        db_session.refresh(semester)
        return semester
    
    @pytest.fixture
    def inactive_semester(self, db_session: Session) -> Semester:
        """创建停用学期"""
        semester = Semester(
            name="停用学期",
            code="INACTIVE2024",
            start_date=datetime.utcnow() - timedelta(days=100),
            end_date=datetime.utcnow() - timedelta(days=10),
            is_active=False
        )
        db_session.add(semester)
        db_session.commit()
        db_session.refresh(semester)
        return semester
    
    # ========== get_semesters 测试 ==========
    
    def test_get_semesters_success_empty(self, semester_service: SemesterService):
        """测试获取空学期列表"""
        result = semester_service.get_semesters()
        
        assert "semesters" in result
        assert "message" in result
        assert result["semesters"] == []
        assert result["message"] == "获取学期列表成功"
    
    def test_get_semesters_success_with_data(self, semester_service: SemesterService, 
                                           db_session: Session):
        """测试获取有数据的学期列表"""
        # 创建多个学期，包括活跃和非活跃
        semesters_data = [
            ("学期1", "SEM1", True, 10),
            ("学期2", "SEM2", True, 20),  
            ("学期3", "SEM3", False, 30),  # 非活跃
        ]
        
        for name, code, is_active, days_offset in semesters_data:
            semester = Semester(
                name=name,
                code=code,
                start_date=datetime.utcnow() + timedelta(days=days_offset),
                end_date=datetime.utcnow() + timedelta(days=days_offset + 90),
                is_active=is_active
            )
            db_session.add(semester)
        db_session.commit()
        
        result = semester_service.get_semesters()
        
        # 只返回活跃学期
        assert len(result["semesters"]) == 2
        semester_codes = [s.code for s in result["semesters"]]
        assert "SEM1" in semester_codes
        assert "SEM2" in semester_codes
        assert "SEM3" not in semester_codes  # 非活跃的不返回
        
        # 验证按开始时间倒序排列
        start_dates = [s.start_date for s in result["semesters"]]
        assert start_dates[0] >= start_dates[1]
    
    def test_get_semesters_exception_handling(self, semester_service: SemesterService):
        """测试获取学期列表异常处理"""
        # 由于METHOD_EXCEPTIONS声明get_semesters无异常，这里测试数据库异常的处理
        with patch.object(semester_service.db, 'query') as mock_query:
            mock_query.side_effect = Exception("Database error")
            
            with pytest.raises(BadRequestError) as exc_info:
                semester_service.get_semesters()
            
            assert "获取学期列表失败" in str(exc_info.value)
    
    # ========== get_semester 测试 ==========
    
    def test_get_semester_success(self, semester_service: SemesterService, 
                                sample_semester: Semester):
        """测试获取学期详情成功"""
        result = semester_service.get_semester(sample_semester.id)
        
        assert "semester" in result
        assert "message" in result
        assert result["semester"].id == sample_semester.id
        assert result["semester"].name == sample_semester.name
        assert result["semester"].code == sample_semester.code
        assert result["message"] == "获取学期详情成功"
    
    def test_get_semester_not_found(self, semester_service: SemesterService):
        """测试获取不存在的学期"""
        with pytest.raises(NotFoundError) as exc_info:
            semester_service.get_semester(99999)
        
        assert exc_info.value.error_code == "SEMESTER_NOT_FOUND"
        assert "学期不存在" in str(exc_info.value)
    
    def test_get_semester_inactive(self, semester_service: SemesterService,
                                 inactive_semester: Semester):
        """测试获取非活跃学期"""
        with pytest.raises(NotFoundError) as exc_info:
            semester_service.get_semester(inactive_semester.id)
        
        assert exc_info.value.error_code == "SEMESTER_NOT_FOUND"
    
    def test_get_semester_exception_handling(self, semester_service: SemesterService):
        """测试获取学期详情异常处理"""
        with patch.object(semester_service.db, 'query') as mock_query:
            mock_query.side_effect = Exception("Database error")
            
            with pytest.raises(BadRequestError) as exc_info:
                semester_service.get_semester(1)
            
            assert "获取学期详情失败" in str(exc_info.value)
    
    # ========== create_semester 测试 ==========
    
    def test_create_semester_success(self, semester_service: SemesterService, admin_user: User):
        """测试创建学期成功"""
        request = CreateSemesterRequest(
            name="新学期2025",
            code="NEW2025",
            start_date=datetime.utcnow() + timedelta(days=60),
            end_date=datetime.utcnow() + timedelta(days=150)
        )
        
        result = semester_service.create_semester(request, admin_user.id)
        
        assert "semester" in result
        assert "message" in result
        assert result["semester"].name == "新学期2025"
        assert result["semester"].code == "NEW2025"
        assert result["semester"].is_active is True
        assert result["message"] == "学期创建成功"
    
    def test_create_semester_duplicate_code(self, semester_service: SemesterService,
                                          sample_semester: Semester, admin_user: User):
        """测试创建重复学期代码"""
        request = CreateSemesterRequest(
            name="重复代码学期",
            code=sample_semester.code,  # 重复代码
            start_date=datetime.utcnow() + timedelta(days=200),
            end_date=datetime.utcnow() + timedelta(days=290)
        )
        
        with pytest.raises(ConflictError) as exc_info:
            semester_service.create_semester(request, admin_user.id)
        
        assert exc_info.value.error_code == "SEMESTER_CODE_EXISTS"
        assert sample_semester.code in str(exc_info.value)
    
    def test_create_semester_code_case_insensitive(self, semester_service: SemesterService,
                                                  sample_semester: Semester, admin_user: User):
        """测试学期代码大小写不敏感"""
        request = CreateSemesterRequest(
            name="大小写测试学期",
            code=sample_semester.code.lower(),  # 小写版本
            start_date=datetime.utcnow() + timedelta(days=200),
            end_date=datetime.utcnow() + timedelta(days=290)
        )
        
        with pytest.raises(ConflictError) as exc_info:
            semester_service.create_semester(request, admin_user.id)
        
        assert exc_info.value.error_code == "SEMESTER_CODE_EXISTS"
    
    def test_create_semester_code_normalization(self, semester_service: SemesterService,
                                              admin_user: User, db_session: Session):
        """测试学期代码标准化（去空格、转大写）"""
        request = CreateSemesterRequest(
            name="代码标准化测试",
            code="  norm2025  ",  # 带空格的小写代码
            start_date=datetime.utcnow() + timedelta(days=60),
            end_date=datetime.utcnow() + timedelta(days=150)
        )
        
        result = semester_service.create_semester(request, admin_user.id)
        
        # 验证代码被标准化为大写且去除空格
        assert result["semester"].code == "NORM2025"
    
    def test_create_semester_name_normalization(self, semester_service: SemesterService,
                                              admin_user: User):
        """测试学期名称标准化（去空格）"""
        request = CreateSemesterRequest(
            name="  名称标准化测试  ",  # 带空格的名称
            code="NAMETEST",
            start_date=datetime.utcnow() + timedelta(days=60),
            end_date=datetime.utcnow() + timedelta(days=150)
        )
        
        result = semester_service.create_semester(request, admin_user.id)
        
        # 验证名称去除了前后空格
        assert result["semester"].name == "名称标准化测试"
    
    def test_create_semester_integrity_error(self, semester_service: SemesterService,
                                           admin_user: User):
        """测试创建学期数据库约束错误"""
        from sqlalchemy.exc import IntegrityError
        
        with patch.object(semester_service.db, 'commit') as mock_commit:
            mock_commit.side_effect = IntegrityError("", "", "")
            
            request = CreateSemesterRequest(
                name="约束错误测试",
                code="CONSTRAINT",
                start_date=datetime.utcnow() + timedelta(days=60),
                end_date=datetime.utcnow() + timedelta(days=150)
            )
            
            with pytest.raises(ConflictError) as exc_info:
                semester_service.create_semester(request, admin_user.id)
            
            assert "学期代码已存在或数据冲突" in str(exc_info.value)
    
    # ========== update_semester 测试 ==========
    
    def test_update_semester_success(self, semester_service: SemesterService,
                                   sample_semester: Semester, admin_user: User):
        """测试更新学期成功"""
        request = UpdateSemesterRequest(
            name="更新后的学期名称",
            start_date=datetime.utcnow() + timedelta(days=40)
        )
        
        result = semester_service.update_semester(sample_semester.id, request, admin_user.id)
        
        assert "semester" in result
        assert "message" in result
        assert result["semester"].name == "更新后的学期名称"
        assert result["message"] == "学期更新成功"
    
    def test_update_semester_not_found(self, semester_service: SemesterService, admin_user: User):
        """测试更新不存在的学期"""
        request = UpdateSemesterRequest(name="不存在的学期")
        
        with pytest.raises(NotFoundError) as exc_info:
            semester_service.update_semester(99999, request, admin_user.id)
        
        assert exc_info.value.error_code == "SEMESTER_NOT_FOUND"
    
    def test_update_semester_duplicate_code(self, semester_service: SemesterService,
                                          db_session: Session, sample_semester: Semester,
                                          admin_user: User):
        """测试更新学期为重复代码"""
        # 创建另一个学期
        another_semester = Semester(
            name="另一个学期",
            code="ANOTHER2024",
            start_date=datetime.utcnow() + timedelta(days=200),
            end_date=datetime.utcnow() + timedelta(days=290),
            is_active=True
        )
        db_session.add(another_semester)
        db_session.commit()
        
        # 尝试更新为重复代码
        request = UpdateSemesterRequest(code=another_semester.code)
        
        with pytest.raises(ConflictError) as exc_info:
            semester_service.update_semester(sample_semester.id, request, admin_user.id)
        
        assert exc_info.value.error_code == "SEMESTER_CODE_EXISTS"
    
    def test_update_semester_same_code_allowed(self, semester_service: SemesterService,
                                             sample_semester: Semester, admin_user: User):
        """测试更新学期为相同代码（应该允许）"""
        request = UpdateSemesterRequest(
            code=sample_semester.code,  # 相同代码
            name="更新但保持代码不变"
        )
        
        # 不应该抛出异常
        result = semester_service.update_semester(sample_semester.id, request, admin_user.id)
        assert result["semester"].code == sample_semester.code
        assert result["semester"].name == "更新但保持代码不变"
    
    def test_update_semester_invalid_date_range(self, semester_service: SemesterService,
                                              sample_semester: Semester, admin_user: User):
        """测试更新学期无效日期范围"""
        request = UpdateSemesterRequest(
            start_date=datetime.utcnow() + timedelta(days=200),
            end_date=datetime.utcnow() + timedelta(days=100)  # 早于开始时间
        )
        
        with pytest.raises(BadRequestError) as exc_info:
            semester_service.update_semester(sample_semester.id, request, admin_user.id)
        
        assert "结束时间必须晚于开始时间" in str(exc_info.value)
    
    def test_update_semester_partial_update(self, semester_service: SemesterService,
                                          sample_semester: Semester, admin_user: User):
        """测试部分更新学期字段"""
        original_code = sample_semester.code
        original_start_date = sample_semester.start_date
        
        request = UpdateSemesterRequest(
            name="仅更新名称"
            # 不更新其他字段
        )
        
        result = semester_service.update_semester(sample_semester.id, request, admin_user.id)
        
        # 验证只有指定字段被更新
        assert result["semester"].name == "仅更新名称"
        assert result["semester"].code == original_code
        assert result["semester"].start_date == original_start_date
    
    # ========== delete_semester 测试 ==========
    
    def test_delete_semester_success(self, semester_service: SemesterService,
                                   sample_semester: Semester, admin_user: User, db_session: Session):
        """测试删除学期成功（软删除）"""
        result = semester_service.delete_semester(sample_semester.id, admin_user.id)
        
        assert "message" in result
        assert "学期删除成功" in result["message"]
        
        # 验证软删除 - 学期仍存在但is_active=False
        db_session.refresh(sample_semester)
        assert sample_semester.is_active is False
    
    def test_delete_semester_not_found(self, semester_service: SemesterService, admin_user: User):
        """测试删除不存在的学期"""
        with pytest.raises(NotFoundError) as exc_info:
            semester_service.delete_semester(99999, admin_user.id)
        
        assert exc_info.value.error_code == "SEMESTER_NOT_FOUND"
    
    def test_delete_semester_with_courses(self, semester_service: SemesterService,
                                        sample_semester: Semester, admin_user: User,
                                        regular_user: User, db_session: Session):
        """测试删除有关联课程的学期"""
        # 创建关联到该学期的课程
        course = Course(
            name="关联课程",
            code="LINKED",
            description="关联到学期的课程",
            semester_id=sample_semester.id,
            user_id=regular_user.id
        )
        db_session.add(course)
        db_session.commit()
        
        with pytest.raises(ConflictError) as exc_info:
            semester_service.delete_semester(sample_semester.id, admin_user.id)
        
        assert exc_info.value.error_code == "SEMESTER_HAS_COURSES"
        assert "门课程关联到此学期" in str(exc_info.value)
        
        # 验证学期仍为活跃状态
        db_session.refresh(sample_semester)
        assert sample_semester.is_active is True
    
    def test_delete_semester_multiple_courses_count(self, semester_service: SemesterService,
                                                  sample_semester: Semester, admin_user: User,
                                                  regular_user: User, db_session: Session):
        """测试删除有多个关联课程的学期"""
        # 创建3个关联课程
        for i in range(3):
            course = Course(
                name=f"关联课程{i+1}",
                code=f"LINK{i+1}",
                semester_id=sample_semester.id,
                user_id=regular_user.id
            )
            db_session.add(course)
        db_session.commit()
        
        with pytest.raises(ConflictError) as exc_info:
            semester_service.delete_semester(sample_semester.id, admin_user.id)
        
        # 验证错误消息包含课程数量
        assert "3 门课程关联到此学期" in str(exc_info.value)
    
    # ========== get_semester_courses 测试 ==========
    
    def test_get_semester_courses_success_empty(self, semester_service: SemesterService,
                                              sample_semester: Semester):
        """测试获取学期课程 - 无课程"""
        result = semester_service.get_semester_courses(sample_semester.id)
        
        assert "courses" in result
        assert "message" in result
        assert result["courses"] == []
        assert f"获取学期 {sample_semester.name} 课程列表成功" in result["message"]
    
    def test_get_semester_courses_success_with_data(self, semester_service: SemesterService,
                                                  sample_semester: Semester, regular_user: User,
                                                  admin_user: User, db_session: Session):
        """测试获取学期课程 - 有课程数据"""
        # 创建多个课程关联到该学期
        courses_data = [
            ("课程1", "COURSE1", regular_user.id),
            ("课程2", "COURSE2", admin_user.id),
            ("课程3", "COURSE3", regular_user.id),
        ]
        
        created_courses = []
        for name, code, user_id in courses_data:
            course = Course(
                name=name,
                code=code,
                description=f"{name}的描述",
                semester_id=sample_semester.id,
                user_id=user_id
            )
            created_courses.append(course)
            db_session.add(course)
        db_session.commit()
        
        result = semester_service.get_semester_courses(sample_semester.id)
        
        assert len(result["courses"]) == 3
        
        # 验证按创建时间倒序排列
        course_names = [c.name for c in result["courses"]]
        assert course_names[0] == "课程3"  # 最后创建的在前
        
        # 验证每个课程都包含学期信息（通过joinedload）
        for course in result["courses"]:
            assert hasattr(course, 'semester')
            assert course.semester.id == sample_semester.id
    
    def test_get_semester_courses_semester_not_found(self, semester_service: SemesterService):
        """测试获取不存在学期的课程"""
        with pytest.raises(NotFoundError) as exc_info:
            semester_service.get_semester_courses(99999)
        
        assert exc_info.value.error_code == "SEMESTER_NOT_FOUND"
    
    def test_get_semester_courses_inactive_semester(self, semester_service: SemesterService,
                                                  inactive_semester: Semester):
        """测试获取非活跃学期的课程"""
        with pytest.raises(NotFoundError) as exc_info:
            semester_service.get_semester_courses(inactive_semester.id)
        
        assert exc_info.value.error_code == "SEMESTER_NOT_FOUND"


class TestCourseService:
    """课程服务类测试"""
    
    @pytest.fixture
    def course_service(self, db_session: Session) -> CourseService:
        """创建CourseService实例"""
        return CourseService(db_session)
    
    @pytest.fixture
    def sample_semester(self, db_session: Session) -> Semester:
        """创建测试学期"""
        semester = Semester(
            name="课程测试学期",
            code="COURSETEST",
            start_date=datetime.utcnow() + timedelta(days=10),
            end_date=datetime.utcnow() + timedelta(days=100),
            is_active=True
        )
        db_session.add(semester)
        db_session.commit()
        db_session.refresh(semester)
        return semester
    
    @pytest.fixture
    def sample_course(self, db_session: Session, sample_semester: Semester, regular_user: User) -> Course:
        """创建测试课程"""
        course = Course(
            name="测试课程",
            code="TEST101",
            description="这是一个测试课程",
            semester_id=sample_semester.id,
            user_id=regular_user.id
        )
        db_session.add(course)
        db_session.commit()
        db_session.refresh(course)
        return course
    
    # ========== get_courses 测试 ==========
    
    def test_get_courses_success_empty(self, course_service: CourseService, regular_user: User):
        """测试获取空课程列表"""
        result = course_service.get_courses(regular_user.id)
        
        assert "courses" in result
        assert "message" in result
        assert result["courses"] == []
        assert result["message"] == "获取课程列表成功"
    
    def test_get_courses_success_with_data(self, course_service: CourseService,
                                         db_session: Session, sample_semester: Semester,
                                         regular_user: User, admin_user: User):
        """测试获取用户课程列表"""
        # 创建regular_user的课程
        user_courses = []
        for i in range(2):
            course = Course(
                name=f"用户课程{i+1}",
                code=f"USER{i+1}",
                description=f"用户的课程{i+1}",
                semester_id=sample_semester.id,
                user_id=regular_user.id
            )
            user_courses.append(course)
            db_session.add(course)
        
        # 创建其他用户的课程（不应该返回）
        other_course = Course(
            name="其他用户课程",
            code="OTHER",
            description="不应该出现在结果中",
            semester_id=sample_semester.id,
            user_id=admin_user.id
        )
        db_session.add(other_course)
        db_session.commit()
        
        result = course_service.get_courses(regular_user.id)
        
        # 只返回当前用户的课程
        assert len(result["courses"]) == 2
        for course in result["courses"]:
            assert course.user_id == regular_user.id
            assert course.code in ["USER1", "USER2"]
        
        # 验证按创建时间倒序排列
        created_ats = [c.created_at for c in result["courses"]]
        assert created_ats[0] >= created_ats[1]
        
        # 验证课程包含学期信息（通过joinedload）
        for course in result["courses"]:
            assert hasattr(course, 'semester')
            assert course.semester.id == sample_semester.id
    
    def test_get_courses_filter_by_semester(self, course_service: CourseService,
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
        result = course_service.get_courses(regular_user.id, semester1.id)
        
        assert len(result["courses"]) == 1
        assert result["courses"][0].name == "课程1"
        assert result["courses"][0].semester_id == semester1.id
    
    def test_get_courses_filter_nonexistent_semester(self, course_service: CourseService,
                                                   regular_user: User):
        """测试按不存在的学期过滤"""
        result = course_service.get_courses(regular_user.id, 99999)
        
        # 应该返回空列表，不抛出异常
        assert result["courses"] == []
    
    def test_get_courses_exception_handling(self, course_service: CourseService, regular_user: User):
        """测试获取课程列表异常处理"""
        with patch.object(course_service.db, 'query') as mock_query:
            mock_query.side_effect = Exception("Database error")
            
            with pytest.raises(BadRequestError) as exc_info:
                course_service.get_courses(regular_user.id)
            
            assert "获取课程列表失败" in str(exc_info.value)
    
    # ========== get_course 测试 ==========
    
    def test_get_course_success(self, course_service: CourseService,
                              sample_course: Course, regular_user: User):
        """测试获取课程详情成功"""
        result = course_service.get_course(sample_course.id, regular_user.id)
        
        assert "course" in result
        assert "message" in result
        assert result["course"].id == sample_course.id
        assert result["course"].name == sample_course.name
        assert result["course"].code == sample_course.code
        assert result["message"] == "获取课程详情成功"
        
        # 验证包含学期信息
        assert hasattr(result["course"], 'semester')
    
    def test_get_course_not_found(self, course_service: CourseService, regular_user: User):
        """测试获取不存在的课程"""
        with pytest.raises(NotFoundError) as exc_info:
            course_service.get_course(99999, regular_user.id)
        
        assert exc_info.value.error_code == "COURSE_NOT_FOUND"
        assert "课程不存在" in str(exc_info.value)
    
    def test_get_course_access_denied(self, course_service: CourseService,
                                    db_session: Session, sample_semester: Semester,
                                    regular_user: User, admin_user: User):
        """测试访问其他用户的课程"""
        # 创建属于admin_user的课程
        other_course = Course(
            name="其他用户课程",
            code="OTHER",
            description="属于其他用户",
            semester_id=sample_semester.id,
            user_id=admin_user.id
        )
        db_session.add(other_course)
        db_session.commit()
        db_session.refresh(other_course)
        
        with pytest.raises(ForbiddenError) as exc_info:
            course_service.get_course(other_course.id, regular_user.id)
        
        assert exc_info.value.error_code == "COURSE_ACCESS_DENIED"
        assert "无权访问此课程" in str(exc_info.value)
    
    # ========== create_course 测试 ==========
    
    def test_create_course_success(self, course_service: CourseService,
                                 sample_semester: Semester, regular_user: User):
        """测试创建课程成功"""
        request = CreateCourseRequest(
            name="新课程",
            code="NEW101",
            description="新创建的课程",
            semester_id=sample_semester.id
        )
        
        result = course_service.create_course(request, regular_user.id)
        
        assert "course" in result
        assert "message" in result
        assert result["course"].name == "新课程"
        assert result["course"].code == "NEW101"
        assert result["course"].user_id == regular_user.id
        assert result["course"].semester_id == sample_semester.id
        assert result["message"] == "课程创建成功"
    
    def test_create_course_semester_not_found(self, course_service: CourseService, regular_user: User):
        """测试在不存在的学期创建课程"""
        request = CreateCourseRequest(
            name="无效学期课程",
            code="INVALID",
            description="试图在不存在的学期创建",
            semester_id=99999
        )
        
        with pytest.raises(BadRequestError) as exc_info:
            course_service.create_course(request, regular_user.id)
        
        assert exc_info.value.error_code == "SEMESTER_NOT_FOUND"
        assert "学期不存在或已停用" in str(exc_info.value)
    
    def test_create_course_inactive_semester(self, course_service: CourseService,
                                           db_session: Session, regular_user: User):
        """测试在停用学期创建课程"""
        inactive_semester = Semester(
            name="停用学期",
            code="INACTIVE",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=90),
            is_active=False
        )
        db_session.add(inactive_semester)
        db_session.commit()
        
        request = CreateCourseRequest(
            name="停用学期课程",
            code="INACTIVE",
            description="试图在停用学期创建",
            semester_id=inactive_semester.id
        )
        
        with pytest.raises(BadRequestError) as exc_info:
            course_service.create_course(request, regular_user.id)
        
        assert exc_info.value.error_code == "SEMESTER_NOT_FOUND"
    
    def test_create_course_duplicate_code_same_user_semester(self, course_service: CourseService,
                                                           sample_course: Course, regular_user: User):
        """测试同一用户在同一学期创建重复课程代码"""
        request = CreateCourseRequest(
            name="重复代码课程",
            code=sample_course.code,  # 重复代码
            description="试图创建重复代码",
            semester_id=sample_course.semester_id  # 相同学期
        )
        
        with pytest.raises(ConflictError) as exc_info:
            course_service.create_course(request, regular_user.id)
        
        assert exc_info.value.error_code == "COURSE_CODE_EXISTS"
        assert sample_course.code in str(exc_info.value)
        assert "在此学期内已存在" in str(exc_info.value)
    
    def test_create_course_same_code_different_user_allowed(self, course_service: CourseService,
                                                          sample_course: Course, admin_user: User):
        """测试不同用户在同一学期可以使用相同课程代码"""
        request = CreateCourseRequest(
            name="相同代码不同用户",
            code=sample_course.code,  # 相同代码
            description="不同用户使用相同代码",
            semester_id=sample_course.semester_id  # 相同学期
        )
        
        # 应该成功，因为是不同用户
        result = course_service.create_course(request, admin_user.id)
        assert result["course"].code == sample_course.code
        assert result["course"].user_id == admin_user.id
    
    def test_create_course_same_code_different_semester_allowed(self, course_service: CourseService,
                                                              db_session: Session, sample_course: Course,
                                                              regular_user: User):
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
        
        request = CreateCourseRequest(
            name="相同代码不同学期",
            code=sample_course.code,  # 相同代码
            description="在不同学期使用相同代码",
            semester_id=another_semester.id  # 不同学期
        )
        
        # 应该成功
        result = course_service.create_course(request, regular_user.id)
        assert result["course"].code == sample_course.code
        assert result["course"].semester_id == another_semester.id
    
    def test_create_course_field_normalization(self, course_service: CourseService,
                                             sample_semester: Semester, regular_user: User):
        """测试课程字段标准化（去空格）"""
        request = CreateCourseRequest(
            name="  课程名称标准化  ",  # 带空格
            code="  CODE101  ",  # 带空格
            description="字段标准化测试",
            semester_id=sample_semester.id
        )
        
        result = course_service.create_course(request, regular_user.id)
        
        # 验证字段去除了前后空格
        assert result["course"].name == "课程名称标准化"
        assert result["course"].code == "CODE101"
    
    # ========== update_course 测试 ==========
    
    def test_update_course_success(self, course_service: CourseService,
                                 sample_course: Course, regular_user: User):
        """测试更新课程成功"""
        request = UpdateCourseRequest(
            name="更新后的课程名称",
            description="更新后的描述"
        )
        
        result = course_service.update_course(sample_course.id, request, regular_user.id)
        
        assert "course" in result
        assert "message" in result
        assert result["course"].name == "更新后的课程名称"
        assert result["course"].description == "更新后的描述"
        assert result["message"] == "课程更新成功"
    
    def test_update_course_not_found(self, course_service: CourseService, regular_user: User):
        """测试更新不存在的课程"""
        request = UpdateCourseRequest(name="不存在的课程")
        
        with pytest.raises(NotFoundError) as exc_info:
            course_service.update_course(99999, request, regular_user.id)
        
        assert exc_info.value.error_code == "COURSE_NOT_FOUND"
    
    def test_update_course_access_denied(self, course_service: CourseService,
                                       db_session: Session, sample_semester: Semester,
                                       regular_user: User, admin_user: User):
        """测试更新其他用户的课程"""
        other_course = Course(
            name="其他用户课程",
            code="OTHER",
            description="属于其他用户",
            semester_id=sample_semester.id,
            user_id=admin_user.id
        )
        db_session.add(other_course)
        db_session.commit()
        db_session.refresh(other_course)
        
        request = UpdateCourseRequest(name="无权更新")
        
        with pytest.raises(ForbiddenError) as exc_info:
            course_service.update_course(other_course.id, request, regular_user.id)
        
        assert exc_info.value.error_code == "COURSE_UPDATE_DENIED"
        assert "无权修改此课程" in str(exc_info.value)
    
    def test_update_course_duplicate_code(self, course_service: CourseService,
                                        db_session: Session, sample_course: Course,
                                        sample_semester: Semester, regular_user: User):
        """测试更新课程为重复代码"""
        # 创建另一个课程
        another_course = Course(
            name="另一个课程",
            code="ANOTHER",
            description="另一个测试课程",
            semester_id=sample_semester.id,
            user_id=regular_user.id
        )
        db_session.add(another_course)
        db_session.commit()
        
        # 尝试更新为重复代码
        request = UpdateCourseRequest(code=another_course.code)
        
        with pytest.raises(ConflictError) as exc_info:
            course_service.update_course(sample_course.id, request, regular_user.id)
        
        assert exc_info.value.error_code == "COURSE_CODE_EXISTS"
    
    def test_update_course_same_code_allowed(self, course_service: CourseService,
                                           sample_course: Course, regular_user: User):
        """测试更新课程为相同代码（应该允许）"""
        request = UpdateCourseRequest(
            code=sample_course.code,  # 相同代码
            name="更新但保持代码不变"
        )
        
        # 不应该抛出异常
        result = course_service.update_course(sample_course.id, request, regular_user.id)
        assert result["course"].code == sample_course.code
        assert result["course"].name == "更新但保持代码不变"
    
    def test_update_course_partial_update(self, course_service: CourseService,
                                        sample_course: Course, regular_user: User):
        """测试部分更新课程字段"""
        original_code = sample_course.code
        original_description = sample_course.description
        
        request = UpdateCourseRequest(
            name="仅更新名称"
            # 不更新其他字段
        )
        
        result = course_service.update_course(sample_course.id, request, regular_user.id)
        
        # 验证只有指定字段被更新
        assert result["course"].name == "仅更新名称"
        assert result["course"].code == original_code
        assert result["course"].description == original_description
    
    # ========== delete_course 测试 ==========
    
    def test_delete_course_success(self, course_service: CourseService,
                                 sample_course: Course, regular_user: User, db_session: Session):
        """测试删除课程成功"""
        course_id = sample_course.id
        
        result = course_service.delete_course(course_id, regular_user.id)
        
        assert "message" in result
        assert "课程删除成功" in result["message"]
        
        # 验证物理删除 - 课程不再存在
        deleted_course = db_session.query(Course).filter(Course.id == course_id).first()
        assert deleted_course is None
    
    def test_delete_course_not_found(self, course_service: CourseService, regular_user: User):
        """测试删除不存在的课程"""
        with pytest.raises(NotFoundError) as exc_info:
            course_service.delete_course(99999, regular_user.id)
        
        assert exc_info.value.error_code == "COURSE_NOT_FOUND"
    
    def test_delete_course_access_denied(self, course_service: CourseService,
                                       db_session: Session, sample_semester: Semester,
                                       regular_user: User, admin_user: User):
        """测试删除其他用户的课程"""
        other_course = Course(
            name="其他用户课程",
            code="DELETEOTHER",
            description="无权删除",
            semester_id=sample_semester.id,
            user_id=admin_user.id
        )
        db_session.add(other_course)
        db_session.commit()
        db_session.refresh(other_course)
        
        with pytest.raises(ForbiddenError) as exc_info:
            course_service.delete_course(other_course.id, regular_user.id)
        
        assert exc_info.value.error_code == "COURSE_DELETE_DENIED"
        assert "无权删除此课程" in str(exc_info.value)


class TestServiceExceptionCoverage:
    """异常覆盖测试 - 确保所有声明的异常都有对应测试"""
    
    def test_semester_service_method_exceptions_coverage(self):
        """验证SemesterService METHOD_EXCEPTIONS声明的完整性"""
        expected_methods = {
            'get_semesters', 'get_semester', 'create_semester',
            'update_semester', 'delete_semester', 'get_semester_courses'
        }
        
        actual_methods = set(SemesterService.METHOD_EXCEPTIONS.keys())
        assert actual_methods == expected_methods
    
    def test_course_service_method_exceptions_coverage(self):
        """验证CourseService METHOD_EXCEPTIONS声明的完整性"""
        expected_methods = {
            'get_courses', 'get_course', 'create_course',
            'update_course', 'delete_course'
        }
        
        actual_methods = set(CourseService.METHOD_EXCEPTIONS.keys())
        assert actual_methods == expected_methods
    
    def test_semester_service_exception_types(self):
        """验证SemesterService各方法的异常类型声明"""
        # get_semesters - 无异常
        assert len(SemesterService.METHOD_EXCEPTIONS['get_semesters']) == 0
        
        # get_semester - NotFoundError
        exceptions = SemesterService.METHOD_EXCEPTIONS['get_semester']
        assert NotFoundError in exceptions
        assert len(exceptions) == 1
        
        # create_semester - BadRequestError, ConflictError
        exceptions = SemesterService.METHOD_EXCEPTIONS['create_semester']
        assert BadRequestError in exceptions
        assert ConflictError in exceptions
        assert len(exceptions) == 2
        
        # update_semester - NotFoundError, BadRequestError, ConflictError
        exceptions = SemesterService.METHOD_EXCEPTIONS['update_semester']
        assert NotFoundError in exceptions
        assert BadRequestError in exceptions
        assert ConflictError in exceptions
        assert len(exceptions) == 3
        
        # delete_semester - NotFoundError, ConflictError
        exceptions = SemesterService.METHOD_EXCEPTIONS['delete_semester']
        assert NotFoundError in exceptions
        assert ConflictError in exceptions
        assert len(exceptions) == 2
        
        # get_semester_courses - NotFoundError
        exceptions = SemesterService.METHOD_EXCEPTIONS['get_semester_courses']
        assert NotFoundError in exceptions
        assert len(exceptions) == 1
    
    def test_course_service_exception_types(self):
        """验证CourseService各方法的异常类型声明"""
        # get_courses - 无异常
        assert len(CourseService.METHOD_EXCEPTIONS['get_courses']) == 0
        
        # get_course - NotFoundError, ForbiddenError
        exceptions = CourseService.METHOD_EXCEPTIONS['get_course']
        assert NotFoundError in exceptions
        assert ForbiddenError in exceptions
        assert len(exceptions) == 2
        
        # create_course - BadRequestError, ConflictError
        exceptions = CourseService.METHOD_EXCEPTIONS['create_course']
        assert BadRequestError in exceptions
        assert ConflictError in exceptions
        assert len(exceptions) == 2
        
        # update_course - NotFoundError, ForbiddenError, BadRequestError, ConflictError
        exceptions = CourseService.METHOD_EXCEPTIONS['update_course']
        assert NotFoundError in exceptions
        assert ForbiddenError in exceptions
        assert BadRequestError in exceptions
        assert ConflictError in exceptions
        assert len(exceptions) == 4
        
        # delete_course - NotFoundError, ForbiddenError
        exceptions = CourseService.METHOD_EXCEPTIONS['delete_course']
        assert NotFoundError in exceptions
        assert ForbiddenError in exceptions
        assert len(exceptions) == 2


class TestServiceIntegration:
    """Service层集成测试 - 测试跨Service的交互"""
    
    @pytest.fixture
    def semester_service(self, db_session: Session) -> SemesterService:
        return SemesterService(db_session)
    
    @pytest.fixture
    def course_service(self, db_session: Session) -> CourseService:
        return CourseService(db_session)
    
    def test_semester_course_lifecycle(self, semester_service: SemesterService,
                                     course_service: CourseService, admin_user: User,
                                     regular_user: User, db_session: Session):
        """测试学期-课程完整生命周期"""
        # 1. 创建学期
        semester_request = CreateSemesterRequest(
            name="生命周期测试学期",
            code="LIFECYCLE",
            start_date=datetime.utcnow() + timedelta(days=30),
            end_date=datetime.utcnow() + timedelta(days=120)
        )
        
        semester_result = semester_service.create_semester(semester_request, admin_user.id)
        semester_id = semester_result["semester"].id
        
        # 2. 在学期下创建课程
        course_request = CreateCourseRequest(
            name="生命周期测试课程",
            code="LIFECYCLE101",
            description="用于测试生命周期",
            semester_id=semester_id
        )
        
        course_result = course_service.create_course(course_request, regular_user.id)
        course_id = course_result["course"].id
        
        # 3. 验证学期课程关联
        semester_courses = semester_service.get_semester_courses(semester_id)
        assert len(semester_courses["courses"]) == 1
        assert semester_courses["courses"][0].id == course_id
        
        # 4. 验证有课程的学期无法删除
        with pytest.raises(ConflictError):
            semester_service.delete_semester(semester_id, admin_user.id)
        
        # 5. 删除课程后可以删除学期
        course_service.delete_course(course_id, regular_user.id)
        
        # 验证课程已删除
        with pytest.raises(NotFoundError):
            course_service.get_course(course_id, regular_user.id)
        
        # 现在可以删除学期
        semester_service.delete_semester(semester_id, admin_user.id)
        
        # 验证学期已软删除
        with pytest.raises(NotFoundError):
            semester_service.get_semester(semester_id)
    
    def test_cross_user_isolation(self, course_service: CourseService,
                                 db_session: Session, admin_user: User, regular_user: User):
        """测试跨用户数据隔离"""
        # 创建学期
        semester = Semester(
            name="隔离测试学期",
            code="ISOLATION",
            start_date=datetime.utcnow() + timedelta(days=10),
            end_date=datetime.utcnow() + timedelta(days=100),
            is_active=True
        )
        db_session.add(semester)
        db_session.commit()
        
        # 不同用户创建同名课程
        course_request = CreateCourseRequest(
            name="相同名称课程",
            code="SAMENAME",
            description="测试用户隔离",
            semester_id=semester.id
        )
        
        admin_course = course_service.create_course(course_request, admin_user.id)
        user_course = course_service.create_course(course_request, regular_user.id)
        
        # 验证两个课程都创建成功但属于不同用户
        assert admin_course["course"].user_id == admin_user.id
        assert user_course["course"].user_id == regular_user.id
        assert admin_course["course"].id != user_course["course"].id
        
        # 验证用户只能看到自己的课程
        admin_courses = course_service.get_courses(admin_user.id)
        user_courses = course_service.get_courses(regular_user.id)
        
        assert len(admin_courses["courses"]) == 1
        assert len(user_courses["courses"]) == 1
        assert admin_courses["courses"][0].user_id == admin_user.id
        assert user_courses["courses"][0].user_id == regular_user.id
        
        # 验证用户无法访问其他用户的课程
        with pytest.raises(ForbiddenError):
            course_service.get_course(admin_course["course"].id, regular_user.id)
        
        with pytest.raises(ForbiddenError):
            course_service.get_course(user_course["course"].id, admin_user.id)
    
    def test_semester_deactivation_impact(self, semester_service: SemesterService,
                                        course_service: CourseService, admin_user: User,
                                        regular_user: User, db_session: Session):
        """测试学期停用对课程访问的影响"""
        # 创建学期和课程
        semester_request = CreateSemesterRequest(
            name="停用影响测试学期",
            code="DEACTIVATE",
            start_date=datetime.utcnow() + timedelta(days=30),
            end_date=datetime.utcnow() + timedelta(days=120)
        )
        
        semester_result = semester_service.create_semester(semester_request, admin_user.id)
        semester_id = semester_result["semester"].id
        
        course_request = CreateCourseRequest(
            name="受影响课程",
            code="AFFECTED",
            semester_id=semester_id
        )
        
        course_result = course_service.create_course(course_request, regular_user.id)
        course_id = course_result["course"].id
        
        # 停用学期（通过直接修改数据库，模拟管理员操作）
        semester = db_session.query(Semester).filter(Semester.id == semester_id).first()
        semester.is_active = False
        db_session.commit()
        
        # 验证已存在的课程仍可访问（课程不依赖学期活跃状态）
        course_detail = course_service.get_course(course_id, regular_user.id)
        assert course_detail["course"].id == course_id
        
        # 但无法在停用学期创建新课程
        new_course_request = CreateCourseRequest(
            name="新课程",
            code="NEWCOURSE",
            semester_id=semester_id
        )
        
        with pytest.raises(BadRequestError):
            course_service.create_course(new_course_request, regular_user.id)