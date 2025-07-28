"""Course模块路由定义"""
from fastapi import APIRouter, Query
from typing import Optional

from .service import SemesterService, CourseService
from .schemas import (
    # 请求模型
    CreateSemesterRequest, UpdateSemesterRequest,
    CreateCourseRequest, UpdateCourseRequest,
    # 响应模型
    SemesterListResponse, CreateSemesterResponse, GetSemesterResponse, UpdateSemesterResponse,
    SemesterCoursesResponse, CourseListResponse, CreateCourseResponse, GetCourseResponse, UpdateCourseResponse,
    DeleteSemesterResponse, DeleteCourseResponse,
    # 数据模型
    SemesterData, CourseData
)

# 导入依赖
from src.shared.dependencies import DbDep, UserDep, AdminUserDep

# 导入装饰器
from src.shared.api_decorator import create_service_route_config, service_api_handler

# 创建路由器
router = APIRouter(prefix="/api/v1")


# ===== 学期管理 (管理员权限) =====

@router.get("/semesters", **create_service_route_config(
    SemesterService, 'get_semesters', SemesterListResponse,
    summary="获取学期列表",
    description="获取所有活跃学期列表，按开始时间倒序排列",
    operation_id="get_semesters"
))
@service_api_handler(SemesterService, 'get_semesters')
async def get_semesters(
    user: UserDep,
    db: DbDep
):
    """获取学期列表"""
    service = SemesterService(db)
    result = service.get_semesters()
    
    return SemesterListResponse(
        success=True,
        data={
            "semesters": [SemesterData.model_validate(semester) for semester in result["semesters"]]
        },
        message=result["message"]
    )


@router.post("/semesters", **create_service_route_config(
    SemesterService, 'create_semester', CreateSemesterResponse,
    success_status=201,
    summary="创建学期",
    description="创建新学期（管理员专用）",
    operation_id="create_semester"
))
@service_api_handler(SemesterService, 'create_semester')
async def create_semester(
    request: CreateSemesterRequest,
    admin_user: AdminUserDep,
    db: DbDep
):
    """创建学期 (管理员专用)"""
    service = SemesterService(db)
    result = service.create_semester(request, admin_user.id)
    
    return CreateSemesterResponse(
        success=True,
        data={
            "semester": {
                "id": result["semester"].id,
                "created_at": result["semester"].created_at
            }
        },
        message=result["message"]
    )


@router.get("/semesters/{semester_id}", **create_service_route_config(
    SemesterService, 'get_semester', GetSemesterResponse,
    summary="获取学期详情",
    description="获取指定学期的详细信息",
    operation_id="get_semester"
))
@service_api_handler(SemesterService, 'get_semester')
async def get_semester(
    semester_id: int,
    user: UserDep,
    db: DbDep
):
    """获取学期详情"""
    service = SemesterService(db)
    result = service.get_semester(semester_id)
    
    return GetSemesterResponse(
        success=True,
        data={
            "semester": SemesterData.model_validate(result["semester"])
        },
        message=result["message"]
    )


@router.put("/semesters/{semester_id}", **create_service_route_config(
    SemesterService, 'update_semester', UpdateSemesterResponse,
    summary="更新学期",
    description="更新学期信息（管理员专用）",
    operation_id="update_semester"
))
@service_api_handler(SemesterService, 'update_semester')
async def update_semester(
    semester_id: int,
    request: UpdateSemesterRequest,
    admin_user: AdminUserDep,
    db: DbDep
):
    """更新学期 (管理员专用)"""
    service = SemesterService(db)
    result = service.update_semester(semester_id, request, admin_user.id)
    
    return UpdateSemesterResponse(
        success=True,
        data={
            "semester": {
                "id": result["semester"].id,
                "updated_at": result["semester"].updated_at
            }
        },
        message=result["message"]
    )


@router.delete("/semesters/{semester_id}", **create_service_route_config(
    SemesterService, 'delete_semester', DeleteSemesterResponse,
    summary="删除学期",
    description="软删除学期（管理员专用），如有关联课程则无法删除",
    operation_id="delete_semester"
))
@service_api_handler(SemesterService, 'delete_semester')
async def delete_semester(
    semester_id: int,
    admin_user: AdminUserDep,
    db: DbDep
):
    """删除学期 (管理员专用)"""
    service = SemesterService(db)
    result = service.delete_semester(semester_id, admin_user.id)
    
    return DeleteSemesterResponse(
        success=True,
        data={},  # 删除操作不返回具体数据
        message=result["message"]  # message在根级别
    )


