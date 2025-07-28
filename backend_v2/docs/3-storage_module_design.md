# Storage 模块技术设计文档 📁

## 概述

Storage模块是Campus LLM System v2的文件存储管理模块，负责文件和文件夹的完整生命周期管理。基于v1版本的成熟功能设计，采用FastAPI 2024最佳实践，提供统一的文件存储、权限控制、分享管理和RAG处理集成功能。

## 📋 业务需求分析

### 文件管理功能
- **文件CRUD**: 上传、下载、预览、删除文件
- **文件类型支持**: 文档、图片、音频、视频等多媒体文件
- **文件去重**: 基于SHA256哈希的去重策略
- **临时文件**: 支持聊天上传等临时用途的文件管理
- **文件分享**: 支持临时链接和权限共享

### 文件夹管理功能
- **文件夹CRUD**: 创建、查询、更新、删除文件夹
- **层级结构**: 支持课程级别的文件夹分类
- **文件夹类型**: outline、tutorial、lecture、exam、assignment、others
- **统计信息**: 文件数量、存储大小统计

### 权限控制系统
- **作用域管理**: course、global、personal三种作用域
- **可见性控制**: private、course、public三种可见性
- **用户权限**: 基于用户和课程的访问控制
- **访问审计**: 文件访问日志记录和分析

### RAG集成功能
- **文件处理**: 自动或手动触发RAG处理
- **状态跟踪**: 处理进度和状态监控
- **内容提取**: 文本预览和向量化处理
- **错误处理**: 处理失败的错误记录和重试

## 🗄️ 数据模型设计

### 1. File 模型（基于v1扩展）
```python
class File(Base):
    __tablename__ = "files"
    
    # === 基础字段 ===
    id = Column(Integer, primary_key=True, index=True)
    physical_file_id = Column(Integer, ForeignKey("physical_files.id"), nullable=False, index=True)
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    
    # === 作用域和归属（统一管理核心）===
    scope = Column(String(20), nullable=False, default='course', index=True)
    # scope 取值: 'course', 'global', 'personal'
    
    visibility = Column(String(20), default='private', index=True)
    # visibility 取值: 'private', 'course', 'public'
    
    # === 关联字段 ===
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # === 文件元数据 ===
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_hash = Column(String(64), nullable=True, index=True)  # SHA256去重
    
    # === 访问控制 ===
    is_downloadable = Column(Boolean, default=True)
    access_settings = Column(JSON, nullable=True)  # 存储访问控制配置
    
    # === RAG处理相关 ===
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(20), default="pending")
    processing_error = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    chunk_count = Column(Integer, default=0)
    content_preview = Column(Text, nullable=True)
    
    # === 时间戳 ===
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # === 复合索引优化 ===
    __table_args__ = (
        Index('idx_scope_visibility', scope, visibility),
        Index('idx_owner_course', user_id, course_id),
        Index('idx_file_hash', file_hash),
    )
    
    # === 关系定义 ===
    physical_file = relationship("PhysicalFile", back_populates="files")
    folder = relationship("Folder", back_populates="files")
    course = relationship("Course", back_populates="files")
    user = relationship("User", back_populates="files")
    access_logs = relationship("FileAccessLog", back_populates="file", cascade="all, delete-orphan")
    document_chunks = relationship("DocumentChunk", back_populates="file", cascade="all, delete-orphan")
    message_references = relationship("MessageFileReference", back_populates="file")
```

### 2. Folder 模型（继承v1设计）
```python
class Folder(Base):
    __tablename__ = "folders"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    folder_type = Column(String(20), nullable=False)  # outline, tutorial, lecture, exam, assignment, others
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # 新增所有者
    is_default = Column(Boolean, default=False)
    description = Column(Text, nullable=True)  # 新增描述
    
    # === 时间戳 ===
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # === 关系定义 ===
    course = relationship("Course", back_populates="folders")
    user = relationship("User", back_populates="folders")
    files = relationship("File", back_populates="folder")
```

