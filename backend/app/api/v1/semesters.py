from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, require_admin
from app.services.semester_service import SemesterService
from app.services.course_service import CourseService
from app.schemas.semester import (
    SemesterCreate, 
    SemesterUpdate, 
    SemesterResponse, 
    SemesterListResponse,
    SemesterCreateResponse,
    SemesterUpdateResponse
)
from app.schemas.course import CourseListResponse
from app.schemas.common import SuccessResponse
from app.models.user import User

router = APIRouter(prefix="/semesters", tags=["semesters"])


@router.get("", response_model=SemesterListResponse)
async def get_semesters(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get semester list"""
    service = SemesterService(db)
    semesters = service.get_semesters()
    
    # Convert to response format
    semester_list = [SemesterResponse.model_validate(semester) for semester in semesters]
    
    return SemesterListResponse(
        success=True,
        data={"semesters": semester_list}
    )


@router.post("", response_model=SemesterCreateResponse)
async def create_semester(
    semester_data: SemesterCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create semester (admin only)"""
    service = SemesterService(db)
    semester = service.create_semester(semester_data)
    
    return SemesterCreateResponse(
        success=True,
        data={
            "semester": {
                "id": semester.id,
                "created_at": semester.created_at
            }
        }
    )


@router.put("/{semester_id}", response_model=SemesterUpdateResponse)
async def update_semester(
    semester_id: int,
    semester_data: SemesterUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update semester (admin only)"""
    service = SemesterService(db)
    semester = service.update_semester(semester_id, semester_data)
    
    return SemesterUpdateResponse(
        success=True,
        data={
            "semester": {
                "id": semester.id,
                "updated_at": semester.created_at  # Use created_at as updated_at placeholder
            }
        }
    )


@router.get("/{semester_id}", response_model=SemesterListResponse)
async def get_semester(
    semester_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get semester details"""
    service = SemesterService(db)
    semester = service.get_semester(semester_id)
    
    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")
    
    semester_data = SemesterResponse.model_validate(semester)
    
    return SemesterListResponse(
        success=True,
        data={"semester": semester_data}
    )


@router.get("/{semester_id}/courses", response_model=CourseListResponse)
async def get_semester_courses(
    semester_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all courses for a semester"""
    # First check if semester exists
    semester_service = SemesterService(db)
    semester = semester_service.get_semester(semester_id)
    
    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")
    
    # Get courses for this semester (filtered by current user)
    course_service = CourseService(db)
    courses = course_service.get_courses(user_id=current_user.id, semester_id=semester_id)
    
    # Convert to response format with semester info and stats
    course_list = []
    for course in courses:
        # Get course statistics
        stats = course_service.get_course_stats(course.id, course.user_id)
        
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


@router.delete("/{semester_id}", response_model=SuccessResponse)
async def delete_semester(
    semester_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete semester (admin only)"""
    service = SemesterService(db)
    service.delete_semester(semester_id)
    
    return SuccessResponse(success=True)