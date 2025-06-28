from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.services.course_service import CourseService
from app.schemas.course import (
    CourseCreate, 
    CourseUpdate, 
    CourseListResponse,
    CourseCreateResponse,
    CourseUpdateResponse
)
from app.schemas.common import SuccessResponse
from app.models.user import User

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=CourseListResponse)
async def get_courses(
    semester_id: Optional[int] = Query(None, description="Semester ID filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get course list"""
    service = CourseService(db)
    courses = service.get_courses(current_user.id, semester_id)
    
    # Convert to response format with semester info and stats
    course_list = []
    for course in courses:
        # Get course statistics
        stats = service.get_course_stats(course.id, current_user.id)
        
        course_data = {
            "id": course.id,
            "name": course.name,
            "code": course.code,
            "description": course.description,
            "semester_id": course.semester_id,
            "user_id": course.user_id,
            "created_at": course.created_at,
            "semester": {
                "id": course.semester.id,
                "name": course.semester.name,
                "code": course.semester.code
            },
            "stats": stats
        }
        course_list.append(course_data)
    
    return CourseListResponse(
        success=True,
        data={"courses": course_list}
    )


@router.post("", response_model=CourseCreateResponse)
async def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create course"""
    service = CourseService(db)
    course = service.create_course(course_data, current_user.id)
    
    return CourseCreateResponse(
        success=True,
        data={
            "course": {
                "id": course.id,
                "created_at": course.created_at
            }
        }
    )


@router.put("/{course_id}", response_model=CourseUpdateResponse)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update course"""
    service = CourseService(db)
    course = service.update_course(course_id, course_data, current_user.id)
    
    return CourseUpdateResponse(
        success=True,
        data={
            "course": {
                "id": course.id,
                "updated_at": course.created_at  # Use created_at as updated_at placeholder
            }
        }
    )


@router.delete("/{course_id}", response_model=SuccessResponse)
async def delete_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete course"""
    service = CourseService(db)
    service.delete_course(course_id, current_user.id)
    
    return SuccessResponse(success=True)