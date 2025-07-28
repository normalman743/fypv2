# AI 模块技术设计文档 🤖

## 概述

AI模块是Campus LLM System v2的核心智能服务模块，负责AI对话生成、RAG文档检索、向量存储管理和模型调用。基于v1版本的成熟AI服务设计，采用FastAPI 2024最佳实践，提供多模型支持、流式响应、成本追踪和完整的RAG检索增强生成功能。

## 📋 基于v1的功能继承与优化

### v1现有AI架构继承
基于v1成熟的AI模型管理体系：
- **5个AI模型**: Star(gpt-4o-mini)、StarPlus(gpt-4o)、StarCode(gpt-4.1)
- **成本配置**: 已有精确的input/output token成本计算
- **搜索支持**: Star/StarPlus支持搜索，⚠️ StarCode暂不支持搜索


# 模型到OpenAI模型的映射
MODEL_MAPPING = {
    AIModel.STAR: {
        "base": "gpt-4o-mini",
        "search": "gpt-4o-mini-search-preview",
        "supports_search": True,
        "input_cost_per_million": 0.15,  # $0.15 per 1M input tokens
        "output_cost_per_million": 0.60,  # $0.60 per 1M output tokens
        "max_tokens": 1000
    },
    AIModel.STAR_PLUS: {
        "base": "gpt-4o", 
        "search": "gpt-4o-search-preview",
        "supports_search": True,
        "input_cost_per_million": 2.50,  # $2.50 per 1M input tokens
        "output_cost_per_million": 10.00,  # $10.00 per 1M output tokens
        "max_tokens": 2000
    },
    AIModel.STAR_CODE: {
        "base": "gpt-4.1",  # 代码专用模型
        "search": None,  # 不支持搜索
        "supports_search": False,
        "input_cost_per_million": 2.00,  # $2.00 per 1M input tokens
        "output_cost_per_million": 8.00,  # $8.00 per 1M output tokens
        "max_tokens": 4000
    }
}


### RAG检索优化重点

#### rag_file_scope 多范围支持 (List格式)
```python
# v2新增：支持多个范围同时检索
rag_file_scope: List[str] = ["course", "global"]  
# 替代v1的单一范围字符串

# 实际检索逻辑
def retrieve_context(query: str, rag_file_scope: List[str]):
    results = []
    for scope in rag_file_scope:
        if scope == "course":
            results.extend(search_course_collection(query))
        elif scope == "global": 
            results.extend(search_global_collection(query))
        elif scope == "personal":
            results.extend(search_personal_collection(query))
    
    # 合并后按相似度排序，取前5个
    return sorted(results, key=lambda x: x.similarity, reverse=True)[:5]
```

## 🗄️ 数据模型设计

### 1. DocumentChunk 模型（文档切片）
```python
class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    # === 基础字段 ===
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False, index=True)
    chroma_id = Column(String(36), nullable=False, unique=True, index=True)  # UUID
    
    # === 切片内容 ===
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # 在文件中的序号
    token_count = Column(Integer, nullable=False)
    
    # === 向量信息 ===
    embedding_model = Column(String(50), default="text-embedding-ada-002")
    embedding_version = Column(String(20), default="1.0")
    
    # === 元数据 ===
    chunk_metadata = Column(JSON, nullable=True)  # 存储额外的元数据
    
    # === 质量评估 ===
    content_quality_score = Column(DECIMAL(3, 2), nullable=True)  # 内容质量评分
    is_active = Column(Boolean, default=True, index=True)  # 是否参与检索
    
    # === 统计信息 ===
    retrieval_count = Column(Integer, default=0)  # 被检索次数
    last_retrieved_at = Column(DateTime, nullable=True)  # 最后检索时间
    
    # === 时间戳 ===
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # === 复合索引 ===
    __table_args__ = (
        Index('idx_file_chunk', file_id, chunk_index),
        Index('idx_active_quality', is_active, content_quality_score),
        Index('idx_retrieval_stats', retrieval_count, last_retrieved_at),
    )
    
    # === 关系定义 ===
    file = relationship("File", back_populates="document_chunks")
    message_rag_sources = relationship("MessageRAGSource", back_populates="document_chunk")
```

