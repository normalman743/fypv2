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

**前端轮询建议：**
```javascript
// 文件上传后轮询状态，直到rag_ready=true
const pollStatus = async (fileId) => {
  const interval = setInterval(async () => {
    const response = await fetch(`/api/v1/files/${fileId}/status`);
    const data = await response.json();
    
    if (data.data.rag_ready) {
      console.log('文件可用于RAG对话！');
      clearInterval(interval);
    }
  }, 2000); // 每2秒检查一次
};
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
