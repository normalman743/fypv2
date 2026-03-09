import time
import logging
from fastapi import APIRouter, Depends, Path
from fastapi.responses import JSONResponse
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
    
    # 批量获取 stats（一条 SQL 替代 N 条）
    folder_ids = [f.id for f in folders]
    stats_map = service.get_batch_folder_stats(folder_ids)
    
    folder_list = []
    for folder in folders:
        stats = stats_map.get(folder.id, {"file_count": 0})
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


@router.get("/courses/{course_id}/resources")
async def get_course_resources(
    course_id: int = Path(..., description="Course ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    一次性获取课程所有文件夹及其文件。
    替代前端分别调用 /courses/{id}/folders + N 次 /folders/{id}/files 的瀑布请求。
    """
    t0 = time.perf_counter()
    service = FolderService(db)
    result = service.get_course_folders_with_files(course_id, current_user.id)
    t1 = time.perf_counter()
    logging.info(f"⏱️ [Resources] course_id={course_id}: {(t1 - t0) * 1000:.1f}ms ({len(result)} folders)")
    
    return {
        "success": True,
        "data": {"folders": result}
    }
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

"""
@router.post("/folders", response_model=CreateFolderResponse,include_in_schema=False)
async def create_general_folder(
    folder_data: CreateFolderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    service = FolderService(db)
    
    # If it's a course folder, use the course-specific method
    if hasattr(folder_data, 'course_id') and folder_data.course_id:
        folder = service.create_folder(folder_data.course_id, folder_data, current_user.id)
    else:
        # Create personal folder - need to implement this method
        folder = service.create_personal_folder(folder_data, current_user.id)
    
    return CreateFolderResponse(
        success=True,
        data={
            "folder": {
                "id": folder.id,
                "created_at": folder.created_at
            }
        }
    )
"""

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