### 2. AIModelConfig 模型（模型配置）
```python
class AIModelConfig(Base):
    __tablename__ = "ai_model_configs"
    
    # === 基础字段 ===
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(50), nullable=False, unique=True, index=True)  # Star, StarPlus, StarCode
    display_name = Column(String(100), nullable=False)  # 显示名称
    description = Column(Text, nullable=True)  # 模型描述
    
    # === OpenAI映射 ===
    openai_base_model = Column(String(100), nullable=False)  # gpt-4o-mini
    openai_search_model = Column(String(100), nullable=True)  # gpt-4o-mini-search-preview
    supports_search = Column(Boolean, default=False)
    
    # === 成本配置 ===
    input_cost_per_million = Column(DECIMAL(10, 6), nullable=False)  # 输入成本/百万token
    output_cost_per_million = Column(DECIMAL(10, 6), nullable=False)  # 输出成本/百万token
    
    # === 模型状态 ===
    is_active = Column(Boolean, default=True, index=True)
```


## 🚀 API 接口设计

### 路由前缀和标签
- **前缀**: `/ai`
- **标签**: `["AI智能服务"]` (在 main.py 中设置)
- **权限**: 基于用户认证和使用配额的权限控制

### AI对话接口

#### 1. POST /api/v1/ai/generate - AI对话生成
```python
Request: GenerateAIRequest
{
  "message": "请解释Python装饰器的概念",
  "chat_type": "course",
  "course_id": 1,
  "ai_model": "StarPlus",
  "search_enabled": false,
  "conversation_history": [
    {
      "role": "user",
      "content": "什么是Python?"
    },
    {
      "role": "assistant", 
      "content": "Python是一种编程语言..."
    }
  ],
  "file_context": "这里是用户上传的文件内容...",
  "custom_prompt": "请以教学的方式回答",
  "stream": false,
  "images": [
    {
      "type": "image_url",
      "image_url": {
        "url": "data:image/jpeg;base64,..."
      }
    }
  ]
}

Response 200: GenerateAIResponse
{
  "success": true,
  "data": {
    "content": "Python装饰器是一种设计模式...",
    "model_name": "StarPlus",
    "openai_model": "gpt-4o",
    "tokens_used": 450,
    "input_tokens": 200,
    "output_tokens": 250,
    "cost": 0.0045,
    "response_time_ms": 1200,
    "rag_sources": [
      {
        "source_file": "python_guide.pdf",
        "chunk_id": 15,
        "similarity_score": 0.85,
        "content_preview": "装饰器是Python中的高级特性...",
        "contributor": "triple u"
      }
    ],
    "context_info": {
      "total_context_tokens": 2000,
      "rag_chunks_used": 3,
      "file_context_tokens": 500
    }
  },
  "message": "AI响应生成成功"
}

# 流式响应 (stream: true)
Response: Server-Sent Events
Content-Type: text/event-stream

data: {"type": "start", "model": "StarPlus"}

data: {"type": "content", "content": "Python装饰器"}

data: {"type": "content", "content": "是一种设计模式"}

data: {"type": "rag_sources", "sources": [...]}

data: {"type": "usage", "tokens_used": 450, "cost": 0.0045, "response_time_ms": 1200}

data: {"type": "complete"}

Errors: 400(参数错误), 403(配额不足), 429(请求过频), 503(模型不可用)
```

#### 2. POST /api/v1/ai/generate-title - 生成聊天标题
```python
Request: GenerateTitleRequest
{
  "first_message": "请帮我解释Python装饰器的概念",
  "ai_response": "Python装饰器是一种设计模式...",
  "model": "Star"
}

Response 200: GenerateTitleResponse
{
  "success": true,
  "data": {
    "title": "Python装饰器学习",
    "model_used": "Star",
    "tokens_used": 25,
    "cost": 0.0001
  },
  "message": "标题生成成功"
}
```

