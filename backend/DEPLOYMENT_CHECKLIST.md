# 🚀 生产部署检查清单

## 📋 部署前必须完成的任务

### 1. 🔧 **环境配置与安全**

#### **环境变量配置**
- [ ] 生产环境 `.env` 配置
  ```bash
  # 生产环境配置
  DEBUG=False
  SECRET_KEY=<安全的随机密钥>
  DATABASE_URL=mysql+pymysql://user:pass@host:3306/dbname
  OPENAI_API_KEY=sk-your-real-key
  
  # 服务器配置
  HOST=0.0.0.0
  PORT=8000
  WORKERS=4
  ```

- [ ] **安全密钥生成**
  ```python
  import secrets
  print(secrets.token_urlsafe(32))  # 生成安全的SECRET_KEY
  ```

#### **数据库配置**
- [ ] MySQL/PostgreSQL 生产数据库设置
- [ ] 数据库连接池配置
- [ ] 数据库备份策略
- [ ] 数据库迁移脚本测试

### 2. 🗄️ **文件存储系统**

#### **当前问题：文件存储未实现**
```python
# app/services/file_service.py 第78行
# TODO: Implement actual file storage logic here
```

**需要实现：**
- [ ] **本地文件存储**
  ```python
  UPLOAD_DIR = "/var/uploads"
  # 文件路径: /var/uploads/{user_id}/{course_id}/{filename}
  ```

- [ ] **云存储集成** (推荐)
  ```python
  # 选择一种：AWS S3 / 阿里云OSS / 腾讯云COS
  # 好处：可靠性高、扩展性好、CDN加速
  ```

- [ ] **文件去重机制**
  ```python
  # 基于文件哈希值去重，避免重复存储
  file_hash = hashlib.sha256(file_content).hexdigest()
  ```

### 3. 🔄 **异步任务处理**

#### **当前问题：文件处理阻塞请求**
```python
# 文件上传时同步处理RAG，会导致请求超时
self._process_file_with_rag(file_record, file_content)
```

**需要实现：**
- [ ] **Celery异步任务队列**
  ```python
  # 安装依赖
  pip install celery redis

  # 异步处理文件
  @celery.task
  def process_file_async(file_id):
      # RAG处理逻辑
      pass
  ```

- [ ] **Redis配置**
  ```python
  # 作为Celery broker和结果存储
  CELERY_BROKER_URL = "redis://localhost:6379/0"
  CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
  ```

### 4. 📊 **监控与日志**

- [ ] **结构化日志**
  ```python
  import structlog
  
  # 替换print语句为结构化日志
  logger = structlog.get_logger()
  logger.info("file_processed", file_id=file_id, processing_time=time)
  ```

- [ ] **性能监控**
  ```python
  # 集成 Prometheus + Grafana
  from prometheus_client import Counter, Histogram
  
  file_upload_counter = Counter('file_uploads_total')
  processing_time_histogram = Histogram('file_processing_seconds')
  ```

- [ ] **错误追踪**
  ```python
  # 集成 Sentry
  import sentry_sdk
  sentry_sdk.init(dsn="your-sentry-dsn")
  ```

### 5. 🔒 **安全加固**

- [ ] **API限流**
  ```python
  from slowapi import Limiter
  
  @limiter.limit("10/minute")  # 限制上传频率
  async def upload_file():
      pass
  ```

- [ ] **文件类型验证**
  ```python
  ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.md'}
  MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
  ```

- [ ] **CORS策略**
  ```python
  # 生产环境限制域名
  allow_origins=["https://yourdomain.com"]
  ```

### 6. 🎯 **性能优化**

#### **数据库优化**
- [ ] **索引优化**
  ```sql
  -- 添加复合索引
  CREATE INDEX idx_files_course_user ON files(course_id, user_id);
  CREATE INDEX idx_messages_chat_created ON messages(chat_id, created_at);
  ```

- [ ] **查询优化**
  ```python
  # 使用joinedload减少N+1查询
  files = db.query(File).options(
      joinedload(File.course),
      joinedload(File.folder)
  ).all()
  ```

#### **ChromaDB优化**
- [ ] **持久化配置**
  ```python
  # 生产环境使用专用目录
  CHROMA_DATA_DIR = "/var/lib/chroma"
  ```

- [ ] **向量维度优化**
  ```python
  # 考虑使用更小的embedding模型以提高速度
  # text-embedding-ada-002 (1536维) vs text-embedding-3-small (512维)
  ```

### 7. 🐳 **容器化部署**

- [ ] **Dockerfile**
  ```dockerfile
  FROM python:3.11-slim
  
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install -r requirements.txt
  
  COPY . .
  EXPOSE 8000
  
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

- [ ] **docker-compose.yml**
  ```yaml
  version: '3.8'
  services:
    web:
      build: .
      ports:
        - "8000:8000"
      environment:
        - DATABASE_URL=mysql://...
      depends_on:
        - db
        - redis
    
    db:
      image: mysql:8.0
      environment:
        MYSQL_DATABASE: campus_llm
    
    redis:
      image: redis:alpine
  ```

### 8. 🧪 **生产测试**

- [ ] **负载测试**
  ```python
  # 使用locust进行压力测试
  pip install locust
  
  # 测试文件上传并发
  # 测试聊天API响应时间
  # 测试RAG检索性能
  ```

- [ ] **端到端测试**
  ```python
  # 完整流程测试：注册→登录→上传文件→等待处理→创建聊天→发送消息
  ```

### 9. 📦 **部署脚本**

- [ ] **自动化部署**
  ```bash
  #!/bin/bash
  # deploy.sh
  
  # 1. 拉取代码
  git pull origin main
  
  # 2. 安装依赖
  pip install -r requirements.txt
  
  # 3. 数据库迁移
  alembic upgrade head
  
  # 4. 重启服务
  supervisorctl restart campus_llm
  ```

### 10. 🔧 **配置管理**

- [ ] **配置文件分离**
  ```python
  # config/
  ├── development.py
  ├── production.py
  └── testing.py
  ```

## 📊 **当前状态评估**

### ✅ **已完成**
- API实现 (95%完成率)
- RAG集成 (OpenAI + ChromaDB)
- 状态跟踪系统
- 错误处理机制
- 测试覆盖

### ⚠️ **需要完成**
1. **文件存储系统** (高优先级)
2. **异步任务处理** (高优先级)  
3. **生产数据库配置** (高优先级)
4. **安全加固** (中优先级)
5. **监控日志** (中优先级)

### 🎯 **建议部署顺序**

#### **阶段1：基础部署** (1-2天)
1. 实现文件存储系统
2. 配置生产数据库
3. 基础安全设置

#### **阶段2：性能优化** (2-3天)
1. 实现异步任务处理
2. 添加监控日志
3. 负载测试优化

#### **阶段3：高级功能** (1-2天)
1. 容器化部署
2. 自动化脚本
3. 生产监控

## 💡 **部署建议**

### **推荐技术栈**
- **服务器**: Ubuntu 20.04 LTS
- **Web服务器**: Nginx (反向代理)
- **应用服务器**: Uvicorn + Gunicorn
- **数据库**: MySQL 8.0
- **缓存**: Redis
- **任务队列**: Celery
- **容器**: Docker + Docker Compose

### **最小可行部署**
如果时间紧急，可以先完成：
1. 文件本地存储 (临时方案)
2. 同步处理保持现状 (小文件可接受)
3. 基础安全配置
4. 简单监控

**预计工作量**: 3-5天完成基础部署，7-10天完成完整的生产级部署。