@router.get("/semesters/{semester_id}/courses", **create_service_route_config(
    SemesterService, 'get_semester_courses', SemesterCoursesResponse,
    summary="获取学期课程",
    description="获取指定学期下的所有课程",
    operation_id="get_semester_courses"
))
@service_api_handler(SemesterService, 'get_semester_courses')
async def get_semester_courses(
    semester_id: int,
    user: UserDep,
    db: DbDep
):
    """获取学期课程列表"""
    service = SemesterService(db)
    result = service.get_semester_courses(semester_id)
    
    return SemesterCoursesResponse(
        success=True,
        data={
            "courses": [CourseData.from_orm_with_relations(course) for course in result["courses"]]
        },
        message=result["message"]
    )


# ===== 课程管理 (用户权限) =====

@router.get("/courses", **create_service_route_config(
    CourseService, 'get_courses', CourseListResponse,
    summary="获取课程列表",
    description="获取用户的课程列表，可按学期过滤",
    operation_id="get_courses"
))
@service_api_handler(CourseService, 'get_courses')
async def get_courses(
    user: UserDep,
    db: DbDep,
    semester_id: Optional[int] = Query(None, ge=1, description="学期ID过滤")
):
    """获取课程列表"""
    service = CourseService(db)
    result = service.get_courses(user.id, semester_id)
    
    return CourseListResponse(
        success=True,
        data={
            "courses": [CourseData.from_orm_with_relations(course) for course in result["courses"]]
        },
        message=result["message"]
    )


@router.post("/courses", **create_service_route_config(
    CourseService, 'create_course', CreateCourseResponse,
    success_status=201,
    summary="创建课程",
    description="创建新课程",
    operation_id="create_course"
))
@service_api_handler(CourseService, 'create_course')
async def create_course(
    request: CreateCourseRequest,
    user: UserDep,
    db: DbDep
):
    """创建课程"""
    service = CourseService(db)
    result = service.create_course(request, user.id)
    
    return CreateCourseResponse(
        success=True,
        data={
            "course": {
                "id": result["course"].id,
                "created_at": result["course"].created_at
            }
        },
        message=result["message"]
    )


@router.get("/courses/{course_id}", **create_service_route_config(
    CourseService, 'get_course', GetCourseResponse,
    summary="获取课程详情",
    description="获取指定课程的详细信息",
    operation_id="get_course"
))
@service_api_handler(CourseService, 'get_course')
async def get_course(
    course_id: int,
    user: UserDep,
    db: DbDep
):
    """获取课程详情"""
    service = CourseService(db)
    result = service.get_course(course_id, user.id)
    
    return GetCourseResponse(
        success=True,
        data={
            "course": CourseData.from_orm_with_relations(result["course"])
        },
        message=result["message"]
    )


@router.put("/courses/{course_id}", **create_service_route_config(
    CourseService, 'update_course', UpdateCourseResponse,
    summary="更新课程",
    description="更新课程信息",
    operation_id="update_course"
))
@service_api_handler(CourseService, 'update_course')
async def update_course(
    course_id: int,
    request: UpdateCourseRequest,
    user: UserDep,
    db: DbDep
):
    """更新课程"""
    service = CourseService(db)
    result = service.update_course(course_id, request, user.id)
    
    return UpdateCourseResponse(
        success=True,
        data={
            "course": {
                "id": result["course"].id,
                "updated_at": result["course"].updated_at
            }
        },
        message=result["message"]
    )


@router.delete("/courses/{course_id}", **create_service_route_config(
    CourseService, 'delete_course', DeleteCourseResponse,
    summary="删除课程",
    description="删除指定课程",
    operation_id="delete_course"
))
@service_api_handler(CourseService, 'delete_course')
async def delete_course(
    course_id: int,
    user: UserDep,
    db: DbDep
):
    """删除课程"""
    service = CourseService(db)
    result = service.delete_course(course_id, user.id)
    
    return DeleteCourseResponse(
        success=True,
        data={},  # 删除操作不返回具体数据
        message=result["message"]  # message在根级别
    )