// Campus LLM API 客户端类

class CampusLLMAPIClient {
    constructor() {
        this.baseURL = CONFIG.API_BASE_URL;
        this.token = localStorage.getItem('campus_llm_token');
        this.currentUser = null;
    }

    // 通用请求方法
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const defaultOptions = {
            mode: 'cors',
            credentials: 'omit',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            ...options
        };

        // 添加认证头
        if (this.token) {
            defaultOptions.headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            console.log(`[API] ${options.method || 'GET'} ${endpoint}`);
            
            const response = await fetch(url, defaultOptions);
            
            // 检查响应状态
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error?.message || `HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log(`[API] Success:`, data);
            
            return data;
        } catch (error) {
            console.error(`[API] Error on ${endpoint}:`, error);
            throw error;
        }
    }

    // GET 请求
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    // POST 请求
    async post(endpoint, body = null) {
        return this.request(endpoint, {
            method: 'POST',
            body: body ? JSON.stringify(body) : null
        });
    }

    // PUT 请求
    async put(endpoint, body = null) {
        return this.request(endpoint, {
            method: 'PUT',
            body: body ? JSON.stringify(body) : null
        });
    }

    // DELETE 请求
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // 文件上传请求
    async uploadFile(endpoint, formData) {
        const url = `${this.baseURL}${endpoint}`;
        
        const options = {
            method: 'POST',
            headers: {}
        };

        // 添加认证头
        if (this.token) {
            options.headers['Authorization'] = `Bearer ${this.token}`;
        }

        // 不设置 Content-Type，让浏览器自动设置 multipart/form-data
        options.body = formData;

        try {
            console.log(`[API] POST ${endpoint} (file upload)`);
            
            const response = await fetch(url, options);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error?.message || `HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log(`[API] Upload success:`, data);
            
            return data;
        } catch (error) {
            console.error(`[API] Upload error on ${endpoint}:`, error);
            throw error;
        }
    }

    // ==================== 认证相关 API ====================

    // 用户登录
    async login(username, password) {
        try {
            // 现在CORS已经配置好，使用正确的Content-Type
            const url = `${this.baseURL}/api/v1/auth/login`;
            const response = await fetch(url, {
                method: 'POST',
                mode: 'cors',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            const data = await response.json();

            if (data.success && data.data.access_token) {
                this.token = data.data.access_token;
                this.currentUser = data.data.user;
                
                // 保存到本地存储
                localStorage.setItem('campus_llm_token', this.token);
                localStorage.setItem('campus_llm_user', JSON.stringify(this.currentUser));
                
                console.log('[Auth] Login successful:', this.currentUser);
                return { success: true, user: this.currentUser };
            } else {
                throw new Error('登录响应格式错误');
            }
        } catch (error) {
            console.error('[Auth] Login failed:', error);
            throw new Error(`登录失败: ${error.message}`);
        }
    }

    // 获取当前用户信息
    async getCurrentUser() {
        try {
            const response = await this.get('/api/v1/auth/me');
            
            if (response.success && response.data) {
                this.currentUser = response.data;
                localStorage.setItem('campus_llm_user', JSON.stringify(this.currentUser));
                return this.currentUser;
            } else {
                throw new Error('获取用户信息失败');
            }
        } catch (error) {
            console.error('[Auth] Get current user failed:', error);
            this.logout();
            throw error;
        }
    }

    // 用户登出
    logout() {
        this.token = null;
        this.currentUser = null;
        localStorage.removeItem('campus_llm_token');
        localStorage.removeItem('campus_llm_user');
        console.log('[Auth] Logged out');
    }

    // 检查是否已登录
    isLoggedIn() {
        return !!this.token;
    }

    // 从本地存储恢复登录状态
    restoreLoginState() {
        const savedToken = localStorage.getItem('campus_llm_token');
        const savedUser = localStorage.getItem('campus_llm_user');
        
        if (savedToken && savedUser) {
            this.token = savedToken;
            try {
                this.currentUser = JSON.parse(savedUser);
                console.log('[Auth] Restored login state:', this.currentUser);
                return true;
            } catch (error) {
                console.error('[Auth] Failed to restore user data:', error);
                this.logout();
                return false;
            }
        }
        return false;
    }

    // ==================== 课程数据 API ====================

    // 获取学期列表
    async getSemesters() {
        return this.get('/api/v1/semesters');
    }

    // 获取课程列表
    async getCourses(semesterId = null) {
        const endpoint = semesterId 
            ? `/api/v1/courses?semester_id=${semesterId}`
            : '/api/v1/courses';
        return this.get(endpoint);
    }

    // 获取课程文件夹
    async getCourseFolders(courseId) {
        return this.get(`/api/v1/courses/${courseId}/folders`);
    }

    // 获取文件夹文件
    async getFolderFiles(folderId) {
        return this.get(`/api/v1/folders/${folderId}/files`);
    }

    // ==================== 文件上传 API ====================

    // 上传文件到课程文件夹
    async uploadCourseFile(file, courseId, folderId) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('course_id', courseId.toString());
        formData.append('folder_id', folderId.toString());

        return this.uploadFile('/api/v1/files/upload', formData);
    }

    // 上传临时文件
    async uploadTemporaryFile(file, purpose = 'chat_upload') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('purpose', purpose);

        return this.uploadFile('/api/v1/files/temporary', formData);
    }

    // ==================== 聊天相关 API ====================

    // 创建聊天
    async createChat(chatData) {
        return this.post('/api/v1/chats', chatData);
    }

    // 发送消息
    async sendMessage(chatId, messageData) {
        return this.post(`/api/v1/chats/${chatId}/messages`, messageData);
    }

    // 获取聊天列表
    async getChats() {
        return this.get('/api/v1/chats');
    }

    // 获取聊天消息
    async getChatMessages(chatId) {
        return this.get(`/api/v1/chats/${chatId}/messages`);
    }

    // ==================== 流式响应处理 ====================

    // 创建带流式响应的聊天
    async createChatStream(chatData) {
        const url = `${this.baseURL}/api/v1/chats`;
        
        const options = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            },
            body: JSON.stringify({ ...chatData, stream: true })
        };

        const response = await fetch(url, options);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response.body.getReader();
    }

    // 发送带流式响应的消息
    async sendMessageStream(chatId, messageData) {
        const url = `${this.baseURL}/api/v1/chats/${chatId}/messages`;
        
        const options = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            },
            body: JSON.stringify({ ...messageData, stream: true })
        };

        const response = await fetch(url, options);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response.body.getReader();
    }
}

// 创建全局 API 客户端实例
window.apiClient = new CampusLLMAPIClient();