#### 3. GET /api/v1/ai/models - 获取可用模型列表
```python
Response 200: AIModelsResponse
{
  "success": true,
  "data": {
    "models": [
      {
        "name": "Star",
        "display_name": "Star - 经济模式",
        "description": "基于gpt-4o-mini，适合日常对话",
        "supports_search": true,
        "supports_vision": false,
        "max_tokens": 1000,
        "input_cost_per_million": 0.15,
        "output_cost_per_million": 0.60,
        "user_access_level": "all"
      },
      {
        "name": "StarPlus",
        "display_name": "Star Plus - 高质量模式", 
        "description": "基于gpt-4o，提供最佳对话质量",
        "supports_search": true,
        "supports_vision": true,
        "max_tokens": 2000,
        "input_cost_per_million": 2.50,
        "output_cost_per_million": 10.00,
        "user_access_level": "all"
      },
      {
        "name": "StarCode", 
        "display_name": "Star Code - 代码专用",
        "description": "基于gpt-4.1，专为代码任务优化",
        "supports_search": false,  # ⚠️ 代码模型暂不支持搜索
        "supports_vision": false,
        "max_tokens": 4000,
        "input_cost_per_million": 2.00,
        "output_cost_per_million": 8.00,
        "user_access_level": "all",
        "recommended_for": ["代码编写", "算法解释", "技术文档"],
        "performance_level": "专业",
        "future_extensions": "计划扩展StarCodeMini、StarCodeNano等更多代码模型"
      }
    ],
    "total": 3
  }
}
```

### RAG文档处理接口

#### 1. POST /api/v1/ai/documents/process - 处理文档并向量化
```python
Request: ProcessDocumentRequest
{
  "file_id": 1,
  "processing_options": {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "quality_threshold": 0.7,
    "extract_metadata": true
  },
  "force_reprocess": false
}

Response 202: ProcessDocumentResponse
{
  "success": true,
  "data": {
    "task_id": "doc-process-uuid",
    "file_id": 1,
    "estimated_time_seconds": 120,
    "processing_status": "queued"
  },
  "message": "文档处理任务已启动"
}
```

#### 2. GET /api/v1/ai/documents/{file_id}/status - 获取文档处理状态
```python
Response 200: DocumentStatusResponse
{
  "success": true,
  "data": {
    "file_id": 1,
    "processing_status": "completed",
    "chunks_created": 25,
    "processing_time_seconds": 85,
    "collection_name": "course_1",
    "quality_stats": {
      "avg_quality_score": 0.82,
      "high_quality_chunks": 20,
      "low_quality_chunks": 5
    },
    "error_message": null
  }
}
```

#### 3. POST /api/v1/ai/search - RAG语义搜索
```python
Request: RAGSearchRequest
{
  "query": "Python装饰器的用法",
  "search_scope": {
    "type": "course",
    "course_id": 1
  },
  "limit": 5,
  "similarity_threshold": 0.7,
  "include_global": true
}

Response 200: RAGSearchResponse
{
  "success": true,
  "data": {
    "results": [
      {
        "chunk_id": 15,
        "file_id": 1,
        "file_name": "python_advanced.pdf",
        "content": "装饰器是Python中的高级特性...",
        "similarity_score": 0.85,
        "chunk_index": 15,
        "token_count": 150,
        "contributor": "triple u",
        "source_type": "course"
      }
    ],
    "total_results": 3,
    "search_time_ms": 45,
    "query_embedding_time_ms": 12
  }
}
```

#### 4. DELETE /api/v1/ai/documents/{file_id}/chunks - 删除文档向量
```python
Response 200: DeleteChunksResponse
{
  "success": true,
  "data": {
    "file_id": 1,
    "deleted_chunks": 25,
    "deleted_from_collections": ["course_1"],
    "cleanup_time_ms": 150
  },
  "message": "文档向量删除成功"
}
```

### AI统计和监控接口

#### 1. GET /api/v1/ai/usage/stats - 获取AI使用统计
```python
Query Parameters:
- date_range?: str = "7d" (1d, 7d, 30d, 90d)
- model?: str (过滤特定模型)
- user_id?: int (管理员查看特定用户)

Response 200: AIUsageStatsResponse
{
  "success": true,
  "data": {
    "period": "7d",
    "total_requests": 1250,
    "total_tokens": 45000,
    "total_cost": 15.75,
    "by_model": {
      "Star": {
        "requests": 800,
        "tokens": 25000,
        "cost": 6.25,
        "avg_response_time_ms": 1100
      },
      "StarPlus": {
        "requests": 350,
        "tokens": 15000,
        "cost": 8.50,
        "avg_response_time_ms": 1400
      },
      "StarCode": {
        "requests": 100,
        "tokens": 5000,
        "cost": 1.00,
        "avg_response_time_ms": 900
      }
    },
    "daily_breakdown": [
      {
        "date": "2025-01-27",
        "requests": 180,
        "tokens": 6500,
        "cost": 2.25
      }
    ]
  }
}
```

