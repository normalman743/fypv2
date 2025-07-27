from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import os

from app.dependencies import get_db, get_current_user, require_admin
from app.models.user import User
from app.services.admin_service import AdminService
from app.schemas.invite_code import (
    CreateInviteCodeRequest, 
    UpdateInviteCodeRequest,
    InviteCodeResponse,
    InviteCodeListResponse,
    CreateInviteCodeResponse,
    UpdateInviteCodeResponse,
    CreateInviteCodeData,
    UpdateInviteCodeData,
    InviteCodeListData
)
from app.schemas.system import SystemConfigResponse, AuditLogsResponse
from app.schemas.common import SuccessResponse
from app.core.exceptions import NotFoundError, BadRequestError
from app.services.unified_file_service import UnifiedFileService

router = APIRouter(tags=["管理员管理/Admin Management"])

# 邀请码管理
@router.post("/invite-codes", response_model=CreateInviteCodeResponse)
async def create_invite_code(
    request: CreateInviteCodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """创建邀请码 (管理员专用)"""
    try:
        admin_service = AdminService(db)
        invite_code = admin_service.create_invite_code(request, created_by=current_user.id)
        
        return CreateInviteCodeResponse(
            data=CreateInviteCodeData(
                invite_code={
                    "id": invite_code.id,
                    "code": invite_code.code,
                    "created_at": invite_code.created_at
                }
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/invite-codes", response_model=InviteCodeListResponse)
async def get_invite_codes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取邀请码列表 (管理员专用)"""
    try:
        admin_service = AdminService(db)
        invite_codes = admin_service.get_invite_codes(skip=skip, limit=limit)
        
        invite_code_responses = [
            InviteCodeResponse(
                id=ic.id,
                code=ic.code,
                description=ic.description,
                is_used=ic.is_used,
                expires_at=ic.expires_at,
                created_at=ic.created_at
            ) for ic in invite_codes
        ]
        
        return InviteCodeListResponse(
            data=InviteCodeListData(invite_codes=invite_code_responses)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/invite-codes/{invite_code_id}", response_model=UpdateInviteCodeResponse)
async def update_invite_code(
    invite_code_id: int,
    request: UpdateInviteCodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """更新邀请码 (管理员专用)"""
    try:
        admin_service = AdminService(db)
        invite_code = admin_service.update_invite_code(invite_code_id, request)
        
        return UpdateInviteCodeResponse(
            data=UpdateInviteCodeData(
                invite_code={
                    "id": invite_code.id,
                    "updated_at": invite_code.created_at  # 使用created_at代替不存在的updated_at
                }
            )
        )
    except NotFoundError as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/invite-codes/{invite_code_id}", response_model=SuccessResponse)
async def delete_invite_code(
    invite_code_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """删除邀请码 (管理员专用)"""
    try:
        admin_service = AdminService(db)
        admin_service.delete_invite_code(invite_code_id)
        
        return SuccessResponse()
    except NotFoundError as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 系统配置
@router.get("/system/config", response_model=SystemConfigResponse)
async def get_system_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取系统配置 (管理员专用)"""
    try:
        admin_service = AdminService(db)
        config = admin_service.get_system_config()
        
        return SystemConfigResponse(
            data={"config": config}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/system/config", response_model=SystemConfigResponse)
async def update_system_config(
    config: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """更新系统配置 (管理员专用)"""
    try:
        admin_service = AdminService(db)
        updated_config = admin_service.update_system_config(config)
        
        return SystemConfigResponse(
            data={"config": updated_config}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 审计日志
@router.get("/audit-logs", response_model=AuditLogsResponse)
async def get_audit_logs(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取审计日志 (管理员专用)"""
    try:
        admin_service = AdminService(db)
        logs = admin_service.get_audit_logs(
            user_id=user_id,
            action=action,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        
        return AuditLogsResponse(
            data={"logs": logs}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/global-files/upload", response_model=SuccessResponse, operation_id="upload_global_file")
async def upload_global_file(
    file: UploadFile = File(...),
    description: str = Form(None),
    tags: str = Form(None),  # 建议前端传json字符串
    visibility: str = Form('public'),  # 新增可见性控制
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    上传全局文件（管理员专用）
    使用统一文件服务代替原有的 GlobalFileService
    """
    try:
        # 解析tags
        tags_list = json.loads(tags) if tags else []

        service = UnifiedFileService(db)
        file_record = service.upload_file(
            file=file,
            user_id=current_user.id,
            scope='global',
            description=description,
            tags=tags_list,
            visibility=visibility
        )
        return SuccessResponse(
            data={
                "file": {
                    "id": file_record.id,
                    "original_name": file_record.original_name,
                    "file_type": file_record.file_type,
                    "scope": file_record.scope,
                    "visibility": file_record.visibility,
                    "is_processed": file_record.is_processed,
                    "processing_status": file_record.processing_status,
                    "created_at": file_record.created_at,
                    "file_size": file_record.file_size,
                    "description": file_record.description,
                    "tags": file_record.tags
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/files/{file_id}/reprocess-rag", response_model=SuccessResponse)
async def reprocess_file_rag(
    file_id: int,
    use_async: bool = Query(True, description="是否使用异步处理"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    重新处理文件RAG（管理员专用）
    适用于处理失败的文件
    """
    try:
        from app.models.file import File
        from app.models.physical_file import PhysicalFile
        from app.services.local_file_storage import local_file_storage
        
        # 获取文件记录
        file_record = db.query(File).filter(File.id == file_id).first()
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        physical_file = db.query(PhysicalFile).filter(
            PhysicalFile.id == file_record.physical_file_id
        ).first()
        if not physical_file:
            raise HTTPException(status_code=404, detail="Physical file not found")
        
        # 检查文件是否存在于磁盘
        full_path = local_file_storage.base_dir / physical_file.storage_path
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        # 重置处理状态
        file_record.processing_status = "processing"
        file_record.is_processed = False
        file_record.processing_error = None
        db.commit()
        
        if use_async:
            # 异步处理
            from app.tasks.file_processing import process_file_rag_task
            with open(full_path, 'rb') as f:
                file_content = f.read()
            
            task = process_file_rag_task.delay(file_id, file_content)
            
            return SuccessResponse(
                data={
                    "message": "RAG processing started",
                    "task_id": task.id,
                    "file_id": file_id,
                    "processing_mode": "async"
                }
            )
        else:
            # 同步处理
            from app.services.rag_service import ProductionRAGService
            try:
                rag_service = ProductionRAGService(db_session=db)
                result = rag_service.process_file(file_record, str(full_path))
                
                file_record.is_processed = True
                file_record.processing_status = "completed"
                db.commit()
                
                return SuccessResponse(
                    data={
                        "message": "RAG processing completed",
                        "file_id": file_id,
                        "processing_mode": "sync",
                        "result": result
                    }
                )
            except Exception as e:
                file_record.processing_status = "failed"
                file_record.processing_error = str(e)
                db.commit()
                raise HTTPException(status_code=500, detail=f"RAG processing failed: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/global-files", response_model=SuccessResponse)
async def get_global_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    visibility: Optional[str] = Query(None),  # 可根据可见性过滤
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取全局文件列表（管理员专用）"""
    try:
        service = UnifiedFileService(db)
        files = service.get_accessible_files(
            user_id=current_user.id,
            scope='global',
            include_shared=True
        )
        
        # 按可见性过滤
        if visibility:
            files = [f for f in files if f.visibility == visibility]
        
        # 分页
        total = len(files)
        files_page = files[skip:skip + limit]
        
        files_data = [
            {
                "id": file.id,
                "original_name": file.original_name,
                "file_type": file.file_type,
                "visibility": file.visibility,
                "owner_id": file.user_id,
                "is_processed": file.is_processed,
                "processing_status": file.processing_status,
                "created_at": file.created_at,
                "file_size": file.file_size,
                "description": file.description,
                "tags": file.tags
            }
            for file in files_page
        ]
        
        return SuccessResponse(
            data={
                "files": files_data,
                "pagination": {
                    "total": total,
                    "skip": skip,
                    "limit": limit,
                    "has_more": skip + limit < total
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/global-files/{file_id}", response_model=SuccessResponse)
async def delete_global_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """删除全局文件（管理员专用）"""
    try:
        # 验证文件确实是全局文件
        from app.models.file import File
        file_record = db.query(File).filter(File.id == file_id).first()
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        if file_record.scope != 'global':
            raise HTTPException(status_code=400, detail="This is not a global file")
        
        service = UnifiedFileService(db)
        success = service.delete_file(file_id, current_user.id)
        
        if success:
            return SuccessResponse(data={"message": "Global file deleted successfully"})
        else:
            raise HTTPException(status_code=500, detail="Failed to delete global file")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