### 3. PhysicalFile 模型（物理存储）
```python
class PhysicalFile(Base):
    __tablename__ = "physical_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, unique=True)  # 系统生成的唯一文件名
    file_hash = Column(String(64), nullable=False, unique=True, index=True)  # SHA256哈希
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    storage_path = Column(String(500), nullable=False)  # 实际存储路径
    
    # === 引用计数（去重支持）===
    ref_count = Column(Integer, default=1)  # 被引用的次数
    
    # === 时间戳 ===
    created_at = Column(DateTime, server_default=func.now())
    
    # === 关系定义 ===
    files = relationship("File", back_populates="physical_file")
    temporary_files = relationship("TemporaryFile", back_populates="physical_file")
```

### 4. TemporaryFile 模型（临时文件）
```python
class TemporaryFile(Base):
    __tablename__ = "temporary_files"
    
    id = Column(Integer, primary_key=True, index=True)
    physical_file_id = Column(Integer, ForeignKey("physical_files.id"), nullable=False)
    token = Column(String(36), nullable=False, unique=True, index=True)  # UUID访问令牌
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    # === 临时文件特定字段 ===
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    purpose = Column(String(50), nullable=True)  # chat_upload, preview, etc.
    expires_at = Column(DateTime, nullable=False, index=True)
    
    # === 时间戳 ===
    created_at = Column(DateTime, server_default=func.now())
    
    # === 关系定义 ===
    physical_file = relationship("PhysicalFile", back_populates="temporary_files")
    user = relationship("User", back_populates="temporary_files")
```

### 5. FileAccessLog 模型（访问日志）
```python
class FileAccessLog(Base):
    __tablename__ = "file_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # === 访问信息 ===
    action = Column(String(20), nullable=False)  # view, download, preview, upload
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # === 访问方式 ===
    access_method = Column(String(20), nullable=False)  # direct, api, temporary
    session_info = Column(JSON, nullable=True)  # 会话相关信息
    
    # === 时间戳 ===
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    # === 关系定义 ===
    file = relationship("File", back_populates="access_logs")
    user = relationship("User", back_populates="file_access_logs")
```

## 🚀 API 接口设计

### 路由前缀和标签
- **前缀**: `/storage`
- **标签**: `["文件存储"]` (在 main.py 中设置)
- **权限**: 基于文件所有权和可见性的细粒度权限控制

### 文件管理接口

#### 1. POST /api/v1/storage/files/upload - 上传文件
```python
# 兼容v1 API: POST /files/upload
Request: FormData
- file: UploadFile
- course_id: int
- folder_id: int
- description?: str
- tags?: List[str]
- scope?: str = "course"
- visibility?: str = "private"

Response 201: CreateFileResponse
{
  "success": true,
  "data": {
    "file": {
      "id": 1,
      "original_name": "document.pdf",
      "file_type": "pdf",
      "file_size": 1024000,
      "mime_type": "application/pdf",
      "file_hash": "sha256...",
      "course_id": 1,
      "folder_id": 1,
      "user_id": 1,
      "scope": "course",
      "visibility": "private",
      "is_processed": false,
      "processing_status": "pending",
      "created_at": "2025-01-27T10:00:00Z"
    }
  },
  "message": "文件上传成功"
}

Errors: 400(文件无效), 403(权限不足), 409(文件已存在), 413(文件过大)
```

#### 2. POST /api/v1/storage/files/temporary - 上传临时文件
```python
# 兼容v1 API: POST /files/temporary
Request: FormData
- file: UploadFile
- purpose?: str = "chat_upload"
- expiry_hours?: int = 24

Response 201: CreateTemporaryFileResponse
{
  "success": true,
  "data": {
    "file": {
      "id": 1,
      "token": "uuid-token-here",
      "original_name": "temp.jpg",
      "file_type": "jpg",
      "file_size": 500000,
      "mime_type": "image/jpeg",
      "purpose": "chat_upload",
      "expires_at": "2025-01-28T10:00:00Z",
      "created_at": "2025-01-27T10:00:00Z"
    }
  },
  "message": "临时文件上传成功"
}
```

