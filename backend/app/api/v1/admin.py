from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.dependencies import get_db, get_current_user, require_admin
from app.models.user import User
from app.services.admin_service import AdminService
from app.schemas.invite_code import (
    CreateInviteCodeRequest, 
    UpdateInviteCodeRequest,
    InviteCodeResponse,
    InviteCodeListResponse,
    CreateInviteCodeResponse,
    UpdateInviteCodeResponse
)
from app.schemas.common import ResponseModel, ErrorResponse
from app.core.exceptions import NotFoundError, BadRequestError

router = APIRouter(tags=["管理员"])

# 邀请码管理
@router.post("/invite-codes", response_model=ResponseModel[CreateInviteCodeResponse])
async def create_invite_code(
    request: CreateInviteCodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """创建邀请码 (管理员专用)"""
    try:
        admin_service = AdminService(db)
        invite_code = admin_service.create_invite_code(request, created_by=current_user.id)
        
        return ResponseModel(
            success=True,
            data=CreateInviteCodeResponse(
                invite_code={
                    "id": invite_code.id,
                    "code": invite_code.code,
                    "created_at": invite_code.created_at
                }
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/invite-codes", response_model=ResponseModel[InviteCodeListResponse])
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
        
        return ResponseModel(
            success=True,
            data=InviteCodeListResponse(invite_codes=invite_code_responses)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/invite-codes/{invite_code_id}", response_model=ResponseModel[UpdateInviteCodeResponse])
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
        
        return ResponseModel(
            success=True,
            data=UpdateInviteCodeResponse(
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

@router.delete("/invite-codes/{invite_code_id}", response_model=ResponseModel)
async def delete_invite_code(
    invite_code_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """删除邀请码 (管理员专用)"""
    try:
        admin_service = AdminService(db)
        admin_service.delete_invite_code(invite_code_id)
        
        return ResponseModel(success=True)
    except NotFoundError as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 系统配置
@router.get("/system/config", response_model=ResponseModel[Dict[str, Any]])
async def get_system_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取系统配置 (管理员专用)"""
    try:
        admin_service = AdminService(db)
        config = admin_service.get_system_config()
        
        return ResponseModel(success=True, data={"config": config})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/system/config", response_model=ResponseModel[Dict[str, Any]])
async def update_system_config(
    config: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """更新系统配置 (管理员专用)"""
    try:
        admin_service = AdminService(db)
        updated_config = admin_service.update_system_config(config)
        
        return ResponseModel(success=True, data={"config": updated_config})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 审计日志
@router.get("/audit-logs", response_model=ResponseModel[Dict[str, Any]])
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
        
        return ResponseModel(success=True, data={"logs": logs})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 