#### 2. GET /api/v1/ai/rag/collections - 获取RAG集合统计
```python
Response 200: RAGCollectionsResponse
{
  "success": true,
  "data": {
    "collections": [
      {
        "name": "course_1",
        "type": "course",
        "course_id": 1,
        "course_name": "Python编程基础",
        "total_chunks": 450,
        "total_files": 12,
        "total_tokens": 125000,
        "query_count": 89,
        "avg_response_time_ms": 35,
        "last_updated_at": "2025-01-27T10:00:00Z"
      },
      {
        "name": "global",
        "type": "global",
        "total_chunks": 1200,
        "total_files": 35,
        "total_tokens": 350000,
        "query_count": 245,
        "avg_response_time_ms": 42,
        "last_updated_at": "2025-01-27T09:30:00Z"
      }
    ],
    "total_collections": 2,
    "total_chunks": 1650,
    "total_files": 47
  }
}
```

## 📊 Schema 设计（FastAPI 2024最佳实践）

### 请求模型
```python
# === AI对话请求 ===
class GenerateAIRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="用户消息")
    chat_type: Literal["general", "course"] = Field("general", description="聊天类型")
    course_id: Optional[int] = Field(None, gt=0, description="课程ID（course类型时需要）")
    ai_model: Literal["Star", "StarPlus", "StarCode"] = Field("Star", description="AI模型")
    search_enabled: bool = Field(False, description="启用搜索功能")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(None, description="对话历史")
    file_context: Optional[str] = Field(None, max_length=50000, description="文件上下文")
    custom_prompt: Optional[str] = Field(None, max_length=2000, description="自定义提示")
    stream: bool = Field(False, description="启用流式响应")
    images: Optional[List[Dict[str, Any]]] = Field(None, description="图像输入")
    
    @field_validator('course_id')
    @classmethod
    def validate_course_id(cls, v, info):
        if info.data.get('chat_type') == 'course' and v is None:
            raise ValueError('课程聊天必须指定course_id')
        return v

class GenerateTitleRequest(BaseModel):
    first_message: str = Field(..., min_length=1, max_length=1000)
    ai_response: Optional[str] = Field(None, max_length=5000, description="AI响应内容")
    model: Literal["Star", "StarPlus", "StarCode"] = Field("Star", description="使用的模型")

# === RAG文档处理请求 ===
class ProcessDocumentRequest(BaseModel):
    file_id: int = Field(..., gt=0, description="文件ID")
    processing_options: Optional[Dict[str, Any]] = Field(None, description="处理选项")
    force_reprocess: bool = Field(False, description="强制重新处理")

class RAGSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="搜索查询")
    search_scope: Dict[str, Any] = Field(..., description="搜索范围配置")
    limit: int = Field(5, ge=1, le=20, description="结果数量限制")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="相似度阈值")
    include_global: bool = Field(True, description="包含全局文档")

# === AI使用统计请求 ===
class AIUsageStatsRequest(BaseModel):
    date_range: Literal["1d", "7d", "30d", "90d"] = Field("7d", description="时间范围")
    model: Optional[str] = Field(None, description="模型过滤")
    user_id: Optional[int] = Field(None, gt=0, description="用户过滤")
```

