from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, require_admin
from app.services.semester_service import SemesterService
from app.services.course_service import CourseService
from app.schemas.semester import (
    SemesterCreate, 
    SemesterUpdate, 
    SemesterResponse, 
    SemesterListResponse,
    SemesterOperationResponse
)
from app.schemas.course import CourseListResponse
from app.schemas.common import SuccessResponse
from app.models.user import User
from app.core.exceptions import NotFoundError, ConflictError, BadRequestError

router = APIRouter(prefix="/semesters", tags=["学期管理/Semesters"])


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


@router.post("", response_model=SemesterOperationResponse)
async def create_semester(
    semester_data: SemesterCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create semester (admin only)"""
    try:
        service = SemesterService(db)
        semester = service.create_semester(semester_data)
        
        return SemesterOperationResponse(
            success=True,
            data={
                "semester": {
                    "id": semester.id,
                    "created_at": semester.created_at
                }
            }
        )
    except (ConflictError, BadRequestError) as e:
        raise e


@router.put("/{semester_id}", response_model=SemesterOperationResponse)
async def update_semester(
    semester_id: int,
    semester_data: SemesterUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update semester (admin only)"""
    try:
        service = SemesterService(db)
        semester = service.update_semester(semester_id, semester_data)
        
        return SemesterOperationResponse(
            success=True,
            data={
                "semester": {
                    "id": semester.id,
                    "updated_at": semester.created_at  # Use created_at as updated_at placeholder
                }
            }
        )
    except (NotFoundError, ConflictError, BadRequestError) as e:
        raise e


@router.get("/{semester_id}", response_model=SemesterListResponse)
async def get_semester(
    semester_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get semester details"""
    try:
        service = SemesterService(db)
        semester = service.get_semester(semester_id)
        
        semester_data = SemesterResponse.model_validate(semester)
        
        return SemesterListResponse(
            success=True,
            data={"semester": semester_data}
        )
    except NotFoundError as e:
        raise e


@router.get("/{semester_id}/courses", response_model=CourseListResponse)
async def get_semester_courses(
    semester_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all courses for a semester"""
    try:
        # Verify semester exists
        semester_service = SemesterService(db)
        semester = semester_service.get_semester(semester_id)
        
        # Get courses with stats (business logic moved to service)
        course_service = CourseService(db)
        courses_with_stats = course_service.get_courses_with_stats(
            user_id=current_user.id, 
            semester_id=semester_id
        )
        
        return CourseListResponse(
            success=True,
            data={"courses": courses_with_stats}
        )
    except NotFoundError as e:
        raise e


@router.delete("/{semester_id}", response_model=SuccessResponse)
async def delete_semester(
    semester_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete semester (admin only)"""
    try:
        service = SemesterService(db)
        service.delete_semester(semester_id)
        
        return SuccessResponse(success=True)
    except (NotFoundError, ConflictError) as e:
        raise e