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
    FolderInfo
)
from app.schemas.common import SuccessResponse
from app.models.user import User

router = APIRouter(tags=["files"])


@router.post("/files/upload", response_model=UploadFileResponse)
async def upload_file(
    file: UploadFile = File(...),
    course_id: int = Form(...),
    folder_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload file to folder"""
    service = FileService(db)
    file_record = service.upload_file(file, course_id, folder_id, current_user.id)
    
    # Convert to response format
    file_data = FileResponse(
        id=file_record.id,
        original_name=file_record.original_name,
        file_type=file_record.file_type,
        file_size=file_record.file_size,
        mime_type=file_record.mime_type,
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
    service = FileService(db)
    files = service.get_folder_files(folder_id, current_user.id)
    
    # Convert to response format with folder info
    file_list = []
    for file_record in files:
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
            file_size=file_record.file_size,
            mime_type=file_record.mime_type,
            course_id=file_record.course_id,
            folder_id=file_record.folder_id,
            user_id=file_record.user_id,
            is_processed=file_record.is_processed,
            processing_status=file_record.processing_status,
            created_at=file_record.created_at,
            folder=folder_info
        )
        file_list.append(file_data)
    
    return FileListResponse(
        success=True,
        data={"files": [file_data.model_dump() for file_data in file_list]}
    )


@router.get("/files/{file_id}/preview", response_model=FilePreviewResponse)
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
            "file_size": file_record.file_size,
            "mime_type": file_record.mime_type,
            "created_at": file_record.created_at
        }
    )


@router.get("/files/{file_id}/status")
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


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: int = Path(..., description="File ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download file"""
    service = FileService(db)
    file_record = service.download_file(file_id, current_user.id)
    
    # TODO: Implement actual file serving from storage
    # For now, return a placeholder response
    fake_content = f"Content of {file_record.original_name}".encode()
    
    # Encode filename properly for Content-Disposition header
    from urllib.parse import quote
    encoded_filename = quote(file_record.original_name.encode('utf-8'))
    
    return StreamingResponse(
        io.BytesIO(fake_content),
        media_type=file_record.mime_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.delete("/files/{file_id}", response_model=SuccessResponse)
async def delete_file(
    file_id: int = Path(..., description="File ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete file"""
    service = FileService(db)
    service.delete_file(file_id, current_user.id)
    
    return SuccessResponse(success=True)