#### 3. GET /api/v1/storage/files/{file_id} - 获取文件详情
```python
# 兼容v1 API: GET /files/{file_id}/preview
Response 200: FileDetailResponse
{
  "success": true,
  "data": {
    "file": {
      "id": 1,
      "original_name": "document.pdf",
      "file_type": "pdf",
      "file_size": 1024000,
      "mime_type": "application/pdf",
      "description": "课程文档",
      "tags": ["lecture", "important"],
      "scope": "course",
      "visibility": "private",
      "course_id": 1,
      "folder_id": 1,
      "user_id": 1,
      "is_processed": true,
      "processing_status": "completed",
      "chunk_count": 15,
      "content_preview": "文档内容预览...",
      "created_at": "2025-01-27T10:00:00Z",
      "updated_at": "2025-01-27T11:00:00Z",
      "folder": {
        "id": 1,
        "name": "Lecture Notes",
        "folder_type": "lecture"
      },
      "stats": {
        "view_count": 25,
        "download_count": 5,
        "share_count": 2
      }
    }
  }
}

Errors: 404(文件不存在), 403(无访问权限)
```

#### 4. GET /api/v1/storage/files/{file_id}/download - 下载文件
```python
# 兼容v1 API: GET /files/{file_id}/download
Response: StreamingResponse
Content-Type: application/pdf
Content-Disposition: attachment; filename*=UTF-8''document.pdf

Errors: 404(文件不存在), 403(无下载权限)
```

#### 5. PUT /api/v1/storage/files/{file_id} - 更新文件信息
```python
Request: UpdateFileRequest
{
  "original_name": "new-name.pdf",
  "description": "更新的描述",
  "tags": ["updated", "important"],
  "visibility": "course"
}

Response 200: UpdateFileResponse
{
  "success": true,
  "data": {
    "file": {
      // 更新后的文件信息
    }
  },
  "message": "文件信息更新成功"
}
```

#### 6. DELETE /api/v1/storage/files/{file_id} - 删除文件
```python
# 兼容v1 API: DELETE /files/{file_id}
Response 200: MessageResponse
{
  "success": true,
  "data": {"message": "文件删除成功"}
}

Errors: 404(文件不存在), 403(无删除权限), 409(文件被引用)
```

### 文件夹管理接口

#### 1. GET /api/v1/storage/courses/{course_id}/folders - 获取课程文件夹
```python
# 兼容v1 API: GET /courses/{course_id}/folders
Response 200: FolderListResponse
{
  "success": true,
  "data": {
    "folders": [
      {
        "id": 1,
        "name": "Lecture Notes",
        "folder_type": "lecture",
        "course_id": 1,
        "user_id": 1,
        "is_default": false,
        "description": "课程讲义文件夹",
        "created_at": "2025-01-27T10:00:00Z",
        "stats": {
          "file_count": 15,
          "total_size": 50000000
        }
      }
    ],
    "total": 1
  }
}
```

#### 2. POST /api/v1/storage/courses/{course_id}/folders - 创建文件夹
```python
# 兼容v1 API: POST /courses/{course_id}/folders
Request: CreateFolderRequest
{
  "name": "Assignment Files",
  "folder_type": "assignment",
  "description": "作业文件存储"
}

Response 201: CreateFolderResponse
{
  "success": true,
  "data": {
    "folder": {
      "id": 2,
      "name": "Assignment Files",
      "folder_type": "assignment",
      "course_id": 1,
      "user_id": 1,
      "created_at": "2025-01-27T10:00:00Z"
    }
  },
  "message": "文件夹创建成功"
}
```

#### 3. GET /api/v1/storage/folders/{folder_id}/files - 获取文件夹内文件
```python
# 兼容v1 API: GET /folders/{folder_id}/files
Query Parameters:
- skip?: int = 0
- limit?: int = 100
- file_type?: str (过滤文件类型)
- processed_only?: bool = false (只显示已处理的文件)

Response 200: FolderFilesResponse
{
  "success": true,
  "data": {
    "files": [
      // FileResponse 数组
    ],
    "folder": {
      "id": 1,
      "name": "Lecture Notes",
      "folder_type": "lecture"
    },
    "total": 15,
    "pagination": {
      "skip": 0,
      "limit": 100,
      "has_more": false
    }
  }
}
```


### RAG处理接口

#### 1. POST /api/v1/storage/files/{file_id}/process - 触发RAG处理
```python
Request: ProcessFileRequest
{
  "force_reprocess": false,
  "processing_options": {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "extract_images": true
  }
}

Response 202: ProcessFileResponse
{
  "success": true,
  "data": {
    "task_id": "uuid-task-id",
    "processing_status": "queued",
    "estimated_time": 300
  },
  "message": "文件已加入处理队列"
}
```

