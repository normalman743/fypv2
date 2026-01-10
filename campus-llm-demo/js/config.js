// Campus LLM Demo 配置文件

const CONFIG = {
    // API 基础配置
    API_BASE_URL: 'https://api-icu.584743.xyz',
    
    // Demo 固定凭据 (仅用于演示)
    DEMO_CREDENTIALS: {
        username: 'demo', // 可以在这里设置默认值，或在界面中填写
        password: 'demo'  // 可以在这里设置默认值，或在界面中填写
    },
    
    // 默认学期 ID (根据需求固定为1)
    DEFAULT_SEMESTER_ID: 1,
    
    // 文件上传限制
    FILE_UPLOAD: {
        MAX_SIZE: 5 * 1024 * 1024, // 5MB
        ALLOWED_EXTENSIONS: [
            'txt', 'docx', 'doc', 'py', 'c', 'md', 'js', 'html',
            'pdf', 'pptx', 'ppt', 'xlsx', 'xls', 'json', 'xml',
            'css', 'java', 'cpp', 'h', 'hpp'
        ],
        ALLOWED_MIME_TYPES: [
            'text/plain',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
            'text/x-python-script',
            'text/x-c',
            'text/markdown',
            'application/javascript',
            'text/html',
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'application/json',
            'text/xml',
            'text/css'
        ]
    },
    
    // AI 模型选项
    AI_MODELS: ['Star', 'StarPlus', 'StarCode'],
    
    // 上下文模式选项
    CONTEXT_MODES: ['Economy', 'Standard', 'Premium', 'Max'],
    
    // 聊天类型
    CHAT_TYPES: ['general', 'course'],
    
    // 请求超时设置
    REQUEST_TIMEOUT: 30000, // 30秒
    
    // 流式响应设置
    STREAMING: {
        ENABLED: true,
        CHUNK_DELIMITER: '\n\n',
        DONE_SIGNAL: '[DONE]'
    }
};

// 暴露配置给全局使用
window.CONFIG = CONFIG;