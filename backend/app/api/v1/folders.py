from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.services.folder_service import FolderService
from app.schemas.folder import (
    CreateFolderRequest,
    FolderListResponse,
    CreateFolderResponse,
    FolderResponse,
    FolderStats
)
from app.schemas.common import SuccessResponse
from app.models.user import User

router = APIRouter(tags=["folders"])


@router.get("/courses/{course_id}/folders", response_model=FolderListResponse)
async def get_course_folders(
    course_id: int = Path(..., description="Course ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all folders for a course"""
    service = FolderService(db)
    folders = service.get_course_folders(course_id, current_user.id)
    
    # Convert to response format with stats
    folder_list = []
    for folder in folders:
        stats = service.get_folder_stats(folder.id)
        folder_data = FolderResponse(
            id=folder.id,
            name=folder.name,
            folder_type=folder.folder_type,
            course_id=folder.course_id,
            is_default=folder.is_default,
            created_at=folder.created_at,
            stats=FolderStats(**stats)
        )
        folder_list.append(folder_data)
    
    return FolderListResponse(
        success=True,
        data={"folders": [folder.model_dump() for folder in folder_list]}
    )


@router.post("/courses/{course_id}/folders", response_model=CreateFolderResponse)
async def create_folder(
    course_id: int = Path(..., description="Course ID"),
    folder_data: CreateFolderRequest = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new folder in course"""
    service = FolderService(db)
    folder = service.create_folder(course_id, folder_data, current_user.id)
    
    return CreateFolderResponse(
        success=True,
        data={
            "folder": {
                "id": folder.id,
                "created_at": folder.created_at
            }
        }
    )


@router.delete("/folders/{folder_id}", response_model=SuccessResponse)
async def delete_folder(
    folder_id: int = Path(..., description="Folder ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a folder"""
    service = FolderService(db)
    service.delete_folder(folder_id, current_user.id)
    
    return SuccessResponse(success=True)