#### 2. GET /api/v1/storage/files/{file_id}/processing-status - 获取处理状态
```python
# 兼容v1 API: GET /files/{file_id}/status
Response 200: ProcessingStatusResponse
{
  "success": true,
  "data": {
    "file_id": 1,
    "is_processed": false,
    "processing_status": "processing",
    "progress": 45,
    "chunk_count": 8,
    "processing_error": null,
    "started_at": "2025-01-27T10:00:00Z",
    "estimated_completion": "2025-01-27T10:05:00Z"
  }
}
```

## 📊 Schema 设计（FastAPI 2024最佳实践）

### 请求模型
```python
# === 文件相关请求 ===
class CreateFileRequest(BaseModel):
    course_id: int = Field(..., gt=0, description="课程ID")
    folder_id: int = Field(..., gt=0, description="文件夹ID")
    description: Optional[str] = Field(None, max_length=500, description="文件描述")
    tags: Optional[List[str]] = Field(None, description="文件标签")
    scope: str = Field("course", description="文件作用域", regex="^(course|global|personal|shared)$")
    visibility: str = Field("private", description="可见性", regex="^(private|course|public|shared)$")

class UpdateFileRequest(BaseModel):
    original_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = Field(None, max_items=10)
    visibility: Optional[str] = Field(None, regex="^(private|course|public|shared)$")

# === 文件夹相关请求 ===
class CreateFolderRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="文件夹名称")
    folder_type: str = Field(..., description="文件夹类型", 
                           regex="^(outline|tutorial|lecture|exam|assignment|others)$")
    description: Optional[str] = Field(None, max_length=500, description="文件夹描述")

class UpdateFolderRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    folder_type: Optional[str] = Field(None, regex="^(outline|tutorial|lecture|exam|assignment|others)$")
    description: Optional[str] = Field(None, max_length=500)

# === RAG处理请求 ===
class ProcessFileRequest(BaseModel):
    force_reprocess: bool = Field(False, description="强制重新处理")
    processing_options: Optional[Dict[str, Any]] = Field(None, description="处理选项")
```

### 响应模型（遵循BaseResponse[T]模式）
```python
# === 文件数据模型 ===
class FileData(BaseModel):
    id: int
    original_name: str
    file_type: str
    file_size: Optional[int]
    mime_type: Optional[str]
    file_hash: Optional[str]
    description: Optional[str]
    tags: Optional[List[str]]
    scope: str
    visibility: str
    course_id: Optional[int]
    folder_id: Optional[int]
    user_id: int
    is_downloadable: bool
    is_processed: bool
    processing_status: str
    processing_error: Optional[str]
    processed_at: Optional[datetime]
    chunk_count: int
    content_preview: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # 关联数据
    folder: Optional[FolderBasicData] = None
    stats: Optional[FileStatsData] = None

class FileStatsData(BaseModel):
    view_count: int
    download_count: int
    share_count: int

class FolderBasicData(BaseModel):
    id: int
    name: str
    folder_type: str

# === 文件夹数据模型 ===
class FolderData(BaseModel):
    id: int
    name: str
    folder_type: str
    course_id: int
    user_id: int
    is_default: bool
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    stats: Optional[FolderStatsData] = None

class FolderStatsData(BaseModel):
    file_count: int
    total_size: int
    processed_file_count: int

# === 临时文件数据模型 ===
class TemporaryFileData(BaseModel):
    id: int
    token: str
    original_name: str
    file_type: str
    file_size: int
    mime_type: str
    purpose: Optional[str]
    expires_at: datetime
    created_at: datetime

# === 响应模型 ===
class CreateFileResponse(BaseResponse[Dict]):
    # data.file: FileData
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "success": True,
                "data": {
                    "file": {
                        "id": 1,
                        "original_name": "document.pdf",
                        "file_type": "pdf",
                        "file_size": 1024000,
                        "mime_type": "application/pdf",
                        "scope": "course",
                        "visibility": "private",
                        "created_at": "2025-01-27T10:00:00Z"
                    }
                },
                "message": "文件上传成功"
            }]
        }
    )

class FileListResponse(BaseResponse[Dict]):
    # data.files: List[FileData], data.total: int, data.pagination: PaginationInfo

class FolderListResponse(BaseResponse[Dict]):
    # data.folders: List[FolderData], data.total: int
```

