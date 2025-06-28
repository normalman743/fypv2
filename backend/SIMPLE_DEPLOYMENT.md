# 🚀 简单直接部署指南

## 📍 **当前位置确认**
```bash
# 你现在在：
/var/www/api.icu.584743.xyz/fypv2

# 进入backend目录
cd backend
pwd  # 应该显示：/var/www/api.icu.584743.xyz/fypv2/backend
```

## ⚡ **直接部署（推荐）**

### **1. 安装依赖**
```bash
# 安装Redis
sudo apt update
sudo apt install -y redis-server python3-pip python3-venv

# 启动Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 验证Redis
redis-cli ping  # 应该返回 PONG
```

### **2. 创建Python环境**
```bash
# 在backend目录下
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### **3. 配置环境变量**
```bash
# 复制配置文件
cp .env.production .env

# 编辑配置
nano .env
```

**重要配置项：**
```bash
DEBUG=False
DATABASE_URL=mysql+pymysql://campus_user:CampusLLM123!@39.108.113.103:3306/campus_llm
REDIS_URL=redis://localhost:6379/0
UPLOAD_DIR=/var/www/api.icu.584743.xyz/uploads
CORS_ORIGINS=https://icu.584743.xyz
SECRET_KEY=请生成一个安全密钥
OPENAI_API_KEY=你的OpenAI密钥
```

### **4. 创建必要目录**
```bash
# 创建上传目录
mkdir -p /var/www/api.icu.584743.xyz/uploads
mkdir -p /var/www/api.icu.584743.xyz/logs
mkdir -p data/chroma

# 设置权限
sudo chown -R $USER:$USER /var/www/api.icu.584743.xyz/uploads
sudo chmod -R 755 /var/www/api.icu.584743.xyz/uploads
```

### **5. 测试数据库连接**
```bash
# 激活虚拟环境
source venv/bin/activate

# 测试连接
python3 -c "
from app.models.database import engine
try:
    engine.connect()
    print('✅ 数据库连接成功')
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
"
```

### **6. 启动服务**
```bash
# 确保在backend目录且虚拟环境已激活
cd /var/www/api.icu.584743.xyz/fypv2/backend
source venv/bin/activate

# 启动FastAPI应用
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /var/www/api.icu.584743.xyz/logs/app.log 2>&1 &

# 启动Celery Worker（异步任务处理）
nohup celery -A app.celery_app worker --loglevel=info --concurrency=4 > /var/www/api.icu.584743.xyz/logs/celery.log 2>&1 &

# 可选：启动Flower监控
nohup celery -A app.celery_app flower --port=5555 > /var/www/api.icu.584743.xyz/logs/flower.log 2>&1 &
```

### **7. 验证服务**
```bash
# 检查进程
ps aux | grep uvicorn
ps aux | grep celery

# 检查端口
netstat -tlnp | grep :8000
netstat -tlnp | grep :5555

# 测试API
curl http://localhost:8000/health
curl http://localhost:8000/
```

## 🔧 **配置Nginx（如果还没配置）**

```bash
# 创建Nginx配置
sudo nano /etc/nginx/sites-available/api.icu.584743.xyz
```

**Nginx配置内容：**
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
        
        # 文件上传大小限制
        client_max_body_size 50M;
    }

    # 监控界面（可选）
    location /flower/ {
        proxy_pass http://127.0.0.1:5555/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/api.icu.584743.xyz /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 📊 **服务管理脚本**

创建管理脚本方便操作：

```bash
# 创建启动脚本
cat > /var/www/api.icu.584743.xyz/start_services.sh << 'EOF'
#!/bin/bash
cd /var/www/api.icu.584743.xyz/fypv2/backend
source venv/bin/activate

echo "启动FastAPI应用..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /var/www/api.icu.584743.xyz/logs/app.log 2>&1 &
echo "FastAPI PID: $!"

echo "启动Celery Worker..."
nohup celery -A app.celery_app worker --loglevel=info --concurrency=4 > /var/www/api.icu.584743.xyz/logs/celery.log 2>&1 &
echo "Celery PID: $!"

echo "启动Flower监控..."
nohup celery -A app.celery_app flower --port=5555 > /var/www/api.icu.584743.xyz/logs/flower.log 2>&1 &
echo "Flower PID: $!"

echo "✅ 所有服务启动完成"
EOF

chmod +x /var/www/api.icu.584743.xyz/start_services.sh
```

```bash
# 创建停止脚本
cat > /var/www/api.icu.584743.xyz/stop_services.sh << 'EOF'
#!/bin/bash

echo "停止FastAPI应用..."
pkill -f "uvicorn app.main:app"

echo "停止Celery Worker..."
pkill -f "celery.*worker"

echo "停止Flower监控..."
pkill -f "celery.*flower"

echo "✅ 所有服务已停止"
EOF

chmod +x /var/www/api.icu.584743.xyz/stop_services.sh
```

## 🔍 **故障排除**

### **常见问题**

1. **Redis连接失败**
```bash
sudo systemctl status redis-server
sudo systemctl restart redis-server
```

2. **数据库连接失败**
```bash
# 检查数据库配置
mysql -h 39.108.113.103 -u campus_user -p
```

3. **权限问题**
```bash
sudo chown -R $USER:$USER /var/www/api.icu.584743.xyz/
```

4. **查看日志**
```bash
tail -f /var/www/api.icu.584743.xyz/logs/app.log
tail -f /var/www/api.icu.584743.xyz/logs/celery.log
```

## ✅ **部署验证**

```bash
# 1. 健康检查
curl http://api.icu.584743.xyz/health

# 2. API测试
curl http://api.icu.584743.xyz/

# 3. 查看进程
ps aux | grep -E "(uvicorn|celery)"

# 4. 查看日志
tail -f /var/www/api.icu.584743.xyz/logs/app.log
```

## 🎯 **为什么不用Docker？**

✅ **直接部署优势：**
- 更简单的配置和调试
- 直接访问文件和日志
- 更好的性能（无容器开销）
- 更容易排查问题
- 更灵活的服务管理

❌ **Docker的复杂性：**
- 需要学习Docker概念
- 文件挂载和权限问题
- 网络配置复杂
- 调试困难

**你的选择是对的！直接部署更适合这种场景。**