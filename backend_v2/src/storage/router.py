"""Storage模块API路由"""
from fastapi import APIRouter, Depends, Path, Query, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List

from src.shared.dependencies import DbDep, UserDep
from src.shared.api_decorator import create_service_route_config, service_api_handler
from src.shared.schemas import BaseResponse, MessageResponse
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

@folder_router.get("/courses/{course_id}/folders", **create_service_route_config(
    FolderService, 'get_course_folders', FolderListResponse,
    summary="获取课程文件夹列表",
    description="获取指定课程的所有文件夹，包括统计信息",
    operation_id="get_course_folders"
))
@service_api_handler(FolderService, 'get_course_folders')
def get_course_folders(
    current_user: UserDep,
    db: DbDep,
    course_id: int = Path(..., description="Course ID")
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


@folder_router.post("/courses/{course_id}/folders", **create_service_route_config(
    FolderService, 'create_folder', CreateFolderResponse,
    success_status=201,
    summary="创建文件夹",
    description="在指定课程中创建新的文件夹",
    operation_id="create_folder"
))
@service_api_handler(FolderService, 'create_folder')
def create_folder(
    folder_data: CreateFolderRequest,
    current_user: UserDep,
    db: DbDep,
    course_id: int = Path(..., description="Course ID")
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


@folder_router.put("/folders/{folder_id}", **create_service_route_config(
    FolderService, 'update_folder', CreateFolderResponse,
    summary="更新文件夹",
    description="更新文件夹的名称和类型",
    operation_id="update_folder"
))
@service_api_handler(FolderService, 'update_folder')
def update_folder(
    folder_data: UpdateFolderRequest,
    current_user: UserDep,
    db: DbDep,
    folder_id: int = Path(..., description="Folder ID")
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


@folder_router.delete("/folders/{folder_id}", **create_service_route_config(
    FolderService, 'delete_folder', MessageResponse,
    summary="删除文件夹",
    description="删除空的文件夹（非默认文件夹）",
    operation_id="delete_folder"
))
@service_api_handler(FolderService, 'delete_folder')
def delete_folder(
    current_user: UserDep,
    db: DbDep,
    folder_id: int = Path(..., description="Folder ID")
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

@file_router.get("/folders/{folder_id}/files", **create_service_route_config(
    FileService, 'get_folder_files', FileListResponse,
    summary="获取文件夹文件列表",
    description="获取指定文件夹中的所有文件",
    operation_id="get_folder_files"
))
@service_api_handler(FileService, 'get_folder_files')
def get_folder_files(
    current_user: UserDep,
    db: DbDep,
    folder_id: int = Path(..., description="Folder ID")
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


@file_router.post("/files/upload", **create_service_route_config(
    FileService, 'upload_file', UploadFileResponse,
    success_status=201,
    summary="上传文件",
    description="上传文件到指定文件夹，支持SHA256去重",
    operation_id="upload_file"
))
@service_api_handler(FileService, 'upload_file')
def upload_file(
    current_user: UserDep,
    db: DbDep,
    file: UploadFile = File(...),
    course_id: int = Form(...),
    folder_id: int = Form(...),
    description: Optional[str] = Form(None)
):
    """上传文件到指定文件夹"""
    service = FileService(db)
    file_record = service.upload_file(file, course_id, folder_id, current_user.id, description)
    
    file_response = FileResponse.model_validate(file_record)
    
    return UploadFileResponse(
        success=True,
        data={"file": file_response}
    )


@file_router.get("/files/{file_id}/download", **create_service_route_config(
    FileService, 'download_file', None,
    summary="下载文件",
    description="下载指定文件，返回文件流",
    operation_id="download_file"
))
@service_api_handler(FileService, 'download_file')
def download_file(
    current_user: UserDep,
    db: DbDep,
    file_id: int = Path(..., description="File ID")
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


@file_router.delete("/files/{file_id}", **create_service_route_config(
    FileService, 'delete_file', MessageResponse,
    summary="删除文件",
    description="删除指定文件（仅创建者或管理员）",
    operation_id="delete_file"
))
@service_api_handler(FileService, 'delete_file')
def delete_file(
    current_user: UserDep,
    db: DbDep,
    file_id: int = Path(..., description="File ID")
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

@file_router.post("/tempfiles/upload", **create_service_route_config(
    TemporaryFileService, 'upload_temporary_file', UploadTemporaryFileResponse,
    success_status=201,
    summary="上传临时文件",
    description="上传临时文件，支持设置过期时间",
    operation_id="upload_temporary_file"
))
@service_api_handler(TemporaryFileService, 'upload_temporary_file')
def upload_temporary_file(
    current_user: UserDep,
    db: DbDep,
    file: UploadFile = File(...),
    expiry_hours: int = Form(24, description="过期时间（小时）"),
    purpose: Optional[str] = Form(None, description="用途说明")
):
    """上传临时文件"""
    service = TemporaryFileService(db)
    temp_file = service.upload_temporary_file(file, current_user.id, expiry_hours, purpose)
    
    temp_file_response = TemporaryFileResponse.model_validate(temp_file)
    
    return UploadTemporaryFileResponse(
        success=True,
        data={"file": temp_file_response}
    )


@file_router.get("/tempfiles/{file_id}/download", **create_service_route_config(
    TemporaryFileService, 'download_temporary_file', None,
    summary="下载临时文件",
    description="下载临时文件，检查过期状态",
    operation_id="download_temporary_file"
))
@service_api_handler(TemporaryFileService, 'download_temporary_file')
def download_temporary_file(
    current_user: UserDep,
    db: DbDep,
    file_id: int = Path(..., description="临时文件ID")
):
    """下载临时文件"""
    service = TemporaryFileService(db)
    temp_file, file_path = service.download_temporary_file(file_id, current_user.id)
    
    return FileResponse(
        path=file_path,
        filename=temp_file.filename,
        media_type=temp_file.mime_type
    )


@file_router.delete("/tempfiles/{file_id}", **create_service_route_config(
    TemporaryFileService, 'delete_temporary_file', MessageResponse,
    summary="删除临时文件",
    description="删除指定的临时文件",
    operation_id="delete_temporary_file"
))
@service_api_handler(TemporaryFileService, 'delete_temporary_file')
def delete_temporary_file(
    current_user: UserDep,
    db: DbDep,
    file_id: int = Path(..., description="临时文件ID")
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

@file_router.post("/globalfiles/upload",
    response_model=UploadFileResponse,
    summary="上传全局文件",
    description="上传全局文件（管理员专用），功能暂未实现",
    operation_id="upload_global_file"
)
def upload_global_file(
    current_user: UserDep,
    db: DbDep,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None)
):
    """上传全局文件（管理员专用）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # TODO: 实现全局文件上传逻辑
    # 这里应该调用专门的全局文件服务
    raise HTTPException(status_code=501, detail="功能暂未实现")


@file_router.get("/globalfiles",
    response_model=FileListResponse,
    summary="获取全局文件列表",
    description="获取全局文件列表（管理员专用），功能暂未实现",
    operation_id="get_global_files"
)
def get_global_files(
    current_user: UserDep,
    db: DbDep,
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="每页记录数")
):
    """获取全局文件列表（管理员专用）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # TODO: 实现全局文件列表查询逻辑
    raise HTTPException(status_code=501, detail="功能暂未实现")


@file_router.delete("/globalfiles/{file_id}",
    response_model=MessageResponse,
    summary="删除全局文件",
    description="删除全局文件（管理员专用），功能暂未实现",
    operation_id="delete_global_file"
)
def delete_global_file(
    current_user: UserDep,
    db: DbDep,
    file_id: int = Path(..., description="文件ID")
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