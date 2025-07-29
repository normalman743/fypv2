"""Storage模块API路由"""
from fastapi import APIRouter, Depends, Path, Query, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List

from src.shared.dependencies import get_db, get_current_user
from src.shared.exceptions import handle_service_exceptions
from src.shared.schemas import BaseResponse, MessageResponse
from src.auth.models import User
from .service import FolderService, FileService, TemporaryFileService
from .schemas import (
    CreateFolderRequest, UpdateFolderRequest, FolderListResponse, CreateFolderResponse,
    FileListResponse, UploadFileResponse, UploadTemporaryFileResponse,
    FolderResponse, FolderStats, FileResponse, TemporaryFileResponse
)


# 创建路由器 (移除prefix，由main.py统一管理)
folder_router = APIRouter(tags=["文件夹管理/Folder Management"])
file_router = APIRouter(tags=["文件管理/File Management"])


# ===== 文件夹管理路由 =====

@folder_router.get("/courses/{course_id}/folders", response_model=FolderListResponse)
@handle_service_exceptions
async def get_course_folders(
    course_id: int = Path(..., description="Course ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课程的所有文件夹"""
    service = FolderService(db)
    folders = service.get_course_folders(course_id, current_user.id)
    
    # 转换为响应格式
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
        data={"folders": folder_list}
    )


@folder_router.post("/courses/{course_id}/folders", response_model=CreateFolderResponse)
@handle_service_exceptions
async def create_folder(
    course_id: int = Path(..., description="Course ID"),
    folder_data: CreateFolderRequest = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建文件夹"""
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


@folder_router.put("/folders/{folder_id}", response_model=CreateFolderResponse)
@handle_service_exceptions
async def update_folder(
    folder_id: int = Path(..., description="Folder ID"),
    folder_data: UpdateFolderRequest = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新文件夹"""
    service = FolderService(db)
    folder = service.update_folder(folder_id, folder_data, current_user.id)
    
    return CreateFolderResponse(
        success=True,
        data={
            "folder": {
                "id": folder.id,
                "updated_at": folder.created_at  # TODO: 添加updated_at字段到模型
            }
        }
    )


@folder_router.delete("/folders/{folder_id}", response_model=MessageResponse)
@handle_service_exceptions
async def delete_folder(
    folder_id: int = Path(..., description="Folder ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除文件夹"""
    service = FolderService(db)
    service.delete_folder(folder_id, current_user.id)
    
    return MessageResponse(
        success=True,
        data={},
        message="文件夹删除成功"
    )


# ===== 文件管理路由 =====

@file_router.get("/folders/{folder_id}/files", response_model=FileListResponse)
@handle_service_exceptions
async def get_folder_files(
    folder_id: int = Path(..., description="Folder ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取文件夹中的所有文件"""
    service = FileService(db)
    files = service.get_folder_files(folder_id, current_user.id)
    
    # 转换为响应格式
    file_list = []
    for file in files:
        file_data = FileResponse.model_validate(file)
        file_list.append(file_data)
    
    return FileListResponse(
        success=True,
        data={"files": file_list}
    )


@file_router.post("/files/upload", response_model=UploadFileResponse)
@handle_service_exceptions
async def upload_file(
    file: UploadFile = File(...),
    course_id: int = Form(...),
    folder_id: int = Form(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传文件到指定文件夹"""
    service = FileService(db)
    file_record = service.upload_file(file, course_id, folder_id, current_user.id, description)
    
    file_response = FileResponse.model_validate(file_record)
    
    return UploadFileResponse(
        success=True,
        data={"file": file_response}
    )


@file_router.get("/files/{file_id}/download")
@handle_service_exceptions
async def download_file(
    file_id: int = Path(..., description="File ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """下载文件"""
    service = FileService(db)
    file_record, storage_path = service.download_file(file_id, current_user.id)
    
    # 返回文件流响应
    return FileResponse(
        path=storage_path,
        filename=file_record.original_name,
        media_type=file_record.mime_type
    )


@file_router.delete("/files/{file_id}", response_model=MessageResponse)
@handle_service_exceptions
async def delete_file(
    file_id: int = Path(..., description="File ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除文件"""
    service = FileService(db)
    service.delete_file(file_id, current_user.id)
    
    return MessageResponse(
        success=True,
        data={},
        message="文件删除成功"
    )


# ===== 临时文件管理路由 =====

@file_router.post("/tempfiles/upload", response_model=UploadTemporaryFileResponse)
@handle_service_exceptions
async def upload_temporary_file(
    file: UploadFile = File(...),
    expiry_hours: int = Form(24, description="过期时间（小时）"),
    purpose: Optional[str] = Form(None, description="用途说明"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传临时文件"""
    service = TemporaryFileService(db)
    temp_file = service.upload_temporary_file(file, current_user.id, expiry_hours, purpose)
    
    temp_file_response = TemporaryFileResponse.model_validate(temp_file)
    
    return UploadTemporaryFileResponse(
        success=True,
        data={"file": temp_file_response}
    )


@file_router.get("/tempfiles/{file_id}/download")
@handle_service_exceptions
async def download_temporary_file(
    file_id: int = Path(..., description="临时文件ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """下载临时文件"""
    service = TemporaryFileService(db)
    temp_file, file_path = service.download_temporary_file(file_id, current_user.id)
    
    return FileResponse(
        path=file_path,
        filename=temp_file.filename,
        media_type=temp_file.mime_type
    )


@file_router.delete("/tempfiles/{file_id}", response_model=MessageResponse)
@handle_service_exceptions
async def delete_temporary_file(
    file_id: int = Path(..., description="临时文件ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除临时文件"""
    service = TemporaryFileService(db)
    service.delete_temporary_file(file_id, current_user.id)
    
    return MessageResponse(
        success=True,
        data={},
        message="临时文件删除成功"
    )


# ===== 全局文件管理路由（管理员专用） =====

@file_router.post("/globalfiles/upload", response_model=UploadFileResponse)
@handle_service_exceptions
async def upload_global_file(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传全局文件（管理员专用）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # TODO: 实现全局文件上传逻辑
    # 这里应该调用专门的全局文件服务
    raise HTTPException(status_code=501, detail="功能暂未实现")


@file_router.get("/globalfiles", response_model=FileListResponse)
@handle_service_exceptions
async def get_global_files(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="每页记录数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取全局文件列表（管理员专用）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # TODO: 实现全局文件列表查询逻辑
    raise HTTPException(status_code=501, detail="功能暂未实现")


@file_router.delete("/globalfiles/{file_id}", response_model=MessageResponse)
@handle_service_exceptions
async def delete_global_file(
    file_id: int = Path(..., description="文件ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除全局文件（管理员专用）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # TODO: 实现全局文件删除逻辑
    raise HTTPException(status_code=501, detail="功能暂未实现")


# 合并路由器 (使用统一命名规范)
router = APIRouter()
router.include_router(folder_router)
router.include_router(file_router)

# 保持向后兼容性
storage_router = router