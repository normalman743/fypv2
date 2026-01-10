// Campus LLM Demo 主应用逻辑

class CampusLLMApp {
    constructor() {
        this.currentGeneralChatId = null;
        this.currentCourseChatId = null;
        this.currentMode = 'general'; // 'general' | 'course'
        this.courseData = {};
        this.selectedContext = {
            file_ids: [],
            folder_ids: []
        };
        
        this.initializeApp();
    }

    // 初始化应用
    initializeApp() {
        console.log('[App] Initializing Campus LLM Demo...');
        
        // 绑定事件监听器
        this.bindEventListeners();
        
        // 尝试恢复登录状态
        if (apiClient.restoreLoginState()) {
            this.showMainApp();
            this.validateToken();
        } else {
            this.showLoginSection();
        }
    }

    // 绑定事件监听器
    bindEventListeners() {
        // 登录相关
        document.getElementById('loginBtn').addEventListener('click', () => this.handleLogin());
        document.getElementById('logoutBtn').addEventListener('click', () => this.handleLogout());
        
        // 支持回车键登录
        document.getElementById('loginUsername').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleLogin();
        });
        document.getElementById('loginPassword').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleLogin();
        });

        // 模式切换
        document.getElementById('generalChatBtn').addEventListener('click', () => this.switchMode('general'));
        document.getElementById('courseChatBtn').addEventListener('click', () => this.switchMode('course'));

        // General Chat 功能
        document.getElementById('generalSendBtn').addEventListener('click', () => this.sendGeneralMessage());
        document.getElementById('generalChatInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendGeneralMessage();
        });

        // Course Chat 功能
        document.getElementById('courseSendBtn').addEventListener('click', () => this.sendCourseMessage());
        document.getElementById('courseChatInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendCourseMessage();
        });
    }

    // ==================== 界面显示控制 ====================

    showLoginSection() {
        document.getElementById('loginSection').style.display = 'block';
        document.getElementById('mainApp').style.display = 'none';
        document.getElementById('userInfo').style.display = 'none';
    }

    showMainApp() {
        document.getElementById('loginSection').style.display = 'none';
        document.getElementById('mainApp').style.display = 'block';
        document.getElementById('userInfo').style.display = 'flex';
        
        // 显示用户信息
        if (apiClient.currentUser) {
            document.getElementById('username').textContent = apiClient.currentUser.username;
        }
    }

    switchMode(mode) {
        this.currentMode = mode;
        
        // 更新按钮状态
        document.getElementById('generalChatBtn').classList.toggle('active', mode === 'general');
        document.getElementById('courseChatBtn').classList.toggle('active', mode === 'course');
        
        // 显示对应的界面
        document.getElementById('generalChatMode').style.display = mode === 'general' ? 'block' : 'none';
        document.getElementById('courseChatMode').style.display = mode === 'course' ? 'block' : 'none';
        
        // 如果切换到课程模式，加载课程数据
        if (mode === 'course' && Object.keys(this.courseData).length === 0) {
            this.loadCourseData();
        }
        
        console.log(`[App] Switched to ${mode} mode`);
    }

    // ==================== 认证相关 ====================

    async handleLogin() {
        console.log('[App] Login button clicked');
        
        const usernameInput = document.getElementById('loginUsername');
        const passwordInput = document.getElementById('loginPassword');
        const loginBtn = document.getElementById('loginBtn');
        const statusDiv = document.getElementById('loginStatus');

        console.log('[App] Form elements found:', {
            usernameInput: !!usernameInput,
            passwordInput: !!passwordInput,
            loginBtn: !!loginBtn,
            statusDiv: !!statusDiv
        });

        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();

        console.log('[App] Form values:', { 
            username: username ? '***' : '(empty)', 
            password: password ? '***' : '(empty)' 
        });

        if (!username || !password) {
            this.showStatus('请输入用户名和密码', 'error');
            return;
        }

        // 显示加载状态
        loginBtn.disabled = true;
        loginBtn.textContent = '登录中...';
        this.showStatus('正在验证凭据...', '');

        try {
            const result = await apiClient.login(username, password);
            
            if (result.success) {
                this.showStatus('登录成功！', 'success');
                setTimeout(() => {
                    this.showMainApp();
                }, 1000);
            }
        } catch (error) {
            console.error('[App] Login error:', error);
            this.showStatus(error.message, 'error');
        } finally {
            loginBtn.disabled = false;
            loginBtn.textContent = '登录';
        }
    }

    async validateToken() {
        try {
            await apiClient.getCurrentUser();
            console.log('[App] Token validation successful');
        } catch (error) {
            console.error('[App] Token validation failed:', error);
            this.showLoginSection();
            this.showStatus('登录已过期，请重新登录', 'error');
        }
    }

    handleLogout() {
        apiClient.logout();
        this.showLoginSection();
        this.clearAllData();
        console.log('[App] User logged out');
    }

    showStatus(message, type = '') {
        const statusDiv = document.getElementById('loginStatus');
        statusDiv.textContent = message;
        statusDiv.className = `status-message ${type}`;
    }

    // ==================== 课程数据加载 ====================

    async loadCourseData() {
        const courseDataDiv = document.getElementById('courseData');
        courseDataDiv.innerHTML = '<div class="loading">正在加载课程数据...</div>';

        try {
            // 获取指定学期的课程
            const coursesResponse = await apiClient.getCourses(CONFIG.DEFAULT_SEMESTER_ID);
            
            if (coursesResponse.success && coursesResponse.data.courses) {
                this.courseData.courses = coursesResponse.data.courses;
                await this.loadCourseFoldersAndFiles();
                this.renderCourseData();
            } else {
                throw new Error('获取课程数据失败');
            }
        } catch (error) {
            console.error('[App] Load course data error:', error);
            courseDataDiv.innerHTML = `<div class="error">加载课程数据失败: ${error.message}</div>`;
        }
    }

    async loadCourseFoldersAndFiles() {
        for (const course of this.courseData.courses) {
            try {
                // 获取课程文件夹
                const foldersResponse = await apiClient.getCourseFolders(course.id);
                
                if (foldersResponse.success && foldersResponse.data.folders) {
                    course.folders = foldersResponse.data.folders;
                    
                    // 获取每个文件夹的文件
                    for (const folder of course.folders) {
                        try {
                            const filesResponse = await apiClient.getFolderFiles(folder.id);
                            
                            if (filesResponse.success && filesResponse.data.files) {
                                folder.files = filesResponse.data.files;
                            } else {
                                folder.files = [];
                            }
                        } catch (error) {
                            console.error(`[App] Load files for folder ${folder.id} error:`, error);
                            folder.files = [];
                        }
                    }
                } else {
                    course.folders = [];
                }
            } catch (error) {
                console.error(`[App] Load folders for course ${course.id} error:`, error);
                course.folders = [];
            }
        }
    }

    renderCourseData() {
        const courseDataDiv = document.getElementById('courseData');
        
        if (!this.courseData.courses || this.courseData.courses.length === 0) {
            courseDataDiv.innerHTML = '<div class="no-data">未找到课程数据</div>';
            return;
        }

        let html = '';
        
        this.courseData.courses.forEach(course => {
            html += `
                <div class="course-item">
                    <h4>${course.name} (${course.code})</h4>
                    <div class="folders-list">
            `;
            
            if (course.folders && course.folders.length > 0) {
                course.folders.forEach(folder => {
                    const fileCount = folder.files ? folder.files.length : 0;
                    html += `
                        <div class="folder-item">
                            <div class="folder-header" onclick="app.toggleFolder('folder-${folder.id}')">
                                <span class="folder-icon">📁</span>
                                <span class="folder-name">${folder.name}</span>
                                <span class="file-count">(${fileCount} 文件)</span>
                                <button class="context-btn" onclick="app.selectFolderContext(${folder.id})" title="选择为上下文">
                                    选择文件夹
                                </button>
                            </div>
                            <div class="files-list" id="folder-${folder.id}" style="display: none;">
                    `;
                    
                    if (folder.files && folder.files.length > 0) {
                        folder.files.forEach(file => {
                            html += `
                                <div class="file-item">
                                    <span class="file-icon">📄</span>
                                    <span class="file-name">${file.original_name}</span>
                                    <span class="file-size">(${this.formatFileSize(file.file_size)})</span>
                                    <button class="context-btn" onclick="app.selectFileContext(${file.id})" title="选择为上下文">
                                        选择文件
                                    </button>
                                </div>
                            `;
                        });
                    } else {
                        html += '<div class="no-files">文件夹为空</div>';
                    }
                    
                    html += '</div></div>';
                });
            } else {
                html += '<div class="no-folders">暂无文件夹</div>';
            }
            
            html += '</div></div>';
        });

        // 添加上下文显示区域
        html += `
            <div class="context-selection">
                <h4>已选择的上下文:</h4>
                <div id="selectedContext">
                    <div class="no-selection">尚未选择任何文件或文件夹</div>
                </div>
                <button onclick="app.clearContext()" class="btn btn-secondary">清除选择</button>
            </div>
        `;

        courseDataDiv.innerHTML = html;
    }

    // ==================== 辅助方法 ====================

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    toggleFolder(folderId) {
        const folderDiv = document.getElementById(folderId);
        if (folderDiv) {
            const isVisible = folderDiv.style.display !== 'none';
            folderDiv.style.display = isVisible ? 'none' : 'block';
        }
    }

    selectFolderContext(folderId) {
        if (!this.selectedContext.folder_ids.includes(folderId)) {
            this.selectedContext.folder_ids.push(folderId);
            this.updateContextDisplay();
        }
    }

    selectFileContext(fileId) {
        if (!this.selectedContext.file_ids.includes(fileId)) {
            this.selectedContext.file_ids.push(fileId);
            this.updateContextDisplay();
        }
    }

    clearContext() {
        this.selectedContext = {
            file_ids: [],
            folder_ids: []
        };
        this.updateContextDisplay();
    }

    updateContextDisplay() {
        const contextDiv = document.getElementById('selectedContext');
        if (!contextDiv) return;

        const totalSelected = this.selectedContext.file_ids.length + this.selectedContext.folder_ids.length;
        
        if (totalSelected === 0) {
            contextDiv.innerHTML = '<div class="no-selection">尚未选择任何文件或文件夹</div>';
            return;
        }

        let html = '';
        
        // 显示选中的文件夹
        this.selectedContext.folder_ids.forEach(folderId => {
            const folder = this.findFolderById(folderId);
            if (folder) {
                html += `
                    <div class="context-item">
                        <span class="context-type">📁 文件夹:</span>
                        <span class="context-name">${folder.name}</span>
                        <button onclick="app.removeFromContext('folder', ${folderId})" class="remove-btn">×</button>
                    </div>
                `;
            }
        });

        // 显示选中的文件
        this.selectedContext.file_ids.forEach(fileId => {
            const file = this.findFileById(fileId);
            if (file) {
                html += `
                    <div class="context-item">
                        <span class="context-type">📄 文件:</span>
                        <span class="context-name">${file.original_name}</span>
                        <button onclick="app.removeFromContext('file', ${fileId})" class="remove-btn">×</button>
                    </div>
                `;
            }
        });

        contextDiv.innerHTML = html;
    }

    removeFromContext(type, id) {
        if (type === 'folder') {
            this.selectedContext.folder_ids = this.selectedContext.folder_ids.filter(fid => fid !== id);
        } else if (type === 'file') {
            this.selectedContext.file_ids = this.selectedContext.file_ids.filter(fid => fid !== id);
        }
        this.updateContextDisplay();
    }

    findFolderById(folderId) {
        for (const course of this.courseData.courses || []) {
            for (const folder of course.folders || []) {
                if (folder.id === folderId) {
                    return folder;
                }
            }
        }
        return null;
    }

    findFileById(fileId) {
        for (const course of this.courseData.courses || []) {
            for (const folder of course.folders || []) {
                for (const file of folder.files || []) {
                    if (file.id === fileId) {
                        return file;
                    }
                }
            }
        }
        return null;
    }

    clearAllData() {
        this.currentGeneralChatId = null;
        this.currentCourseChatId = null;
        this.courseData = {};
        this.selectedContext = {
            file_ids: [],
            folder_ids: []
        };
        
        // 清除聊天界面
        document.getElementById('generalChatMessages').innerHTML = '';
        document.getElementById('courseChatMessages').innerHTML = '';
    }

    // ==================== General Chat 功能 ====================

    async sendGeneralMessage() {
        const input = document.getElementById('generalChatInput');
        const sendBtn = document.getElementById('generalSendBtn');
        const messagesDiv = document.getElementById('generalChatMessages');
        
        const message = input.value.trim();
        if (!message) return;
        
        // 禁用输入
        input.disabled = true;
        sendBtn.disabled = true;
        sendBtn.textContent = '发送中...';
        
        try {
            // 获取聊天配置
            const chatConfig = this.getGeneralChatConfig();
            
            // 显示用户消息
            this.addMessageToChat(messagesDiv, 'user', message);
            
            if (!this.currentGeneralChatId) {
                // 创建新聊天
                await this.createGeneralChat(message, chatConfig);
            } else {
                // 发送消息到现有聊天
                await this.sendMessageToChat(this.currentGeneralChatId, message, chatConfig, messagesDiv);
            }
            
            input.value = '';
        } catch (error) {
            console.error('[App] Send general message error:', error);
            this.addMessageToChat(messagesDiv, 'error', `发送失败: ${error.message}`);
        } finally {
            input.disabled = false;
            sendBtn.disabled = false;
            sendBtn.textContent = '发送';
        }
    }

    getGeneralChatConfig() {
        return {
            chat_type: 'general',
            ai_model: document.getElementById('generalAiModel').value,
            context_mode: document.getElementById('generalContextMode').value,
            search_enabled: document.getElementById('generalSearchEnabled').checked,
            custom_prompt: document.getElementById('generalCustomPrompt').value || null,
            stream: false // 固定为非流式
        };
    }

    async createGeneralChat(firstMessage, config) {
        const messagesDiv = document.getElementById('generalChatMessages');
        
        try {
            console.log('[App] Creating general chat with config:', config);
            
            const chatData = {
                ...config,
                first_message: firstMessage
            };

            // 只使用非流式响应
            const response = await apiClient.createChat(chatData);
            
            if (response.success) {
                this.currentGeneralChatId = response.data.chat.id;
                
                // 显示AI回复
                if (response.data.ai_message) {
                    this.addMessageToChat(messagesDiv, 'assistant', response.data.ai_message.content, response.data.ai_message.rag_sources);
                }
            }
        } catch (error) {
            console.error('[App] Create general chat error:', error);
            throw error;
        }
    }

    async sendMessageToChat(chatId, message, config, messagesDiv) {
        try {
            const messageData = {
                content: message,
                stream: false
            };

            // 只使用非流式响应
            const response = await apiClient.sendMessage(chatId, messageData);
            
            if (response.success && response.data.ai_message) {
                this.addMessageToChat(messagesDiv, 'assistant', response.data.ai_message.content, response.data.ai_message.rag_sources);
            }
        } catch (error) {
            console.error('[App] Send message error:', error);
            throw error;
        }
    }

    async handleStreamResponse(reader, messagesDiv, onChatCreated = null) {
        const decoder = new TextDecoder();
        let assistantMessageDiv = null;
        let buffer = '';

        try {
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) {
                    console.log('[Stream] Stream completed');
                    break;
                }

                // 解码数据
                buffer += decoder.decode(value, { stream: true });
                
                // 处理完整的数据行
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // 保留不完整的行
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        
                        if (data === '[DONE]') {
                            console.log('[Stream] Received DONE signal');
                            continue;
                        }
                        
                        try {
                            const chunk = JSON.parse(data);
                            console.log('[Stream] Received chunk:', chunk);
                            
                            if (chunk.type === 'chat_created' && onChatCreated) {
                                onChatCreated(chunk.data);
                            } else if (chunk.type === 'message_chunk') {
                                // 创建或更新AI消息显示
                                if (!assistantMessageDiv) {
                                    assistantMessageDiv = this.addMessageToChat(messagesDiv, 'assistant', '');
                                }
                                
                                // 追加内容
                                const contentDiv = assistantMessageDiv.querySelector('.message-content');
                                contentDiv.textContent += chunk.data.content || '';
                                
                                // 滚动到底部
                                messagesDiv.scrollTop = messagesDiv.scrollHeight;
                            } else if (chunk.type === 'error') {
                                throw new Error(chunk.error);
                            }
                        } catch (parseError) {
                            console.error('[Stream] Parse error:', parseError, 'Data:', data);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('[Stream] Stream error:', error);
            throw error;
        }
    }

    addMessageToChat(messagesDiv, role, content, ragSources = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const now = new Date().toLocaleTimeString();
        
        let ragSourcesHtml = '';
        if (ragSources && ragSources.length > 0) {
            ragSourcesHtml = `
                <div class="rag-sources">
                    <div class="rag-sources-title">📚 参考来源:</div>
                    ${ragSources.map(source => `
                        <div class="rag-source-item">
                            <span class="source-file">${source.source_file}</span>
                            <span class="chunk-id">(chunk: ${source.chunk_id})</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        messageDiv.innerHTML = `
            <div class="message-content">${this.escapeHtml(content)}</div>
            ${ragSourcesHtml}
            <div class="message-time">${now}</div>
        `;
        
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        
        return messageDiv;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async sendCourseMessage() {
        const input = document.getElementById('courseChatInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        console.log('[App] Sending course message:', message);
        console.log('[App] Selected context:', this.selectedContext);
        // TODO: 实现 Course Chat 功能
        input.value = '';
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new CampusLLMApp();
});

// 添加一些 CSS 样式到页面
const additionalCSS = `
    .course-item {
        margin-bottom: 1.5rem;
        padding: 1rem;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        background: white;
    }

    .course-item h4 {
        margin-bottom: 1rem;
        color: #374151;
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 0.5rem;
    }

    .folder-item {
        margin-bottom: 0.5rem;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        overflow: hidden;
    }

    .folder-header {
        display: flex;
        align-items: center;
        padding: 0.75rem;
        background: #f9fafb;
        cursor: pointer;
        gap: 0.5rem;
    }

    .folder-header:hover {
        background: #f3f4f6;
    }

    .folder-name {
        flex: 1;
        font-weight: 500;
    }

    .file-count {
        color: #6b7280;
        font-size: 0.875rem;
    }

    .context-btn {
        padding: 0.25rem 0.5rem;
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 0.75rem;
        cursor: pointer;
    }

    .context-btn:hover {
        background: #2563eb;
    }

    .files-list {
        background: white;
    }

    .file-item {
        display: flex;
        align-items: center;
        padding: 0.5rem 1rem;
        border-top: 1px solid #e5e7eb;
        gap: 0.5rem;
    }

    .file-item:hover {
        background: #f9fafb;
    }

    .file-name {
        flex: 1;
    }

    .file-size {
        color: #6b7280;
        font-size: 0.875rem;
    }

    .context-selection {
        margin-top: 2rem;
        padding: 1rem;
        background: #f8fafc;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }

    .context-selection h4 {
        margin-bottom: 1rem;
        color: #374151;
    }

    .context-item {
        display: flex;
        align-items: center;
        padding: 0.5rem;
        margin-bottom: 0.5rem;
        background: white;
        border-radius: 4px;
        gap: 0.5rem;
    }

    .context-type {
        font-weight: 500;
        color: #4b5563;
    }

    .context-name {
        flex: 1;
    }

    .remove-btn {
        background: #ef4444;
        color: white;
        border: none;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        line-height: 1;
    }

    .remove-btn:hover {
        background: #dc2626;
    }

    .no-selection, .no-data, .no-folders, .no-files {
        color: #6b7280;
        font-style: italic;
        text-align: center;
        padding: 1rem;
    }

    .error {
        color: #dc2626;
        text-align: center;
        padding: 1rem;
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 6px;
    }

    .rag-sources {
        margin-top: 0.5rem;
        padding: 0.5rem;
        background: #f0f9ff;
        border: 1px solid #bae6fd;
        border-radius: 4px;
        font-size: 0.875rem;
    }

    .rag-sources-title {
        font-weight: 500;
        color: #0369a1;
        margin-bottom: 0.25rem;
    }

    .rag-source-item {
        display: flex;
        justify-content: space-between;
        padding: 0.125rem 0;
        color: #374151;
    }

    .source-file {
        font-weight: 500;
    }

    .chunk-id {
        color: #6b7280;
        font-size: 0.75rem;
    }
`;

// 添加CSS到页面
const style = document.createElement('style');
style.textContent = additionalCSS;
document.head.appendChild(style);