## 🛠️ Service 层设计

### StorageService 类设计
```python
class StorageService:
    """存储服务 - 统一的文件和文件夹管理"""
    
    METHOD_EXCEPTIONS = {
        # 文件管理
        'upload_file': {BadRequestError, ForbiddenError, ConflictError, PayloadTooLargeError},
        'get_file': {NotFoundError, ForbiddenError},
        'update_file': {NotFoundError, ForbiddenError, BadRequestError},
        'delete_file': {NotFoundError, ForbiddenError, ConflictError},
        'download_file': {NotFoundError, ForbiddenError},
        
        # 文件夹管理
        'create_folder': {BadRequestError, ForbiddenError, ConflictError},
        'get_folder_files': {NotFoundError, ForbiddenError},
        'update_folder': {NotFoundError, ForbiddenError, BadRequestError},
        'delete_folder': {NotFoundError, ForbiddenError, ConflictError},
        
        # 临时文件
        'upload_temporary_file': {BadRequestError, PayloadTooLargeError},
        'get_temporary_file': {NotFoundError, UnauthorizedError},
        'delete_temporary_file': {NotFoundError, ForbiddenError},
        
        # RAG处理
        'process_file': {NotFoundError, ForbiddenError, BadRequestError},
        'get_processing_status': {NotFoundError, ForbiddenError},
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.file_storage = LocalFileStorage()  # 或 CloudFileStorage()
```

### 核心业务方法示例
```python
def upload_file(
    self, 
    file: UploadFile, 
    request: CreateFileRequest, 
    user_id: int
) -> Dict[str, Any]:
    """上传文件"""
    # 1. 权限检查
    if not self._can_upload_to_course(user_id, request.course_id):
        raise ForbiddenError("无权限上传文件到此课程")
    
    # 2. 文件验证
    if file.size > settings.max_file_size:
        raise PayloadTooLargeError(f"文件大小超过限制 {settings.max_file_size} bytes")
    
    # 3. 计算文件哈希
    file_hash = self._calculate_file_hash(file.file)
    
    # 4. 检查文件去重
    existing_physical = self.db.query(PhysicalFile).filter(
        PhysicalFile.file_hash == file_hash
    ).first()
    
    if existing_physical:
        # 增加引用计数
        existing_physical.ref_count += 1
        physical_file = existing_physical
    else:
        # 存储新文件
        storage_path = self.file_storage.save_file(file.file, file.filename)
        physical_file = PhysicalFile(
            filename=self._generate_unique_filename(file.filename),
            file_hash=file_hash,
            file_size=file.size,
            mime_type=file.content_type,
            storage_path=storage_path,
            ref_count=1
        )
        self.db.add(physical_file)
    
    # 5. 创建文件记录
    file_record = File(
        physical_file_id=physical_file.id,
        original_name=file.filename,
        file_type=self._extract_file_type(file.filename),
        description=request.description,
        tags=request.tags,
        scope=request.scope,
        visibility=request.visibility,
        course_id=request.course_id,
        folder_id=request.folder_id,
        user_id=user_id,
        file_size=file.size,
        mime_type=file.content_type,
        file_hash=file_hash
    )
    
    self.db.add(file_record)
    self.db.commit()
    self.db.refresh(file_record)
    
    # 6. 异步触发RAG处理
    if self._should_process_for_rag(file_record):
        self._queue_rag_processing(file_record.id)
    
    return {
        "file": file_record,
        "message": "文件上传成功"
    }

```

## 🔐 权限控制设计

### 权限模型
```python
# storage/dependencies.py
def get_file_permission(
    action: str  # read, write, delete, download
) -> Callable:
    """文件权限检查装饰器"""
    def permission_check(
        file_id: int,
        current_user: UserDep,
        db: DbDep
    ) -> File:
        service = StorageService(db)
        file_record = service.get_file_with_permission(file_id, current_user.id, action)
        return file_record
    
    return permission_check

# 权限检查类型别名
FileReadDep = Annotated[File, Depends(get_file_permission("read"))]
FileWriteDep = Annotated[File, Depends(get_file_permission("write"))]
FileDeleteDep = Annotated[File, Depends(get_file_permission("delete"))]
```

