from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.unified_file_service import UnifiedFileService
from app.services.file_permission_service import FilePermissionService
from app.schemas.common import ErrorResponse, SuccessResponse
from app.schemas.unified_file import (
    FileUploadResponse, FileListResponse, FileDetailResponse,
    FileAccessLogResponse, FileShareResponse, FileDeleteResponse,
    FileUploadData, FileListData, FileAccessLogData, FileShareData
)
from app.core.exceptions import NotFoundError, BadRequestError

router = APIRouter(tags=["统一文件管理"])


@router.post("/files/upload", response_model=FileUploadResponse, operation_id="unified_upload_file")
async def upload_file(
    file: UploadFile = File(...),
    scope: str = Form('course'),  # 'course', 'global', 'personal'
    course_id: Optional[int] = Form(None),
    folder_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON string
    visibility: str = Form('private'),  # 'private', 'course', 'public', 'shared'
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    统一文件上传接口
    
    支持三种作用域:
    - course: 课程文件 (需要 course_id)
    - global: 全局文件 (管理员权限)
    - personal: 个人文件
    """
    try:
        # 解析 tags
        tags_list = json.loads(tags) if tags else []
        
        # 权限检查
        if scope == 'global' and current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Only admins can upload global files")
        
        service = UnifiedFileService(db)
        file_record = service.upload_file(
            file=file,
            user_id=current_user.id,
            scope=scope,
            course_id=course_id,
            folder_id=folder_id,
            description=description,
            tags=tags_list,
            visibility=visibility
        )
        
        # 记录上传日志
        service.log_file_access(
            file_id=file_record.id,
            user_id=current_user.id,
            action='upload',
            access_via='api'
        )
        
        return FileUploadResponse(
            data=FileUploadData(
                file={
                    "id": file_record.id,
                    "original_name": file_record.original_name,
                    "file_type": file_record.file_type,
                    "scope": file_record.scope,
                    "visibility": file_record.visibility,
                    "course_id": file_record.course_id,
                    "folder_id": file_record.folder_id,
                    "is_processed": file_record.is_processed,
                    "processing_status": file_record.processing_status,
                    "created_at": file_record.created_at,
                    "file_size": file_record.file_size,
                    "file_hash": file_record.file_hash,  # 添加hash字段
                    "description": file_record.description,
                    "tags": file_record.tags
                }
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/files", response_model=FileListResponse)
async def get_files(
    scope: Optional[str] = Query(None),
    course_id: Optional[int] = Query(None),
    include_shared: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户可访问的文件列表
    """
    try:
        service = UnifiedFileService(db)
        files = service.get_accessible_files(
            user_id=current_user.id,
            scope=scope,
            course_id=course_id,
            include_shared=include_shared
        )
        
        # 分页
        total = len(files)
        files_page = files[skip:skip + limit]
        
        files_data = [
            {
                "id": file.id,
                "original_name": file.original_name,
                "file_type": file.file_type,
                "scope": file.scope,
                "visibility": file.visibility,
                "course_id": file.course_id,
                "folder_id": file.folder_id,
                "owner_id": file.user_id,
                "is_processed": file.is_processed,
                "processing_status": file.processing_status,
                "created_at": file.created_at,
                "updated_at": file.updated_at,
                "file_size": file.file_size,
                "description": file.description,
                "tags": file.tags,
                "is_owner": file.user_id == current_user.id
            }
            for file in files_page
        ]
        
        return FileListResponse(
            data=FileListData(
                files=files_data,
                pagination={
                    "total": total,
                    "skip": skip,
                    "limit": limit,
                    "has_more": skip + limit < total
                }
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/files/{file_id}", response_model=FileDetailResponse)
async def get_file_detail(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文件详情"""
    try:
        service = UnifiedFileService(db)
        
        # 检查文件是否存在以及用户是否有权限访问
        from app.models.file import File
        file_record = db.query(File).filter(File.id == file_id).first()
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        if not file_record.can_access(current_user.id):
            # 这里应该实现更复杂的权限检查逻辑
            if file_record.user_id != current_user.id and file_record.visibility == 'private':
                raise HTTPException(status_code=403, detail="No permission to access this file")
        
        # 记录访问日志
        service.log_file_access(
            file_id=file_id,
            user_id=current_user.id,
            action='view',
            access_via='api'
        )
        
        return FileDetailResponse(
            data={
                "file": {
                    "id": file_record.id,
                    "original_name": file_record.original_name,
                    "file_type": file_record.file_type,
                    "scope": file_record.scope,
                    "visibility": file_record.visibility,
                    "course_id": file_record.course_id,
                    "folder_id": file_record.folder_id,
                    "owner_id": file_record.user_id,
                    "is_processed": file_record.is_processed,
                    "processing_status": file_record.processing_status,
                    "processing_error": file_record.processing_error,
                    "processed_at": file_record.processed_at,
                    "chunk_count": file_record.chunk_count,
                    "content_preview": file_record.content_preview,
                    "created_at": file_record.created_at,
                    "updated_at": file_record.updated_at,
                    "file_size": file_record.file_size,
                    "file_hash": file_record.file_hash,
                    "description": file_record.description,
                    "tags": file_record.tags,
                    "is_owner": file_record.user_id == current_user.id,
                    "is_shareable": file_record.is_shareable
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/files/{file_id}/share", response_model=FileShareResponse, operation_id="share_file")
async def share_file(
    file_id: int,
    shared_with_type: str = Form(...),  # 'user', 'course', 'group', 'public'
    shared_with_id: Optional[int] = Form(None),
    permission_level: str = Form('read'),  # 'read', 'comment', 'edit', 'manage'
    can_reshare: bool = Form(False),
    expires_at: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """共享文件"""
    try:
        service = UnifiedFileService(db)
        share = service.share_file(
            file_id=file_id,
            shared_with_type=shared_with_type,
            shared_with_id=shared_with_id,
            permission_level=permission_level,
            shared_by=current_user.id,
            can_reshare=can_reshare,
            expires_at=expires_at
        )
        
        return FileShareResponse(
            data=FileShareData(
                share={
                    "id": share.id,
                    "file_id": share.file_id,
                    "shared_with_type": share.shared_with_type,
                    "shared_with_id": share.shared_with_id,
                    "permission_level": share.permission_level,
                    "can_reshare": share.can_reshare,
                    "expires_at": share.expires_at,
                    "created_at": share.created_at
                }
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/files/{file_id}", response_model=FileDeleteResponse, operation_id="unified_delete_file")
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除文件"""
    try:
        service = UnifiedFileService(db)
        success = service.delete_file(file_id, current_user.id)
        
        if success:
            return FileDeleteResponse(data={"message": "File deleted successfully"})
        else:
            raise HTTPException(status_code=500, detail="Failed to delete file")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/files/{file_id}/access-logs", response_model=FileAccessLogResponse)
async def get_file_access_logs(
    file_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文件访问日志 (仅文件所有者可查看)"""
    try:
        from app.models.file import File
        from app.models.file_share import FileAccessLog
        
        # 检查权限
        file_record = db.query(File).filter(File.id == file_id).first()
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        if file_record.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only file owner can view access logs")
        
        # 获取访问日志
        logs = db.query(FileAccessLog).filter(
            FileAccessLog.file_id == file_id
        ).order_by(
            FileAccessLog.accessed_at.desc()
        ).offset(skip).limit(limit).all()
        
        total = db.query(FileAccessLog).filter(FileAccessLog.file_id == file_id).count()
        
        logs_data = [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "access_via": log.access_via,
                "ip_address": log.ip_address,
                "accessed_at": log.accessed_at
            }
            for log in logs
        ]
        
        return FileAccessLogResponse(
            data=FileAccessLogData(
                logs=logs_data,
                pagination={
                    "total": total,
                    "skip": skip,
                    "limit": limit,
                    "has_more": skip + limit < total
                }
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))