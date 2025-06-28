# 文件夹与文件管理 API

## 文件夹管理

### GET /api/v1/courses/{id}/folders
- 获取课程下所有文件夹

**响应：**
```json
{
  "success": true,
  "data": {
    "folders": [
      {
        "id": 1,
        "name": "课程大纲",
        "folder_type": "outline",
        "course_id": 1,
        "is_default": true,
        "created_at": "2025-06-10T09:00:00Z",
        "stats": {
          "file_count": 1
        }
      }
    ]
  }
}
```

### POST /api/v1/courses/{id}/folders
- 新建课程文件夹

**请求体：**
```json
{
  "name": "讲座",
  "folder_type": "lecture"
}
```
**响应：**
```json
{
  "success": true,
  "data": {
    "folder": {
      "id": 2,
      "created_at": "2025-06-10T09:10:00Z"
    }
  }
}
```

---

## 文件管理

### POST /api/v1/files/upload
- 上传文件（自动去重，物理文件表+逻辑文件表）

**请求体（multipart/form-data）：**
```
file: <文件>
course_id: 1
folder_id: 2
```
**响应：**
```json
{
  "success": true,
  "data": {
    "file": {
      "id": 5,
      "original_name": "数据结构第一讲.pdf",
      "file_type": "course_material",
      "file_size": 2048000,
      "mime_type": "application/pdf",
      "course_id": 1,
      "folder_id": 2,
      "user_id": 2,
      "is_processed": false,
      "processing_status": "pending",
      "created_at": "2025-06-10T10:30:00Z"
    }
  }
}
```

### GET /api/v1/folders/{id}/files
- 获取文件夹下所有文件

**响应：**
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "id": 1,
        "original_name": "数据结构第一讲.pdf",
        "file_type": "course_material",
        "file_size": 2048000,
        "mime_type": "application/pdf",
        "course_id": 1,
        "folder_id": 2,
        "user_id": 2,
        "is_processed": true,
        "processing_status": "completed",
        "created_at": "2025-06-10T09:30:00Z",
        "folder": {
          "id": 2,
          "name": "讲座",
          "folder_type": "lecture"
        }
      }
    ]
  }
}
```

### GET /api/v1/files/{id}/download
- 下载文件

**响应：**
- 文件流响应，Content-Disposition: attachment

### GET /api/v1/files/{id}/status
- 获取文件RAG处理状态（实时状态查询）

**响应：**
```json
{
  "success": true,
  "data": {
    "id": 5,
    "original_name": "数据结构第一讲.pdf",
    "is_processed": true,
    "processing_status": "completed",
    "created_at": "2025-06-10T10:30:00Z",
    "rag_ready": true
  }
}
```

**状态说明：**
- `processing_status`:
  - `"pending"` - 等待RAG处理
  - `"processing"` - 正在分块和向量化
  - `"completed"` - RAG处理完成，可用于对话
  - `"failed"` - RAG处理失败
- `rag_ready`: 布尔值，`true`表示文件可用于RAG检索

### GET /api/v1/tasks/{task_id}/progress
- 获取异步任务处理进度（Celery任务状态）

**响应：**
```json
{
  "success": true,
  "data": {
    "task_id": "abc123-def456",
    "state": "PROGRESS",
    "progress": {
      "current": 50,
      "total": 100,
      "status": "正在分析文件内容..."
    },
    "result": null,
    "failed": false,
    "successful": false
  }
}
```

**状态说明：**
- `state`: 任务状态
  - `"PENDING"` - 等待执行
  - `"PROGRESS"` - 执行中
  - `"SUCCESS"` - 执行成功
  - `"FAILURE"` - 执行失败
- `progress`: 进度信息
  - `current`: 当前进度值
  - `total`: 总进度值
  - `status`: 当前状态描述

**前端集成指南：**
```javascript
// 异步文件上传 + 实时进度监控
const uploadFileWithProgress = async (file, courseId, folderId) => {
  // 1. 上传文件（立即返回）
  const formData = new FormData();
  formData.append('file', file);
  formData.append('course_id', courseId);
  formData.append('folder_id', folderId);
  
  const uploadResponse = await fetch('/api/v1/files/upload', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  
  const fileData = await uploadResponse.json();
  console.log('文件上传成功，开始后台处理'); // 立即响应
  
  // 2. 轮询文件状态直到完成
  return new Promise((resolve, reject) => {
    const interval = setInterval(async () => {
      try {
        const statusResponse = await fetch(`/api/v1/files/${fileData.data.file.id}/status`);
        const statusData = await statusResponse.json();
        
        // 更新UI状态
        updateFileStatus(statusData.data);
        
        if (statusData.data.rag_ready) {
          clearInterval(interval);
          resolve(fileData.data.file);
        } else if (statusData.data.processing_status === 'failed') {
          clearInterval(interval);
          reject(new Error('文件处理失败'));
        }
      } catch (error) {
        clearInterval(interval);
        reject(error);
      }
    }, 2000);
  });
};

// 使用示例
uploadFileWithProgress(file, 1, 1)
  .then(fileInfo => {
    console.log('文件可用于RAG对话！', fileInfo);
    enableChatWithFile(fileInfo.id);
  })
  .catch(error => {
    console.error('文件上传/处理失败:', error);
    showErrorMessage('文件处理失败，请重试');
  });
```

### GET /api/v1/files/{id}/preview
- 文件预览（返回文件元信息）

**响应：**
```json
{
  "success": true,
  "data": {
    "id": 5,
    "original_name": "数据结构第一讲.pdf",
    "file_type": "course_material",
    "file_size": 2048000,
    "mime_type": "application/pdf",
    "created_at": "2025-06-10T10:30:00Z"
  }
}
```

### DELETE /api/v1/files/{id}
- 删除文件

**响应：**
```json
{
  "success": true
}
```

---

## 全局文件管理（可选）

### GET /api/v1/global-files
- 获取全局文件列表

### POST /api/v1/global-files/upload
- 上传全局文件

### DELETE /api/v1/global-files/{id}
- 删除全局文件
