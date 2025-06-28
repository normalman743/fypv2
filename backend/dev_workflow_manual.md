# 校园LLM系统 - 简化开发工作流

## 🚀 快速开发流程

### 1. 从API文档到代码实现

```bash
# 工作流程：API文档 → Schema → Service → Router → Test
```

#### 步骤1：创建Schema（数据模型）
```python
# app/schemas/example.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ExampleCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ExampleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
```

#### 步骤2：实现Service（业务逻辑）
```python
# app/services/example_service.py
from sqlalchemy.orm import Session
from app.models.example import Example
from app.schemas.example import ExampleCreate

class ExampleService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_example(self, data: ExampleCreate, user_id: int):
        example = Example(**data.dict(), user_id=user_id)
        self.db.add(example)
        self.db.commit()
        self.db.refresh(example)
        return example
```

#### 步骤3：编写Router（API端点）
```python
# app/api/v1/example.py
from fastapi import APIRouter, Depends
from app.schemas.example import ExampleCreate, ExampleResponse
from app.services.example_service import ExampleService
from app.dependencies import get_current_user, get_db

router = APIRouter(prefix="/examples", tags=["examples"])

@router.post("/", response_model=ExampleResponse)
def create_example(
    data: ExampleCreate,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    service = ExampleService(db)
    return service.create_example(data, current_user.id)
```

#### 步骤4：编写测试
```python
# tests/test_example.py
def test_create_example(client, authenticated_user):
    response = client.post("/api/v1/examples", 
        headers={"Authorization": f"Bearer {authenticated_user}"},
        json={"name": "测试", "description": "描述"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "测试"
```

### 2. 快速开发命令

```bash
# 启动开发服务器
uvicorn app.main:app --reload --port 8000

# 运行测试
pytest tests/ -v

# 格式化代码
black app/ tests/

# 数据库迁移
alembic revision --autogenerate -m "描述"
alembic upgrade head
```

## 📁 项目结构（简化版）

```
backend/
├── app/
│   ├── main.py              # FastAPI应用入口
│   ├── api/v1/              # API路由
│   ├── models/              # 数据库模型
│   ├── schemas/             # Pydantic模型
│   ├── services/            # 业务逻辑
│   └── dependencies.py      # 依赖注入
├── tests/                   # 测试文件
├── migrations/              # 数据库迁移
└── requirements.txt         # 依赖包
```

## 🔧 开发环境设置

### 快速启动
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置环境变量
cp .env.example .env
# 编辑 .env 文件

# 3. 启动数据库（如果使用Docker）
docker-compose up -d db

# 4. 运行迁移
alembic upgrade head

# 5. 启动应用
uvicorn app.main:app --reload
```

## 📋 开发规范

### 代码风格
- 使用 **Black** 自动格式化
- 使用 **isort** 整理导入
- 遵循 **PEP 8** 规范

### 提交规范
```bash
# 简化的提交格式
feat: 添加用户认证功能
fix: 修复登录bug
docs: 更新API文档
```

### 分支策略
```bash
main          # 主分支
develop       # 开发分支
feature/xxx   # 功能分支
```

## 🧪 测试策略

### 测试类型
1. **单元测试** - 测试单个函数/方法
2. **集成测试** - 测试API端点
3. **端到端测试** - 测试完整流程

### 测试命令
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_auth.py

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

## 🚀 部署流程

### 开发环境
```bash
# 本地开发
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 生产环境
```bash
# 使用Docker部署
docker build -t campus-llm .
docker run -p 8000:8000 campus-llm
```

## 🔍 调试技巧

### 常用调试命令
```bash
# 查看日志
tail -f logs/app.log

# 数据库连接测试
python -c "from app.database import engine; print(engine.execute('SELECT 1').scalar())"

# API测试
curl -X GET http://localhost:8000/health
```

### 常见问题
1. **数据库连接失败** - 检查 `.env` 配置
2. **API响应慢** - 检查数据库查询和索引
3. **文件上传失败** - 检查存储路径权限

## 📚 快速参考

### API开发模板
```python
# 1. Schema
class YourModelCreate(BaseModel):
    field1: str
    field2: Optional[int] = None

# 2. Service
class YourService:
    def create(self, data: YourModelCreate):
        # 业务逻辑
        pass

# 3. Router
@router.post("/")
def create_item(data: YourModelCreate):
    service = YourService()
    return service.create(data)

# 4. Test
def test_create_item(client):
    response = client.post("/api/v1/items", json={"field1": "value"})
    assert response.status_code == 200
```

### 数据库操作
```python
# 创建记录
item = Model(**data.dict())
db.add(item)
db.commit()

# 查询记录
items = db.query(Model).filter(Model.user_id == user_id).all()

# 更新记录
item.name = "新名称"
db.commit()

# 删除记录
db.delete(item)
db.commit()
```

---

## 🎯 开发原则

1. **快速迭代** - 先实现基本功能，再优化
2. **测试驱动** - 编写测试确保代码质量
3. **文档同步** - API文档和代码保持同步
4. **简单优先** - 避免过度设计

这个简化的工作流专注于快速从API文档到可运行的后端代码，提高开发效率。

# 数据库配置
DATABASE_URL=mysql+pymysql://campus_user:CampusLLM123!@39.108.113.103:3306/campus_llm
TEST_DATABASE_URL=sqlite:///./test.db

# JWT配置
SECRET_KEY=your-secret-key-here