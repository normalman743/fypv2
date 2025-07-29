"""Storage模块Pydantic Schema定义"""
from pydantic import BaseModel, ConfigDict, Field, validator
from typing import Optional, List, Literal
from datetime import datetime
from src.shared.schemas import BaseResponse


# ===== 文件夹相关Schema =====

class FolderBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="文件夹名称")
    folder_type: Literal["outline", "tutorial", "lecture", "exam", "assignment", "others"] = Field(
        ..., description="文件夹类型"
    )


class CreateFolderRequest(FolderBase):
    """创建文件夹请求"""
    pass


class UpdateFolderRequest(BaseModel):
    """更新文件夹请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="文件夹名称")
    folder_type: Optional[Literal["outline", "tutorial", "lecture", "exam", "assignment", "others"]] = Field(
        None, description="文件夹类型"
    )


class FolderStats(BaseModel):
    """文件夹统计信息"""
    file_count: int = Field(0, description="文件数量")


class FolderInfo(BaseModel):
    """文件夹基本信息"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    folder_type: str


class FolderResponse(FolderBase):
    """文件夹响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    course_id: int
    is_default: bool = False
    created_at: datetime
    stats: FolderStats


class FolderListData(BaseModel):
    """文件夹列表数据"""
    folders: List[FolderResponse]


class FolderListResponse(BaseResponse[FolderListData]):
    """文件夹列表响应"""
    pass


class CreateFolderData(BaseModel):
    """创建文件夹响应数据"""
    folder: dict  # {"id": int, "created_at": datetime}


class CreateFolderResponse(BaseResponse[CreateFolderData]):
    """创建文件夹响应"""
    pass


# ===== 文件相关Schema =====

class FileBase(BaseModel):
    original_name: str = Field(..., max_length=255, description="原始文件名")
    description: Optional[str] = Field(None, description="文件描述")
    tags: Optional[List[str]] = Field(None, description="文件标签")


class FileResponse(BaseModel):
    """文件响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    physical_file_id: int
    original_name: str
    file_type: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    course_id: Optional[int] = None
    folder_id: Optional[int] = None
    user_id: int
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    
    # 作用域和可见性
    scope: str = "course"
    visibility: str = "private"
    is_shareable: bool = True
    share_settings: Optional[dict] = None
    
    # RAG处理相关
    is_processed: bool = False
    processing_status: str = "pending"
    processing_error: Optional[str] = None
    processed_at: Optional[datetime] = None
    chunk_count: int = 0
    content_preview: Optional[str] = None
    
    # 时间戳
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # 关联信息
    folder: Optional[FolderInfo] = None


class FileListData(BaseModel):
    """文件列表数据"""
    files: List[FileResponse]


class FileListResponse(BaseResponse[FileListData]):
    """文件列表响应"""
    pass


class UploadFileData(BaseModel):
    """上传文件响应数据"""
    file: FileResponse


class UploadFileResponse(BaseResponse[UploadFileData]):
    """上传文件响应"""
    pass


# ===== 临时文件相关Schema =====

class TemporaryFileResponse(BaseModel):
    """临时文件响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    filename: str
    file_size: int
    mime_type: Optional[str] = None
    user_id: int
    expires_at: datetime
    created_at: datetime


class UploadTemporaryFileData(BaseModel):
    """上传临时文件响应数据"""
    file: TemporaryFileResponse


class UploadTemporaryFileResponse(BaseResponse[UploadTemporaryFileData]):
    """上传临时文件响应"""
    pass


# ===== 全局文件相关Schema =====

class GlobalFileResponse(FileResponse):
    """全局文件响应"""
    pass


class GlobalFileListData(BaseModel):
    """全局文件列表数据"""
    files: List[GlobalFileResponse]
    total: int


class GlobalFileListResponse(BaseResponse[GlobalFileListData]):
    """全局文件列表响应"""
    pass


# ===== 文件分享相关Schema =====

class FileShareResponse(BaseModel):
    """文件分享响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    file_id: int
    user_id: int
    share_token: str
    expires_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime


class CreateFileShareRequest(BaseModel):
    """创建文件分享请求"""
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class CreateFileShareData(BaseModel):
    """创建文件分享响应数据"""
    share: FileShareResponse


class CreateFileShareResponse(BaseResponse[CreateFileShareData]):
    """创建文件分享响应"""
    pass


# ===== 文件访问日志Schema =====

class FileAccessLogResponse(BaseModel):
    """文件访问日志响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    file_id: int
    user_id: Optional[int] = None
    access_type: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    accessed_at: datetime