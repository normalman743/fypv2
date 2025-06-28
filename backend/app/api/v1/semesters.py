from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, require_admin
from app.services.semester_service import SemesterService
from app.schemas.semester import (
    SemesterCreate, 
    SemesterUpdate, 
    SemesterResponse, 
    SemesterListResponse,
    SemesterCreateResponse,
    SemesterUpdateResponse
)
from app.schemas.common import SuccessResponse
from app.models.user import User

router = APIRouter(prefix="/semesters", tags=["semesters"])


@router.get("", response_model=SemesterListResponse)
async def get_semesters(
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