### 权限检查逻辑
```python
def _check_file_permission(self, file: File, user_id: int, action: str) -> bool:
    """检查文件权限"""
    # 1. 文件所有者
    if file.user_id == user_id:
        return True
    
    # 2. 公开文件的读取权限
    if action == "read" and file.visibility == "public":
        return True
    
    # 3. 课程成员的权限
    if file.scope == "course" and file.visibility == "course":
        if self._is_course_member(user_id, file.course_id):
            return action in ["read", "download"]
    
    # 4. 管理员权限
    if self._is_admin(user_id):
        return True
    
    return False
```

## 📁 文件系统结构

### 项目结构
```
src/storage/
├── __init__.py
├── models.py          # File, Folder, PhysicalFile, TemporaryFile, FileAccessLog
├── schemas.py         # 请求/响应模型
├── service.py         # StorageService (统一文件和文件夹管理)
├── router.py          # API 路由
├── dependencies.py    # 权限检查依赖
├── exceptions.py      # 存储相关异常
└── utils.py          # 文件处理工具函数

src/storage/services/
├── __init__.py
├── file_storage.py    # 物理文件存储抽象接口
├── local_storage.py   # 本地文件存储实现
├── cloud_storage.py   # 云存储实现（可选）
└── rag_processor.py   # RAG处理服务
```

## 🧪 测试策略

### 单元测试覆盖
```python
class TestStorageService:
    """存储服务单元测试"""
    
    def test_upload_file_success(self, storage_service, test_file, regular_user):
        """测试文件上传成功"""
        
    def test_upload_file_deduplication(self, storage_service, test_file, regular_user):
        """测试文件去重功能"""
        
    def test_file_permission_check(self, storage_service, sample_file, regular_user):
        """测试文件权限检查"""

class TestStorageAPI:
    """存储API集成测试"""
    
    def test_upload_file_api(self, client, user_headers, test_file):
        """测试文件上传API"""
        
    def test_folder_file_listing(self, client, user_headers, sample_folder):
        """测试文件夹文件列表"""
```

## 🚀 性能优化

### 文件存储优化
- **去重策略**: SHA256哈希去重，节省存储空间
- **分片上传**: 大文件分片上传支持
- **缓存策略**: 文件元数据和权限信息缓存
- **CDN集成**: 静态文件CDN加速

### 数据库优化
- **复合索引**: scope+visibility, user_id+course_id, file_hash
- **分页查询**: 文件列表分页加载
- **预加载优化**: 关联查询优化，避免N+1问题

### 异步处理
- **RAG处理**: 异步文件内容处理和向量化
- **文件清理**: 定期清理过期临时文件和无引用物理文件
- **访问日志**: 异步记录文件访问日志

## 🔗 与其他模块的集成

### Course 模块集成
- 文件归属课程验证
- 课程成员权限继承
- 课程文件统计

### Chat 模块集成
- 临时文件上传支持
- 聊天文件附件管理
- 文件引用和预览

### AI 模块集成
- RAG处理状态同步
- 文档向量化触发
- 处理结果存储

### Admin 模块集成
- 全局文件管理
- 存储空间统计
- 文件审计日志

## 📊 监控和统计

### 存储统计
- 用户存储使用量
- 文件类型分布
- 上传下载统计
- 分享使用统计

### 性能监控
- 文件上传速度
- 下载响应时间
- RAG处理效率
- 存储空间使用率

## 🎯 总结

Storage模块严格遵循FastAPI 2024最佳实践和Campus LLM System的架构标准：

- ✅ **Service API装饰器**: 自动生成完整的OpenAPI文档
- ✅ **统一响应格式**: BaseResponse[T]泛型设计，message/data分离
- ✅ **现代依赖注入**: 类型安全的权限控制
- ✅ **异常处理自动化**: METHOD_EXCEPTIONS声明
- ✅ **v1 API兼容**: 保持API路径和响应格式兼容
- ✅ **完整测试覆盖**: 单元测试+API集成测试
- ✅ **安全性设计**: 细粒度权限控制+文件去重+访问日志

该模块为Campus LLM System提供了强大、安全、高效的文件存储解决方案，支持RAG集成和完善的权限控制，确保了优秀的用户体验和系统性能。