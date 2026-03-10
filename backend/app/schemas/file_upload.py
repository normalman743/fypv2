from pydantic import BaseModel
from typing import Optional, List, Literal
from fastapi import UploadFile, Form

# 为了清理复杂的Body类型名称，我们可以创建明确的请求模型
# 但由于FastAPI对multipart/form-data的处理方式，
# 这些Body类型名称是不可避免的

# 我们可以通过使用operation_id来使API文档更清晰
# 并在API文档中提供清晰的参数说明

class FileUploadFormData(BaseModel):
    """文件上传表单数据模型（仅用于文档说明）"""
    file: str  # UploadFile对象
    course_id: int
    folder_id: int
    
class UnifiedFileUploadFormData(BaseModel):
    """统一文件上传表单数据模型（仅用于文档说明）"""
    file: str  # UploadFile对象
    scope: str = 'course'
    course_id: Optional[int] = None
    folder_id: Optional[int] = None
    description: Optional[str] = None
    tags: Optional[str] = None  # JSON string
    visibility: str = 'private'

class GlobalFileUploadFormData(BaseModel):
    """全局文件上传表单数据模型（仅用于文档说明）"""
    file: str  # UploadFile对象
    description: Optional[str] = None
    tags: Optional[str] = None  # JSON string
    visibility: str = 'public'

class FileShareFormData(BaseModel):
    """文件共享表单数据模型（仅用于文档说明）"""
    shared_with_type: str  # 'user', 'course', 'group', 'public'
    shared_with_id: Optional[int] = None
    permission_level: str = 'read'  # 'read', 'comment', 'edit', 'manage'
    can_reshare: bool = False
    expires_at: Optional[str] = None