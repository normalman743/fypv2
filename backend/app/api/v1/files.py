from fastapi import APIRouter, Depends, Path, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import io

from app.dependencies import get_db, get_current_user
from app.services.file_service import FileService
from app.schemas.file import (
    FileListResponse,
    FilePreviewResponse,
    UploadFileResponse,
    FileResponse,
    FolderInfo,
    UploadTemporaryFileResponse,
    TemporaryFileResponse
)
from app.schemas.common import SuccessResponse
from app.models.user import User

router = APIRouter(tags=["files"])


@router.post("/files/temporary", response_model=UploadTemporaryFileResponse, operation_id="upload_temporary_file")
async def upload_temporary_file(
    file: UploadFile = File(...),
    purpose: Optional[str] = Form(None, description="文件用途，如 'chat_upload', 'preview' 等"),
    expiry_hours: Optional[int] = Form(None, description="过期时间（小时），默认从配置读取"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传临时文件
    
    临时文件特点：
    - 不需要关联到特定课程
    - 自动在指定时间后删除（默认从配置读取）
    - 通过唯一token访问
    - 适用于聊天上传、预览等临时用途
    """
    from app.services.unified_file_service import UnifiedFileService
    
    service = UnifiedFileService(db)
    temp_file = service.upload_temporary_file(
        file=file,
        user_id=current_user.id,
        purpose=purpose,
        expiry_hours=expiry_hours
    )
    
    # Convert to response format
    file_data = TemporaryFileResponse(
        id=temp_file.id,
        token=temp_file.token,
        original_name=temp_file.original_name,
        file_type=temp_file.file_type,
        file_size=temp_file.file_size,
        mime_type=temp_file.mime_type,
        expires_at=temp_file.expires_at,
        purpose=temp_file.purpose,
        created_at=temp_file.created_at
    )
    
    return UploadTemporaryFileResponse(
        success=True,
        data={"file": file_data.model_dump()}
    )


@router.post("/files/upload", response_model=UploadFileResponse, operation_id="upload_course_file")
async def upload_file(
    file: UploadFile = File(...),
    course_id: int = Form(...),
    folder_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload file to folder"""
    import logging
    logging.info(f"[API] Upload request - course_id: {course_id}, folder_id: {folder_id}")
    logging.info(f"[API] *** BILLING LOGIC STARTING *** - user_id: {current_user.id}")
    
    # 文件大小检查 - 使用流式处理避免内存溢出
    from app.core.config import settings
    from app.utils.file_stream_utils import check_file_size_limit
    
    is_valid, file_size = check_file_size_limit(file.file, settings.max_file_size)
    
    if not is_valid:
        raise HTTPException(
            status_code=413,
            detail=f"文件大小超过限制 ({file_size} bytes > {settings.max_file_size} bytes)"
        )
    
    # 计算文件上传费用并验证用户余额
    # 计费规则: 1 MB ≈ 0.0283 USD
    from decimal import Decimal
    
    # 计算费用: 文件大小(MB) * 单价
    file_size_mb = Decimal(str(file_size)) / Decimal('1048576')  # bytes to MB
    upload_cost = file_size_mb * Decimal('0.0283')
    
    logging.info(f"[API] File upload billing - size: {file_size} bytes ({file_size_mb} MB), cost: ${upload_cost}")
    
    # 检查用户余额是否足够
    if current_user.balance < upload_cost:
        raise HTTPException(
            status_code=402,
            detail=f"余额不足。文件大小: {file_size_mb:.2f} MB，需要: ${upload_cost:.4f}，当前余额: ${current_user.balance:.4f}"
        )
    
    # 预扣费用
    original_balance = current_user.balance
    current_user.balance -= upload_cost
    current_user.total_spent += upload_cost
    
    try:
        # 提交余额变更
        db.commit()
        logging.info(f"[API] Balance deducted - user_id: {current_user.id}, cost: ${upload_cost}, new_balance: ${current_user.balance}")
        
        service = FileService(db)
        file_record = service.upload_file(file, course_id, folder_id, current_user.id)
        
        logging.info(f"[API] File uploaded successfully - file_id: {file_record.id}, actual_folder_id: {file_record.folder_id}, charged: ${upload_cost}")
        
    except Exception as e:
        # 上传失败，回滚余额扣除
        logging.error(f"[API] File upload failed, rolling back balance - user_id: {current_user.id}, cost: ${upload_cost}")
        current_user.balance = original_balance
        current_user.total_spent -= upload_cost
        db.commit()
        raise e
    
    # Convert to response format
    file_data = FileResponse(
        id=file_record.id,
        original_name=file_record.original_name,
        file_type=file_record.file_type,
        file_size=file_record.physical_file.file_size if file_record.physical_file else 0,
        mime_type=file_record.physical_file.mime_type if file_record.physical_file else "application/octet-stream",
        course_id=file_record.course_id,
        folder_id=file_record.folder_id,
        user_id=file_record.user_id,
        is_processed=file_record.is_processed,
        processing_status=file_record.processing_status,
        created_at=file_record.created_at
    )
    
    return UploadFileResponse(
        success=True,
        data={"file": file_data.model_dump()}
    )


@router.get("/folders/{folder_id}/files", response_model=FileListResponse)
async def get_folder_files(
    folder_id: int = Path(..., description="Folder ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all files in folder"""
    import logging
    logging.info(f"Getting files for folder_id={folder_id}, user_id={current_user.id}")
    
    service = FileService(db)
    files = service.get_folder_files(folder_id, current_user.id)
    
    logging.info(f"Found {len(files)} files, starting to process...")
    
    # Convert to response format with folder info
    file_list = []
    for i, file_record in enumerate(files):
        logging.info(f"Processing file {i+1}/{len(files)}: {file_record.original_name}")
        folder_info = None
        if file_record.folder:
            folder_info = FolderInfo(
                id=file_record.folder.id,
                name=file_record.folder.name,
                folder_type=file_record.folder.folder_type
            )
        
        file_data = FileResponse(
            id=file_record.id,
            original_name=file_record.original_name,
            file_type=file_record.file_type,
            file_size=file_record.physical_file.file_size if file_record.physical_file else 0,
            mime_type=file_record.physical_file.mime_type if file_record.physical_file else "unknown",
            course_id=file_record.course_id,
            folder_id=file_record.folder_id,
            user_id=file_record.user_id,
            is_processed=file_record.is_processed,
            processing_status=file_record.processing_status,
            created_at=file_record.created_at,
            folder=folder_info
        )
        file_list.append(file_data)
        logging.info(f"Completed processing file {i+1}/{len(files)}")
    
    logging.info(f"All files processed, returning response with {len(file_list)} files")
    return FileListResponse(
        success=True,
        data={"files": [file_data.model_dump() for file_data in file_list]}
    )


@router.get("/files/{file_id}/preview", response_model=FilePreviewResponse,include_in_schema=False)
async def get_file_preview(
    file_id: int = Path(..., description="File ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get file preview information"""
    service = FileService(db)
    file_record = service.get_file_preview(file_id, current_user.id)
    
    return FilePreviewResponse(
        success=True,
        data={
            "id": file_record.id,
            "original_name": file_record.original_name,
            "file_type": file_record.file_type,
            "file_size": file_record.physical_file.file_size if file_record.physical_file else 0,
            "mime_type": file_record.physical_file.mime_type if file_record.physical_file else "unknown",
            "created_at": file_record.created_at
        }
    )


@router.get("/files/{file_id}/status",include_in_schema=False)
async def get_file_status(
    file_id: int = Path(..., description="File ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get file processing status"""
    service = FileService(db)
    file_record = service.get_file_preview(file_id, current_user.id)
    
    return {
        "success": True,
        "data": {
            "id": file_record.id,
            "original_name": file_record.original_name,
            "is_processed": file_record.is_processed,
            "processing_status": file_record.processing_status,
            "created_at": file_record.created_at,
            "rag_ready": file_record.is_processed and file_record.processing_status == "completed"
        }
    }


@router.get("/tasks/{task_id}/progress", include_in_schema=False)
async def get_task_progress(
    task_id: str = Path(..., description="Task ID"),
    current_user: User = Depends(get_current_user)
):
    """Get task progress (Beta版本: 文件同步处理)"""
    # Beta版本中文件直接同步处理，总是返回已完成状态
    return {
        "success": True,
        "data": {
            "task_id": task_id,
            "state": "SUCCESS",
            "progress": {
                "current": 100,
                "total": 100,
                "status": "文件处理已完成"
            },
            "result": {"status": "completed", "message": "Beta版本中文件同步处理完成"},
            "failed": False,
            "successful": True
        }
    }


@router.get("/files/{file_id}/download", include_in_schema=False)
async def download_file(
    file_id: int = Path(..., description="File ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download file"""
    service = FileService(db)
    file_record, file_content = service.download_file(file_id, current_user.id)
    
    # Encode filename properly for Content-Disposition header
    from urllib.parse import quote
    encoded_filename = quote(file_record.original_name.encode('utf-8'))
    
    return StreamingResponse(
        io.BytesIO(file_content),
        media_type=file_record.physical_file.mime_type if file_record.physical_file else "application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.get("/files/temporary/{token}/download", include_in_schema=False)
async def download_temporary_file(
    token: str = Path(..., description="临时文件访问token"),
    db: Session = Depends(get_db)
):
    """
    下载临时文件
    
    通过token访问临时文件，不需要登录验证
    """
    from app.services.unified_file_service import UnifiedFileService
    
    service = UnifiedFileService(db)
    temp_file, content = service.download_temporary_file(token)
    
    # Encode filename properly for Content-Disposition header
    from urllib.parse import quote
    encoded_filename = quote(temp_file.original_name.encode('utf-8'))
    
    return StreamingResponse(
        io.BytesIO(content),
        media_type=temp_file.mime_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.delete("/files/temporary/{file_id}", response_model=SuccessResponse,include_in_schema=False)
async def delete_temporary_file(
    file_id: int = Path(..., description="临时文件ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除临时文件
    
    只能删除自己上传的临时文件
    """
    from app.services.unified_file_service import UnifiedFileService
    
    service = UnifiedFileService(db)
    temp_file = service.get_temporary_file_by_id(file_id, current_user.id)
    
    if not temp_file:
        raise HTTPException(status_code=404, detail="文件不存在或已过期")
    
    success = service.delete_temporary_file(temp_file)
    if not success:
        raise HTTPException(status_code=500, detail="删除文件失败")
    
    return SuccessResponse(success=True)


@router.delete("/files/{file_id}", response_model=SuccessResponse, operation_id="delete_course_file")
async def delete_file(
    file_id: int = Path(..., description="File ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete file"""
    service = FileService(db)
    service.delete_file(file_id, current_user.id)
    
    return SuccessResponse(success=True)