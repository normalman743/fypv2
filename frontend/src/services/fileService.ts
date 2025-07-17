import api from './api';

export interface FileItem {
  id: number;
  name: string;
  description?: string;
  tags?: string;
  visibility: string;
  created_at: string;
  updated_at: string;
  owner_id: number;
  course_id?: number;
  folder_id?: number;
}

export interface UploadFileRequest {
  file: File;
  scope?: string;
  course_id?: number;
  folder_id?: number;
  description?: string;
  tags?: string;
  visibility?: string;
}

export class FileService {
  // 获取文件列表
  static async getFiles(params?: {
    scope?: string;
    course_id?: number;
    include_shared?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<FileItem[]> {
    const res = await api.get('/api/v1/files', { params });
    return res.data.data.files;
  }

  // 获取文件详情
  static async getFileDetail(file_id: number): Promise<FileItem> {
    const res = await api.get(`/api/v1/files/${file_id}`);
    return res.data.data;
  }

  // 上传文件
  static async uploadFile(data: UploadFileRequest): Promise<FileItem> {
    const formData = new FormData();
    formData.append('file', data.file);
    if (data.scope) formData.append('scope', data.scope);
    if (data.course_id) formData.append('course_id', String(data.course_id));
    if (data.folder_id) formData.append('folder_id', String(data.folder_id));
    if (data.description) formData.append('description', data.description);
    if (data.tags) formData.append('tags', data.tags);
    if (data.visibility) formData.append('visibility', data.visibility);
    const res = await api.post('/api/v1/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data.data.file;
  }

  // 下载文件
  static async downloadFile(file_id: number): Promise<Blob> {
    const res = await api.get(`/api/v1/files/${file_id}/download`, {
      responseType: 'blob',
    });
    return res.data;
  }

  // 删除文件
  static async deleteFile(file_id: number): Promise<void> {
    await api.delete(`/api/v1/files/${file_id}`);
  }

  // 共享文件
  static async shareFile(file_id: number, data: {
    shared_with_type: string;
    shared_with_id?: number;
    permission_level?: string;
    can_reshare?: boolean;
    expires_at?: string;
  }): Promise<any> {
    const res = await api.post(`/api/v1/files/${file_id}/share`, data);
    return res.data.data;
  }

  // 获取文件访问日志
  static async getFileAccessLogs(file_id: number, params?: { skip?: number; limit?: number }): Promise<any> {
    const res = await api.get(`/api/v1/files/${file_id}/access-logs`, { params });
    return res.data.data.logs;
  }
}