### 响应模型（遵循BaseResponse[T]模式）
```python
# === AI对话数据模型 ===
class AIResponseData(BaseModel):
    content: str
    model_name: str
    openai_model: str
    tokens_used: int
    input_tokens: int
    output_tokens: int
    cost: Decimal
    response_time_ms: int
    rag_sources: List[RAGSourceData] = []
    context_info: Optional[ContextInfoData] = None

class RAGSourceData(BaseModel):
    source_file: str
    chunk_id: int
    similarity_score: float
    content_preview: str
    contributor: Optional[str] = None
    source_type: str  # course, global, personal

class ContextInfoData(BaseModel):
    total_context_tokens: int
    rag_chunks_used: int
    file_context_tokens: int

# === AI模型数据模型 ===
class AIModelData(BaseModel):
    name: str
    display_name: str
    description: str
    supports_search: bool
    supports_vision: bool
    max_tokens: int
    input_cost_per_million: Decimal
    output_cost_per_million: Decimal
    user_access_level: str

# === RAG文档数据模型 ===
class DocumentChunkData(BaseModel):
    chunk_id: int
    file_id: int
    file_name: str
    content: str
    similarity_score: float
    chunk_index: int
    token_count: int
    contributor: Optional[str]
    source_type: str

class RAGCollectionData(BaseModel):
    name: str
    type: str
    course_id: Optional[int]
    course_name: Optional[str]
    total_chunks: int
    total_files: int
    total_tokens: int
    query_count: int
    avg_response_time_ms: int
    last_updated_at: datetime

# === AI统计数据模型 ===
class AIUsageStatsData(BaseModel):
    period: str
    total_requests: int
    total_tokens: int
    total_cost: Decimal
    by_model: Dict[str, ModelUsageData]
    daily_breakdown: List[DailyUsageData]

class ModelUsageData(BaseModel):
    requests: int
    tokens: int
    cost: Decimal
    avg_response_time_ms: int

class DailyUsageData(BaseModel):
    date: str
    requests: int
    tokens: int
    cost: Decimal

# === 响应模型 ===
class GenerateAIResponse(BaseResponse[AIResponseData]):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "success": True,
                "data": {
                    "content": "Python装饰器是一种设计模式...",
                    "model_name": "StarPlus",
                    "openai_model": "gpt-4o",
                    "tokens_used": 450,
                    "input_tokens": 200,
                    "output_tokens": 250,
                    "cost": 0.0045,
                    "response_time_ms": 1200,
                    "rag_sources": [],
                    "context_info": {
                        "total_context_tokens": 2000,
                        "rag_chunks_used": 3,
                        "file_context_tokens": 500
                    }
                },
                "message": "AI响应生成成功"
            }]
        }
    )

class AIModelsResponse(BaseResponse[Dict]):
    # data.models: List[AIModelData], data.total: int

class RAGSearchResponse(BaseResponse[Dict]):
    # data.results: List[DocumentChunkData], data.total_results: int

class AIUsageStatsResponse(BaseResponse[AIUsageStatsData]):
    pass
```

## 🛠️ Service 层设计

### AIService 类设计
```python
class AIService:
    """AI服务 - 对话生成和模型管理"""
    
    METHOD_EXCEPTIONS = {
        # AI对话生成
        'generate_response': {BadRequestError, ForbiddenError, QuotaExceededError, ServiceUnavailableError},
        'generate_response_stream': {BadRequestError, ForbiddenError, QuotaExceededError, ServiceUnavailableError},
        'generate_title': {BadRequestError, ServiceUnavailableError},
        
        # 模型管理
        'get_available_models': set(),  # 无特定异常
        'validate_model_access': {ForbiddenError, NotFoundError},
        
        # 使用统计
        'get_usage_stats': {ForbiddenError},
        'log_usage': {BadRequestError},
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.openai_client = self._initialize_openai_client()
        self.rag_service = RAGService(db)
```

### RAGService 类设计
```python
class RAGService:
    """RAG服务 - 文档处理和向量检索"""
    
    METHOD_EXCEPTIONS = {
        # 文档处理
        'process_document': {BadRequestError, NotFoundError, ForbiddenError},
        'get_processing_status': {NotFoundError, ForbiddenError},
        'delete_document_chunks': {NotFoundError, ForbiddenError},
        
        # 向量检索
        'semantic_search': {BadRequestError, ForbiddenError},
        'retrieve_context': {BadRequestError},
        
        # 集合管理
        'get_collections': {ForbiddenError},
        'update_collection_stats': set(),
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.chroma_client = self._initialize_chroma()
        self.embeddings = OpenAIEmbeddingsWrapper()
```

