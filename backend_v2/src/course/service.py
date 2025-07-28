"""Course模块业务逻辑服务"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, func
from typing import Optional, Dict, Any, List
from datetime import datetime

# 导入日志
from src.shared.logging import get_logger

# 导入模型
from .models import Semester, Course

# 导入请求模型
from .schemas import (
    CreateSemesterRequest, UpdateSemesterRequest,
    CreateCourseRequest, UpdateCourseRequest
)

# 导入异常
from src.shared.exceptions import (
    BadRequestError, NotFoundError, ConflictError, ForbiddenError
)


class SemesterService:
    """学期服务类"""
    
    # 声明每个方法可能抛出的异常
    METHOD_EXCEPTIONS = {
        'get_semesters': set(),
        'get_semester': {NotFoundError},
        'create_semester': {BadRequestError, ConflictError},
        'update_semester': {NotFoundError, BadRequestError, ConflictError},
        'delete_semester': {NotFoundError, ConflictError},
        'get_semester_courses': {NotFoundError}
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger(__name__)
    
    def get_semesters(self) -> Dict[str, Any]:
        """获取所有活跃学期列表"""
        try:
            semesters = (
                self.db.query(Semester)
                .filter(Semester.is_active == True)
                .order_by(Semester.start_date.desc())
                .all()
            )
            
            return {
                "semesters": semesters,
                "message": "获取学期列表成功"
            }
        except Exception as e:
            self.logger.error(f"获取学期列表失败: {e}")
            raise BadRequestError("获取学期列表失败")
    
    def get_semester(self, semester_id: int) -> Dict[str, Any]:
        """获取学期详情"""
        try:
            semester = (
                self.db.query(Semester)
                .filter(Semester.id == semester_id, Semester.is_active == True)
                .first()
            )
            
            if not semester:
                raise NotFoundError("学期不存在", error_code="SEMESTER_NOT_FOUND")
            
            return {
                "semester": semester,
                "message": "获取学期详情成功"
            }
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"获取学期详情失败: {e}")
            raise BadRequestError("获取学期详情失败")
    
    def create_semester(self, request: CreateSemesterRequest, admin_id: int) -> Dict[str, Any]:
        """创建学期（管理员专用）"""
        try:
            # 检查学期代码唯一性
            existing = (
                self.db.query(Semester)
                .filter(Semester.code == request.code.strip().upper())
                .first()
            )
            if existing:
                raise ConflictError(f"学期代码 '{request.code}' 已存在", error_code="SEMESTER_CODE_EXISTS")
            
            # 创建学期
            semester = Semester(
                name=request.name.strip(),
                code=request.code.strip().upper(),
                start_date=request.start_date,
                end_date=request.end_date
            )
            
            self.db.add(semester)
            self.db.commit()
            self.db.refresh(semester)
            
            self.logger.info(f"管理员 {admin_id} 创建学期: {semester.code}")
            
            return {
                "semester": semester,
                "message": "学期创建成功"
            }
            
        except (ConflictError, BadRequestError):
            self.db.rollback()
            raise
        except IntegrityError as e:
            self.db.rollback()
            self.logger.error(f"学期创建数据库约束错误: {e}")
            raise ConflictError("学期代码已存在或数据冲突")
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"创建学期失败: {e}")
            raise BadRequestError("创建学期失败")
    
    def update_semester(self, semester_id: int, request: UpdateSemesterRequest, admin_id: int) -> Dict[str, Any]:
        """更新学期（管理员专用）"""
        try:
            # 查找学期
            semester = (
                self.db.query(Semester)
                .filter(Semester.id == semester_id, Semester.is_active == True)
                .first()
            )
            if not semester:
                raise NotFoundError("学期不存在", error_code="SEMESTER_NOT_FOUND")
            
            # 检查代码唯一性（如果要更新代码）
            if request.code and request.code.strip().upper() != semester.code:
                existing = (
                    self.db.query(Semester)
                    .filter(
                        Semester.code == request.code.strip().upper(),
                        Semester.id != semester_id
                    )
                    .first()
                )
                if existing:
                    raise ConflictError(f"学期代码 '{request.code}' 已存在", error_code="SEMESTER_CODE_EXISTS")
            
            # 更新字段
            update_data = request.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if field == 'code' and value:
                    setattr(semester, field, value.strip().upper())
                elif field == 'name' and value:
                    setattr(semester, field, value.strip())
                else:
                    setattr(semester, field, value)
            
            # 验证日期逻辑
            if semester.end_date <= semester.start_date:
                raise BadRequestError("结束时间必须晚于开始时间")
            
            self.db.commit()
            self.db.refresh(semester)
            
            self.logger.info(f"管理员 {admin_id} 更新学期: {semester.code}")
            
            return {
                "semester": semester,
                "message": "学期更新成功"
            }
            
        except (NotFoundError, ConflictError, BadRequestError):
            self.db.rollback()
            raise
        except IntegrityError as e:
            self.db.rollback()
            self.logger.error(f"学期更新数据库约束错误: {e}")
            raise ConflictError("学期代码已存在或数据冲突")
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"更新学期失败: {e}")
            raise BadRequestError("更新学期失败")
    
    def delete_semester(self, semester_id: int, admin_id: int) -> Dict[str, Any]:
        """删除学期（软删除，管理员专用）"""
        try:
            # 查找学期
            semester = (
                self.db.query(Semester)
                .filter(Semester.id == semester_id, Semester.is_active == True)
                .first()
            )
            if not semester:
                raise NotFoundError("学期不存在", error_code="SEMESTER_NOT_FOUND")
            
            # 检查是否有关联的课程
            course_count = (
                self.db.query(Course)
                .filter(Course.semester_id == semester_id)
                .count()
            )
            if course_count > 0:
                raise ConflictError(
                    f"无法删除学期，有 {course_count} 门课程关联到此学期",
                    error_code="SEMESTER_HAS_COURSES"
                )
            
            # 软删除
            semester.is_active = False
            self.db.commit()
            
            self.logger.info(f"管理员 {admin_id} 删除学期: {semester.code}")
            
            return {
                "message": "学期删除成功"
            }
            
        except (NotFoundError, ConflictError):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"删除学期失败: {e}")
            raise BadRequestError("删除学期失败")
    
    def get_semester_courses(self, semester_id: int) -> Dict[str, Any]:
        """获取学期下的所有课程"""
        try:
            # 验证学期存在
            semester = (
                self.db.query(Semester)
                .filter(Semester.id == semester_id, Semester.is_active == True)
                .first()
            )
            if not semester:
                raise NotFoundError("学期不存在", error_code="SEMESTER_NOT_FOUND")
            
            # 获取课程列表
            courses = (
                self.db.query(Course)
                .options(joinedload(Course.semester))
                .filter(Course.semester_id == semester_id)
                .order_by(Course.created_at.desc())
                .all()
            )
            
            return {
                "courses": courses,
                "message": f"获取学期 {semester.name} 课程列表成功"
            }
            
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"获取学期课程失败: {e}")
            raise BadRequestError("获取学期课程失败")


class CourseService:
    """课程服务类"""
    
    # 声明每个方法可能抛出的异常
    METHOD_EXCEPTIONS = {
        'get_courses': set(),
        'get_course': {NotFoundError, ForbiddenError},
        'create_course': {BadRequestError, ConflictError},
        'update_course': {NotFoundError, ForbiddenError, BadRequestError, ConflictError},
        'delete_course': {NotFoundError, ForbiddenError}
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger(__name__)
    
    def get_courses(self, user_id: int, semester_id: Optional[int] = None) -> Dict[str, Any]:
        """获取用户的课程列表"""
        try:
            query = (
                self.db.query(Course)
                .options(joinedload(Course.semester))
                .filter(Course.user_id == user_id)
            )
            
            if semester_id:
                query = query.filter(Course.semester_id == semester_id)
            
            courses = query.order_by(Course.created_at.desc()).all()
            
            return {
                "courses": courses,
                "message": "获取课程列表成功"
            }
            
        except Exception as e:
            self.logger.error(f"获取课程列表失败: {e}")
            raise BadRequestError("获取课程列表失败")
    
    def get_course(self, course_id: int, user_id: int) -> Dict[str, Any]:
        """获取课程详情（权限检查）"""
        try:
            course = (
                self.db.query(Course)
                .options(joinedload(Course.semester))
                .filter(Course.id == course_id)
                .first()
            )
            
            if not course:
                raise NotFoundError("课程不存在", error_code="COURSE_NOT_FOUND")
            
            # 权限检查
            if course.user_id != user_id:
                raise ForbiddenError("无权访问此课程", error_code="COURSE_ACCESS_DENIED")
            
            return {
                "course": course,
                "message": "获取课程详情成功"
            }
            
        except (NotFoundError, ForbiddenError):
            raise
        except Exception as e:
            self.logger.error(f"获取课程详情失败: {e}")
            raise BadRequestError("获取课程详情失败")
    
    def create_course(self, request: CreateCourseRequest, user_id: int) -> Dict[str, Any]:
        """创建课程"""
        try:
            # 验证学期存在且活跃
            semester = (
                self.db.query(Semester)
                .filter(Semester.id == request.semester_id, Semester.is_active == True)
                .first()
            )
            if not semester:
                raise BadRequestError("学期不存在或已停用", error_code="SEMESTER_NOT_FOUND")
            
            # 检查同一用户在同一学期内课程代码唯一性
            existing = (
                self.db.query(Course)
                .filter(
                    Course.code == request.code.strip(),
                    Course.semester_id == request.semester_id,
                    Course.user_id == user_id
                )
                .first()
            )
            if existing:
                raise ConflictError(
                    f"课程代码 '{request.code}' 在此学期内已存在",
                    error_code="COURSE_CODE_EXISTS"
                )
            
            # 创建课程
            course = Course(
                name=request.name.strip(),
                code=request.code.strip(),
                description=request.description,
                semester_id=request.semester_id,
                user_id=user_id
            )
            
            self.db.add(course)
            self.db.commit()
            self.db.refresh(course)
            
            self.logger.info(f"用户 {user_id} 创建课程: {course.code}")
            
            return {
                "course": course,
                "message": "课程创建成功"
            }
            
        except (BadRequestError, ConflictError):
            self.db.rollback()
            raise
        except IntegrityError as e:
            self.db.rollback()
            self.logger.error(f"课程创建数据库约束错误: {e}")
            raise ConflictError("课程代码已存在或数据冲突")
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"创建课程失败: {e}")
            raise BadRequestError("创建课程失败")
    
    def update_course(self, course_id: int, request: UpdateCourseRequest, user_id: int) -> Dict[str, Any]:
        """更新课程"""
        try:
            # 查找课程
            course = (
                self.db.query(Course)
                .options(joinedload(Course.semester))
                .filter(Course.id == course_id)
                .first()
            )
            
            if not course:
                raise NotFoundError("课程不存在", error_code="COURSE_NOT_FOUND")
            
            # 权限检查
            if course.user_id != user_id:
                raise ForbiddenError("无权修改此课程", error_code="COURSE_UPDATE_DENIED")
            
            # 检查代码唯一性（如果要更新代码）
            if request.code and request.code.strip() != course.code:
                existing = (
                    self.db.query(Course)
                    .filter(
                        Course.code == request.code.strip(),
                        Course.semester_id == course.semester_id,
                        Course.user_id == user_id,
                        Course.id != course_id
                    )
                    .first()
                )
                if existing:
                    raise ConflictError(
                        f"课程代码 '{request.code}' 在此学期内已存在",
                        error_code="COURSE_CODE_EXISTS"
                    )
            
            # 更新字段
            update_data = request.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if field in ['name', 'code'] and value:
                    setattr(course, field, value.strip())
                else:
                    setattr(course, field, value)
            
            self.db.commit()
            self.db.refresh(course)
            
            self.logger.info(f"用户 {user_id} 更新课程: {course.code}")
            
            return {
                "course": course,
                "message": "课程更新成功"
            }
            
        except (NotFoundError, ForbiddenError, ConflictError):
            self.db.rollback()
            raise
        except IntegrityError as e:
            self.db.rollback()
            self.logger.error(f"课程更新数据库约束错误: {e}")
            raise ConflictError("课程代码已存在或数据冲突")
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"更新课程失败: {e}")
            raise BadRequestError("更新课程失败")
    
    def delete_course(self, course_id: int, user_id: int) -> Dict[str, Any]:
        """删除课程"""
        try:
            # 查找课程
            course = (
                self.db.query(Course)
                .filter(Course.id == course_id)
                .first()
            )
            
            if not course:
                raise NotFoundError("课程不存在", error_code="COURSE_NOT_FOUND")
            
            # 权限检查
            if course.user_id != user_id:
                raise ForbiddenError("无权删除此课程", error_code="COURSE_DELETE_DENIED")
            
            # 物理删除（当文件/聊天模块实现后，需要检查关联数据）
            self.db.delete(course)
            self.db.commit()
            
            self.logger.info(f"用户 {user_id} 删除课程: {course.code}")
            
            return {
                "message": "课程删除成功"
            }
            
        except (NotFoundError, ForbiddenError):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"删除课程失败: {e}")
            raise BadRequestError("删除课程失败")