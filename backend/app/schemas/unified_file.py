from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.schemas.common import BaseResponse

# 物理文件模型 - 对应 physical_files 表
class PhysicalFileResponse(BaseModel):
    """物理文件模型 - 映射 physical_files 表"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    file_hash: str
    file_size: int
    mime_type: str
    storage_path: str
    first_uploaded_at: datetime
    reference_count: int = 0

# 业务文件信息模型 - 对应 files 表
class FileDetailData(BaseModel):
    """业务文件信息模型 - 当前正在使用，对应 files 表"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    original_name: str
    file_type: str
    scope: str
    visibility: str
    course_id: Optional[int]
    folder_id: Optional[int]
    owner_id: int
    is_processed: bool
    processing_status: str
    processing_error: Optional[str] = None
    processed_at: Optional[datetime] = None
    chunk_count: Optional[int] = None
    content_preview: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    file_size: int
    file_hash: str
    description: Optional[str] = None
    tags: List[str] = []
    is_owner: bool
    is_shareable: Optional[bool] = None

class FileUploadData(BaseModel):
    file: Dict[str, Any]

class FileListData(BaseModel):
    files: List[Dict[str, Any]]
    pagination: Dict[str, Any]

class FileAccessLogData(BaseModel):
    logs: List[Dict[str, Any]]
    pagination: Dict[str, Any]

class FileShareData(BaseModel):
    share: Dict[str, Any]

# API响应模型
class FileUploadResponse(BaseResponse):
    success: bool = True
    data: FileUploadData

class FileListResponse(BaseResponse):
    success: bool = True
    data: FileListData

class FileDetailResponse(BaseResponse):
    success: bool = True
    data: Dict[str, Any]

class FileAccessLogResponse(BaseResponse):
    success: bool = True
    data: FileAccessLogData

class FileShareResponse(BaseResponse):
    success: bool = True
    data: FileShareData

class FileDeleteResponse(BaseResponse):
    success: bool = True
    data: Dict[str, str]

# 物理文件响应模型
class PhysicalFileListResponse(BaseResponse):
    success: bool = True
    data: Dict[str, Any]  # {"physical_files": List[PhysicalFileResponse]}

class PhysicalFileDetailResponse(BaseResponse):
    success: bool = True
    data: Dict[str, Any]  # {"physical_file": PhysicalFileResponse}