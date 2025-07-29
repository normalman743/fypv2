"""
Campus LLM System v2 - API客户端封装
用于End-to-End测试的完整API客户端实现
"""
import requests
import json
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class APIException(Exception):
    """API请求异常"""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class CampusLLMClient:
    """Campus LLM System v2 API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8001", debug: bool = False):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.access_token: Optional[str] = None
        self.debug = debug
        
        # 设置默认请求头
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # 对localhost禁用代理
        if 'localhost' in base_url or '127.0.0.1' in base_url:
            self.session.proxies = {
                'http': None,
                'https': None
            }
        
        if debug:
            logging.basicConfig(level=logging.DEBUG)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送HTTP请求的统一方法"""
        url = f"{self.base_url}{endpoint}"
        
        if self.debug:
            logger.debug(f"{method.upper()} {url}")
            if 'json' in kwargs:
                logger.debug(f"Request body: {json.dumps(kwargs['json'], indent=2)}")
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            if self.debug:
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response body: {response.text}")
            
            # 尝试解析JSON响应
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"raw_response": response.text}
            
            # 检查HTTP状态码
            if not response.ok:
                error_message = f"API request failed: {method.upper()} {url} -> {response.status_code}"
                if response_data and isinstance(response_data, dict):
                    if "error" in response_data:
                        error_detail = response_data["error"]
                        if isinstance(error_detail, dict) and "message" in error_detail:
                            error_message += f" - {error_detail['message']}"
                
                raise APIException(
                    error_message,
                    status_code=response.status_code,
                    response_data=response_data
                )
            
            return response_data
            
        except requests.RequestException as e:
            raise APIException(f"Network error: {str(e)}")
    
    def _get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._make_request('GET', endpoint, **kwargs)
    
    def _post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._make_request('POST', endpoint, **kwargs)
    
    def _put(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._make_request('PUT', endpoint, **kwargs)
    
    def _delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._make_request('DELETE', endpoint, **kwargs)
    
    def set_auth_token(self, token: str):
        """设置认证token"""
        self.access_token = token
        self.session.headers['Authorization'] = f'Bearer {token}'
    
    def clear_auth_token(self):
        """清除认证token"""
        self.access_token = None
        self.session.headers.pop('Authorization', None)
    
    # ===== 系统级API =====
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return self._get('/health')
    
    def get_root_info(self) -> Dict[str, Any]:
        """获取系统根信息"""
        return self._get('/')
    
    # ===== 认证模块API =====
    
    def register(self, username: str, email: str, password: str, invite_code: str, 
                real_name: Optional[str] = None, phone: Optional[str] = None) -> Dict[str, Any]:
        """用户注册"""
        data = {
            "username": username,
            "email": email,
            "password": password,
            "invite_code": invite_code
        }
        if real_name:
            data["real_name"] = real_name
        if phone:
            data["phone"] = phone
        
        return self._post('/api/v1/auth/register', json=data)
    
    def login(self, identifier: str, password: str) -> Dict[str, Any]:
        """用户登录"""
        response = self._post('/api/v1/auth/login', json={
            "identifier": identifier,
            "password": password
        })
        
        # 自动设置认证token
        if response.get("success") and "data" in response:
            token = response["data"].get("access_token")
            if token:
                self.set_auth_token(token)
        
        return response
    
    def logout(self) -> Dict[str, Any]:
        """用户登出"""
        try:
            response = self._post('/api/v1/auth/logout')
            return response
        finally:
            # 无论成功与否都清除本地token
            self.clear_auth_token()
    
    def get_me(self) -> Dict[str, Any]:
        """获取当前用户信息"""
        return self._get('/api/v1/auth/me')
    
    def update_me(self, **kwargs) -> Dict[str, Any]:
        """更新用户信息"""
        return self._put('/api/v1/auth/me', json=kwargs)
    
    def verify_email(self, email: str, code: str) -> Dict[str, Any]:
        """验证邮箱"""
        return self._post('/api/v1/auth/verify-email', json={
            "email": email,
            "code": code
        })
    
    def resend_verification(self, email: str) -> Dict[str, Any]:
        """重发验证码"""
        return self._post('/api/v1/auth/resend-verification', json={
            "email": email
        })
    
    def change_password(self, current_password: str, new_password: str) -> Dict[str, Any]:
        """修改密码"""
        return self._put('/api/v1/auth/change-password', json={
            "current_password": current_password,
            "new_password": new_password
        })
    
    def forgot_password(self, email: str) -> Dict[str, Any]:
        """忘记密码"""
        return self._post('/api/v1/auth/forgot-password', json={
            "email": email
        })
    
    def reset_password(self, email: str, reset_token: str, new_password: str) -> Dict[str, Any]:
        """重置密码"""
        return self._post('/api/v1/auth/reset-password', json={
            "email": email,
            "reset_token": reset_token,
            "new_password": new_password
        })
    
    # ===== 管理模块API =====
    
    def create_invite_code(self, description: Optional[str] = None, 
                          expires_at: Optional[str] = None) -> Dict[str, Any]:
        """创建邀请码"""
        data = {}
        if description:
            data["description"] = description
        if expires_at:
            data["expires_at"] = expires_at
        
        return self._post('/api/v1/admin/invite-codes', json=data)
    
    def get_invite_codes(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """获取邀请码列表"""
        return self._get('/api/v1/admin/invite-codes', params={
            "skip": skip,
            "limit": limit
        })
    
    def get_invite_code(self, invite_code_id: int) -> Dict[str, Any]:
        """获取邀请码详情"""
        return self._get(f'/api/v1/admin/invite-codes/{invite_code_id}')
    
    def update_invite_code(self, invite_code_id: int, **kwargs) -> Dict[str, Any]:
        """更新邀请码"""
        return self._put(f'/api/v1/admin/invite-codes/{invite_code_id}', json=kwargs)
    
    def delete_invite_code(self, invite_code_id: int) -> Dict[str, Any]:
        """删除邀请码"""
        return self._delete(f'/api/v1/admin/invite-codes/{invite_code_id}')
    
    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置"""
        return self._get('/api/v1/admin/system/config')
    
    def get_audit_logs(self, user_id: Optional[int] = None, action: Optional[str] = None,
                      entity_type: Optional[str] = None, start_date: Optional[str] = None,
                      end_date: Optional[str] = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """获取审计日志"""
        params = {"skip": skip, "limit": limit}
        if user_id:
            params["user_id"] = user_id
        if action:
            params["action"] = action
        if entity_type:
            params["entity_type"] = entity_type
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        return self._get('/api/v1/admin/audit-logs', params=params)
    
    # ===== 学期课程模块API =====
    
    def get_semesters(self) -> Dict[str, Any]:
        """获取学期列表"""
        return self._get('/api/v1/semesters')
    
    def create_semester(self, name: str, code: str, start_date: str, end_date: str,
                       description: Optional[str] = None) -> Dict[str, Any]:
        """创建学期"""
        data = {
            "name": name,
            "code": code,
            "start_date": start_date,
            "end_date": end_date
        }
        if description:
            data["description"] = description
        
        return self._post('/api/v1/semesters', json=data)
    
    def get_semester(self, semester_id: int) -> Dict[str, Any]:
        """获取学期详情"""
        return self._get(f'/api/v1/semesters/{semester_id}')
    
    def update_semester(self, semester_id: int, **kwargs) -> Dict[str, Any]:
        """更新学期"""
        return self._put(f'/api/v1/semesters/{semester_id}', json=kwargs)
    
    def delete_semester(self, semester_id: int) -> Dict[str, Any]:
        """删除学期"""
        return self._delete(f'/api/v1/semesters/{semester_id}')
    
    def get_semester_courses(self, semester_id: int) -> Dict[str, Any]:
        """获取学期课程"""
        return self._get(f'/api/v1/semesters/{semester_id}/courses')
    
    def get_courses(self, semester_id: Optional[int] = None) -> Dict[str, Any]:
        """获取课程列表"""
        params = {}
        if semester_id:
            params["semester_id"] = semester_id
        
        return self._get('/api/v1/courses', params=params)
    
    def create_course(self, name: str, code: str, semester_id: int,
                     description: Optional[str] = None, credits: Optional[int] = None) -> Dict[str, Any]:
        """创建课程"""
        data = {
            "name": name,
            "code": code,
            "semester_id": semester_id
        }
        if description:
            data["description"] = description
        if credits:
            data["credits"] = credits
        
        return self._post('/api/v1/courses', json=data)
    
    def get_course(self, course_id: int) -> Dict[str, Any]:
        """获取课程详情"""
        return self._get(f'/api/v1/courses/{course_id}')
    
    def update_course(self, course_id: int, **kwargs) -> Dict[str, Any]:
        """更新课程"""
        return self._put(f'/api/v1/courses/{course_id}', json=kwargs)
    
    def delete_course(self, course_id: int) -> Dict[str, Any]:
        """删除课程"""
        return self._delete(f'/api/v1/courses/{course_id}')
    
    # ===== 存储模块API =====
    
    def get_course_folders(self, course_id: int) -> Dict[str, Any]:
        """获取课程文件夹列表"""
        return self._get(f'/api/v1/courses/{course_id}/folders')
    
    def create_folder(self, course_id: int, name: str, folder_type: str) -> Dict[str, Any]:
        """创建文件夹"""
        return self._post(f'/api/v1/courses/{course_id}/folders', json={
            "name": name,
            "folder_type": folder_type
        })
    
    def update_folder(self, folder_id: int, **kwargs) -> Dict[str, Any]:
        """更新文件夹"""
        return self._put(f'/api/v1/folders/{folder_id}', json=kwargs)
    
    def delete_folder(self, folder_id: int) -> Dict[str, Any]:
        """删除文件夹"""
        return self._delete(f'/api/v1/folders/{folder_id}')
    
    def get_folder_files(self, folder_id: int) -> Dict[str, Any]:
        """获取文件夹文件列表"""
        return self._get(f'/api/v1/folders/{folder_id}/files')
    
    def upload_file(self, file_path: Union[str, Path], course_id: int, folder_id: int,
                   description: Optional[str] = None) -> Dict[str, Any]:
        """上传文件"""
        file_path = Path(file_path)
        
        # 构建multipart/form-data请求
        files = {'file': (file_path.name, open(file_path, 'rb'))}
        data = {
            'course_id': str(course_id),
            'folder_id': str(folder_id)
        }
        if description:
            data['description'] = description
        
        # 临时移除Content-Type头，让requests自动设置multipart格式
        original_content_type = self.session.headers.pop('Content-Type', None)
        
        try:
            response = self._make_request('POST', '/api/v1/files/upload', files=files, data=data)
            return response
        finally:
            # 恢复Content-Type头
            if original_content_type:
                self.session.headers['Content-Type'] = original_content_type
            # 关闭文件
            files['file'][1].close()
    
    def download_file(self, file_id: int) -> requests.Response:
        """下载文件"""
        url = f"{self.base_url}/api/v1/files/{file_id}/download"
        response = self.session.get(url, stream=True)
        
        if not response.ok:
            raise APIException(
                f"File download failed: {response.status_code}",
                status_code=response.status_code
            )
        
        return response
    
    def delete_file(self, file_id: int) -> Dict[str, Any]:
        """删除文件"""
        return self._delete(f'/api/v1/files/{file_id}')
    
    def upload_temporary_file(self, file_path: Union[str, Path], expiry_hours: int = 24,
                             purpose: Optional[str] = None) -> Dict[str, Any]:
        """上传临时文件"""
        file_path = Path(file_path)
        
        files = {'file': (file_path.name, open(file_path, 'rb'))}
        data = {'expiry_hours': str(expiry_hours)}
        if purpose:
            data['purpose'] = purpose
        
        original_content_type = self.session.headers.pop('Content-Type', None)
        
        try:
            response = self._make_request('POST', '/api/v1/tempfiles/upload', files=files, data=data)
            return response
        finally:
            if original_content_type:
                self.session.headers['Content-Type'] = original_content_type
            files['file'][1].close()
    
    def download_temporary_file(self, file_id: int) -> requests.Response:
        """下载临时文件"""
        url = f"{self.base_url}/api/v1/tempfiles/{file_id}/download"
        response = self.session.get(url, stream=True)
        
        if not response.ok:
            raise APIException(
                f"Temporary file download failed: {response.status_code}",
                status_code=response.status_code
            )
        
        return response
    
    def delete_temporary_file(self, file_id: int) -> Dict[str, Any]:
        """删除临时文件"""
        return self._delete(f'/api/v1/tempfiles/{file_id}')
    
    # ===== 聊天模块API =====
    
    def get_chats(self, chat_type: Optional[str] = None) -> Dict[str, Any]:
        """获取用户聊天列表"""
        params = {}
        if chat_type:
            params["chat_type"] = chat_type
        
        return self._get('/api/v1/chats', params=params)
    
    def create_chat(self, title: str, chat_type: str, course_id: Optional[int] = None,
                   ai_model: str = "gpt-3.5-turbo", custom_prompt: Optional[str] = None,
                   rag_enabled: bool = True, context_mode: str = "default") -> Dict[str, Any]:
        """创建聊天"""
        data = {
            "title": title,
            "chat_type": chat_type,
            "ai_model": ai_model,
            "rag_enabled": rag_enabled,
            "context_mode": context_mode
        }
        if course_id:
            data["course_id"] = course_id
        if custom_prompt:
            data["custom_prompt"] = custom_prompt
        
        return self._post('/api/v1/chats', json=data)
    
    def update_chat(self, chat_id: int, **kwargs) -> Dict[str, Any]:
        """更新聊天"""
        return self._put(f'/api/v1/chats/{chat_id}', json=kwargs)
    
    def delete_chat(self, chat_id: int) -> Dict[str, Any]:
        """删除聊天"""
        return self._delete(f'/api/v1/chats/{chat_id}')
    
    def get_chat_messages(self, chat_id: int, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """获取聊天消息列表"""
        return self._get(f'/api/v1/chats/{chat_id}/messages', params={
            "limit": limit,
            "offset": offset
        })
    
    def send_message(self, chat_id: int, content: str) -> Dict[str, Any]:
        """发送消息"""
        return self._post(f'/api/v1/chats/{chat_id}/messages', json={
            "content": content
        })
    
    def edit_message(self, message_id: int, content: str) -> Dict[str, Any]:
        """编辑消息"""
        return self._put(f'/api/v1/messages/{message_id}', json={
            "content": content
        })
    
    def delete_message(self, message_id: int) -> Dict[str, Any]:
        """删除消息"""
        return self._delete(f'/api/v1/messages/{message_id}')
    
    # ===== AI模块API =====
    
    def ai_chat(self, message: str, ai_model: str = "gpt-3.5-turbo", 
               chat_type: str = "general", rag_enabled: bool = True,
               course_id: Optional[int] = None, context_mode: str = "default",
               custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """AI对话生成"""
        data = {
            "message": message,
            "ai_model": ai_model,
            "chat_type": chat_type,
            "rag_enabled": rag_enabled,
            "context_mode": context_mode
        }
        if course_id:
            data["course_id"] = course_id
        if custom_prompt:
            data["custom_prompt"] = custom_prompt
        
        return self._post('/api/v1/ai/chat', json=data)
    
    def get_ai_models(self) -> Dict[str, Any]:
        """获取可用AI模型"""
        return self._get('/api/v1/ai/models')
    
    def get_ai_configs(self) -> Dict[str, Any]:
        """获取对话配置"""
        return self._get('/api/v1/ai/configs')
    
    def rag_search(self, query: str, course_id: Optional[int] = None, limit: int = 5) -> Dict[str, Any]:
        """知识库搜索"""
        params = {"query": query, "limit": limit}
        if course_id:
            params["course_id"] = course_id
        
        return self._post('/api/v1/ai/rag/search', params=params)
    
    def vectorize_file(self, file_id: int) -> Dict[str, Any]:
        """文件向量化"""
        return self._post(f'/api/v1/ai/vectorize/file/{file_id}')
    
    def vectorize_course(self, course_id: int) -> Dict[str, Any]:
        """课程文件批量向量化"""
        return self._post(f'/api/v1/ai/vectorize/course/{course_id}')
    
    def get_vectorization_status(self, file_id: int) -> Dict[str, Any]:
        """查询文件向量化状态"""
        return self._get(f'/api/v1/ai/vectorize/status/{file_id}')


# 便利函数
def create_client(base_url: str = "http://localhost:8001", debug: bool = False) -> CampusLLMClient:
    """创建API客户端实例"""
    return CampusLLMClient(base_url=base_url, debug=debug)


def create_admin_client(base_url: str = "http://localhost:8001", debug: bool = False) -> CampusLLMClient:
    """创建管理员API客户端实例"""
    client = CampusLLMClient(base_url=base_url, debug=debug)
    # TODO: 这里可以预设管理员登录逻辑
    return client