### 核心业务方法示例
```python
def generate_response(
    self, 
    request: GenerateAIRequest, 
    user_id: int
) -> Dict[str, Any]:
    """生成AI响应"""
    # 1. 验证用户配额
    if not self._check_user_quota(user_id, request.ai_model):
        raise QuotaExceededError("用户今日配额已用完")
    
    # 2. 获取模型配置
    model_config = self._get_model_config(request.ai_model)
    if not model_config.is_active:
        raise ServiceUnavailableError(f"模型 {request.ai_model} 当前不可用")
    
    # 3. 构建RAG上下文
    rag_sources = []
    if request.chat_type == "course" and request.course_id:
        rag_sources = self.rag_service.retrieve_context(
            request.message, 
            chat_type="course", 
            course_id=request.course_id,
            limit=5
        )
    elif request.chat_type == "general":
        rag_sources = self.rag_service.retrieve_context(
            request.message,
            chat_type="general",
            limit=5
        )
    
    # 4. 构建系统提示
    system_prompt = self._build_system_prompt(
        request.chat_type,
        rag_sources,
        request.file_context,
        request.custom_prompt
    )
    
    # 5. 准备OpenAI请求
    messages = [{"role": "system", "content": system_prompt}]
    if request.conversation_history:
        messages.extend(request.conversation_history)
    
    # 处理图像输入
    if request.images:
        content = [{"type": "text", "text": request.message}]
        content.extend(request.images)
        messages.append({"role": "user", "content": content})
    else:
        messages.append({"role": "user", "content": request.message})
    
    # 6. 调用OpenAI API
    start_time = time.time()
    try:
        openai_model = self._get_openai_model(request.ai_model, request.search_enabled)
        
        api_params = {
            "model": openai_model,
            "messages": messages,
            "max_tokens": model_config.max_tokens
        }
        
        if "search-preview" not in openai_model:
            api_params["temperature"] = model_config.temperature_default
        
        response = self.openai_client.chat.completions.create(**api_params)
        
        content = response.choices[0].message.content
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        
        # 7. 计算成本
        input_cost = (input_tokens / 1_000_000) * model_config.input_cost_per_million
        output_cost = (output_tokens / 1_000_000) * model_config.output_cost_per_million
        total_cost = input_cost + output_cost
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # 8. 记录使用日志
        self._log_usage(
            user_id=user_id,
            model_config=model_config,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_cost=total_cost,
            response_time_ms=response_time_ms,
            rag_sources_count=len(rag_sources)
        )
        
        return {
            "content": content,
            "model_name": request.ai_model,
            "openai_model": openai_model,
            "tokens_used": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": total_cost,
            "response_time_ms": response_time_ms,
            "rag_sources": [self._format_rag_source(source) for source in rag_sources],
            "context_info": {
                "total_context_tokens": sum(len(msg["content"]) for msg in messages) // 4,
                "rag_chunks_used": len(rag_sources),
                "file_context_tokens": len(request.file_context or "") // 4
            }
        }
        
    except Exception as e:
        # 记录错误日志
        self._log_error(user_id, request.ai_model, str(e))
        raise ServiceUnavailableError(f"AI服务调用失败: {str(e)}")

def process_document(
    self, 
    file_id: int, 
    user_id: int, 
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """处理文档并向量化"""
    # 1. 获取文件并检查权限
    file_record = self._get_file_with_permission(file_id, user_id)
    
    # 2. 检查是否需要重新处理
    if not options.get("force_reprocess", False):
        existing_chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.file_id == file_id
        ).count()
        
        if existing_chunks > 0:
            return {
                "file_id": file_id,
                "status": "already_processed",
                "chunks_created": existing_chunks
            }
    
    # 3. 获取物理文件路径
    physical_file_path = self._get_physical_file_path(file_record)
    
    # 4. 调用RAG处理
    result = self._process_file_with_rag(
        file_record,
        physical_file_path,
        options or {}
    )
    
    return result
```

## 🔐 权限控制设计

### 配额管理
```python
def _check_user_quota(self, user_id: int, model_name: str) -> bool:
    """检查用户配额"""
    today = datetime.now().date()
    
    # 获取今日使用量
    daily_usage = self.db.query(func.sum(AIUsageLog.total_tokens)).filter(
        AIUsageLog.user_id == user_id,
        func.date(AIUsageLog.created_at) == today,
        AIUsageLog.model_name == model_name
    ).scalar() or 0
    
    # 获取用户配额限制
    user = self.db.query(User).filter(User.id == user_id).first()
    model_config = self.db.query(AIModelConfig).filter(
        AIModelConfig.model_name == model_name
    ).first()
    
    daily_limit = self._get_daily_limit(user, model_config)
    
    return daily_usage < daily_limit

def _get_daily_limit(self, user: User, model_config: AIModelConfig) -> int:
    """获取用户每日限制"""
    if user.role == "admin":
        return float('inf')  # 管理员无限制
    
    if model_config.user_access_level == "premium" and user.role != "premium":
        return 0  # 无权限访问
    
    # 根据模型类型设置不同限制
    limits = {
        "Star": 10000,      # 经济模式限制较宽松
        "StarPlus": 5000,   # 高质量模式限制较严
        "StarCode": 3000    # 代码模式中等限制
    }
    
    return limits.get(model_config.model_name, 1000)
```

## 📁 文件系统结构

