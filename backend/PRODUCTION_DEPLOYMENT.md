# 🚀 生产环境部署指南

## 📋 服务器配置信息

- **后端API**: api.icu.584743.xyz
- **前端**: icu.584743.xyz  
- **数据库**: 39.108.113.103:3306
- **用户**: campus_user
- **密码**: CampusLLM123!

## 🛠️ 部署步骤

### 1. 服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要软件
sudo apt install -y python3.11 python3.11-venv python3-pip
sudo apt install -y redis-server nginx git

# 安装Docker (可选)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt install -y docker-compose
```

### 2. 克隆项目

```bash
cd /opt
sudo git clone https://github.com/normalman743/fypv2.git
sudo chown -R $USER:$USER fypv2
cd fypv2/backend
```

### 3. 创建Python虚拟环境

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制生产配置
cp .env.production .env

# 编辑配置文件
nano .env
```

**重要配置项：**
```bash
# 生成安全密钥
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 在.env中设置
SECRET_KEY=<生成的安全密钥>
OPENAI_API_KEY=<你的OpenAI密钥>
CORS_ORIGINS=https://icu.584743.xyz
```

### 5. 数据库初始化

```bash
# 测试数据库连接
python3 -c "
from app.models.database import engine
try:
    engine.connect()
    print('✅ 数据库连接成功')
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
"

# 创建数据库表
python3 -c "
from app.models.database import Base, engine
Base.metadata.create_all(bind=engine)
print('✅ 数据库表创建完成')
"
```

### 6. 启动服务

#### 方式一：使用Docker Compose（推荐）

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f web
docker-compose logs -f worker
```

#### 方式二：手动启动

```bash
# 1. 启动Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 2. 启动FastAPI应用
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/app.log 2>&1 &

# 3. 启动Celery Worker
nohup celery -A app.celery_app worker --loglevel=info --concurrency=4 > logs/celery.log 2>&1 &

# 4. 启动Flower监控（可选）
nohup celery -A app.celery_app flower --port=5555 > logs/flower.log 2>&1 &
```

### 7. 配置Nginx反向代理

```bash
sudo nano /etc/nginx/sites-available/api.icu.584743.xyz
```

**Nginx配置：**
```nginx
server {
    listen 80;
    server_name api.icu.584743.xyz;

    # API代理
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 处理大文件上传
        client_max_body_size 50M;
        proxy_request_buffering off;
    }

    # Flower监控（可选）
    location /flower/ {
        proxy_pass http://127.0.0.1:5555/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/api.icu.584743.xyz /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 8. 配置SSL证书（推荐）

```bash
# 安装Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d api.icu.584743.xyz

# 自动续期
sudo crontab -e
# 添加：0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 服务验证

### 1. 基础服务检查

```bash
# 检查服务状态
curl http://api.icu.584743.xyz/health
curl http://api.icu.584743.xyz/

# 检查Redis连接
redis-cli ping

# 检查Celery Worker
celery -A app.celery_app inspect active
```

### 2. 功能测试

```bash
# 测试API端点
curl -X GET "http://api.icu.584743.xyz/api/v1/health"

# 测试文件上传（需要认证token）
# curl -X POST "http://api.icu.584743.xyz/api/v1/files/upload" \
#      -H "Authorization: Bearer <token>" \
#      -F "file=@test.txt" \
#      -F "course_id=1" \
#      -F "folder_id=1"
```

## 🔧 API变更说明

### 新增API端点

1. **任务进度查询**
   ```
   GET /api/v1/tasks/{task_id}/progress
   ```
   
   **响应示例：**
   ```json
   {
     "success": true,
     "data": {
       "task_id": "abc123",
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

2. **文件状态查询（增强）**
   ```
   GET /api/v1/files/{file_id}/status
   ```
   
   **响应保持不变，但处理逻辑优化为异步**

### 前端集成变更

**文件上传流程变更：**

```javascript
// 1. 上传文件（立即返回）
const uploadResponse = await fetch('/api/v1/files/upload', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});

const fileData = await uploadResponse.json();
console.log('文件上传成功，开始后台处理'); // 立即响应

// 2. 轮询文件状态
const pollFileStatus = async (fileId) => {
  const interval = setInterval(async () => {
    const response = await fetch(`/api/v1/files/${fileId}/status`);
    const data = await response.json();
    
    if (data.data.rag_ready) {
      console.log('文件处理完成，可用于对话！');
      clearInterval(interval);
      onFileReady(fileId);
    } else if (data.data.processing_status === 'failed') {
      console.log('文件处理失败');
      clearInterval(interval);
      onFileError(fileId);
    }
  }, 2000);
};

pollFileStatus(fileData.data.file.id);
```

**性能提升：**
- 🚀 文件上传响应时间：从4-15秒 → 0.5秒
- ⚡ 用户体验：立即反馈 + 后台处理
- 📈 并发处理：支持多文件同时处理

## 🔍 监控和维护

### 1. 服务监控

```bash
# 查看服务状态
docker-compose ps
systemctl status nginx

# 查看日志
tail -f logs/app.log
tail -f logs/celery.log
docker-compose logs -f worker

# 监控Redis
redis-cli monitor

# Flower任务监控
# 访问：http://api.icu.584743.xyz/flower/
```

### 2. 性能监控

```bash
# 查看系统资源
htop
df -h
free -h

# 查看任务队列状态
celery -A app.celery_app inspect active
celery -A app.celery_app inspect stats
```

### 3. 故障排除

**常见问题：**

1. **Celery任务失败**
   ```bash
   # 查看失败任务
   celery -A app.celery_app inspect failed
   
   # 重启Worker
   docker-compose restart worker
   ```

2. **数据库连接问题**
   ```bash
   # 测试连接
   mysql -h 39.108.113.103 -u campus_user -p campus_llm
   ```

3. **Redis连接问题**
   ```bash
   # 检查Redis状态
   redis-cli ping
   systemctl status redis-server
   ```

## 🔒 安全注意事项

1. **防火墙配置**
   ```bash
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 80/tcp   # HTTP
   sudo ufw allow 443/tcp  # HTTPS
   sudo ufw enable
   ```

2. **定期更新**
   ```bash
   # 系统更新
   sudo apt update && sudo apt upgrade
   
   # 依赖更新
   pip install --upgrade -r requirements.txt
   ```

3. **备份策略**
   ```bash
   # 数据库备份
   mysqldump -h 39.108.113.103 -u campus_user -p campus_llm > backup.sql
   
   # 应用备份
   tar -czf backup_$(date +%Y%m%d).tar.gz /opt/fypv2
   ```

## 🎯 部署完成检查清单

- [ ] 服务器基础软件安装完成
- [ ] 项目代码部署到 /opt/fypv2
- [ ] Python虚拟环境创建并安装依赖
- [ ] 环境变量配置正确（.env文件）
- [ ] 数据库连接测试成功
- [ ] Redis服务启动
- [ ] FastAPI应用启动（端口8000）
- [ ] Celery Worker启动
- [ ] Nginx反向代理配置
- [ ] SSL证书配置（推荐）
- [ ] API健康检查通过
- [ ] 文件上传功能测试
- [ ] 异步任务处理测试
- [ ] 监控系统配置

**部署完成后，你的系统将支持：**
✅ 高性能文件上传（秒级响应）
✅ 后台异步RAG处理
✅ 实时任务进度监控
✅ 多文件并发处理
✅ 生产级错误处理和监控