### 项目结构
```
src/ai/
├── __init__.py
├── models.py           # DocumentChunk, AIModelConfig, AIUsageLog, RAGCollection
├── schemas.py          # 请求/响应模型
├── service.py          # AIService (AI对话生成)
├── rag_service.py      # RAGService (文档处理和检索)
├── router.py           # API 路由
├── dependencies.py     # 配额检查和权限控制
├── exceptions.py       # AI相关异常
└── utils.py           # AI工具函数

src/ai/services/
├── __init__.py
├── model_manager.py    # AI模型配置管理
├── embeddings.py       # 向量嵌入服务
├── prompt_builder.py   # 提示词构建
└── usage_tracker.py    # 使用统计和配额管理

src/ai/integrations/
├── __init__.py
├── openai_client.py    # OpenAI API客户端
├── chroma_client.py    # ChromaDB向量存储客户端
└── langchain_utils.py  # LangChain工具集成
```

## 🧪 测试策略

### 单元测试覆盖
```python
class TestAIService:
    """AI服务单元测试"""
    
    def test_generate_response_success(self, ai_service, regular_user):
        """测试AI响应生成成功"""
        
    def test_model_quota_enforcement(self, ai_service, regular_user):
        """测试模型配额限制"""
        
    def test_cost_calculation_accuracy(self, ai_service, model_configs):
        """测试成本计算准确性"""

class TestRAGService:
    """RAG服务单元测试"""
    
    def test_document_processing_success(self, rag_service, test_pdf):
        """测试文档处理成功"""
        
    def test_semantic_search_relevance(self, rag_service, processed_docs):
        """测试语义搜索相关性"""
        
    def test_collection_isolation(self, rag_service, course_docs, global_docs):
        """测试集合隔离"""

class TestAIAPI:
    """AI API集成测试"""
    
    def test_stream_response(self, client, user_headers):
        """测试流式响应"""
        
    def test_multimodal_input(self, client, user_headers, test_image):
        """测试多模态输入"""
        
    def test_rag_integration(self, client, user_headers, processed_course):
        """测试RAG集成"""
```

## 🚀 性能优化

### 向量检索优化
- **批量嵌入**: 文档处理时批量生成嵌入向量
- **缓存策略**: 常用查询结果缓存
- **索引优化**: ChromaDB索引和查询优化
- **异步处理**: 文档处理异步队列

### AI调用优化
- **连接池**: OpenAI API连接复用
- **请求合并**: 相似请求合并处理
- **模型选择**: 自动选择最适合的模型
- **成本控制**: 智能的成本预算管理

## 🔗 与其他模块的集成

### Chat 模块集成
- AI响应生成
- 流式对话支持
- 上下文管理
- 消息历史处理

### Storage 模块集成
- 文档向量化处理
- 文件权限验证
- 处理状态同步
- 文件删除清理

### Course 模块集成
- 课程文档隔离
- 课程权限继承
- 学习统计分析
- 课程RAG集合

### Admin 模块集成
- 使用统计报告
- 成本分析
- 配额管理
- 系统监控

## 📊 监控和统计

### AI使用监控
- 模型调用频率
- Token消耗统计
- 成本分析报告
- 用户使用模式

### RAG性能监控
- 检索响应时间
- 相关性评分分布
- 文档覆盖率
- 查询模式分析

### 质量监控
- 响应质量评估
- 用户满意度统计
- 错误率监控
- 系统可用性追踪

## 🎯 总结

AI模块严格遵循FastAPI 2024最佳实践和Campus LLM System的架构标准：

- ✅ **Service API装饰器**: 自动生成完整的OpenAPI文档
- ✅ **统一响应格式**: BaseResponse[T]泛型设计，message/data分离
- ✅ **现代依赖注入**: 类型安全的配额和权限控制
- ✅ **异常处理自动化**: METHOD_EXCEPTIONS声明
- ✅ **v1 API兼容**: 保持模型配置和调用接口兼容
- ✅ **流式响应支持**: Server-Sent Events实时AI对话
- ✅ **RAG集成**: 完整的文档处理和语义检索功能
- ✅ **成本追踪**: 精确的Token计算和费用统计
- ✅ **配额管理**: 多层级的使用限制和控制
- ✅ **完整测试覆盖**: 单元测试+API集成测试+性能测试

该模块为Campus LLM System提供了强大、智能、可控的AI服务解决方案，支持多模型选择、RAG增强检索、流式对话和精确的成本控制，确保了优秀的用户体验和系统性能。