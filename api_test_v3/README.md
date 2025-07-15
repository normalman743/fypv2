# API测试工具 V3.0

## 概述

这是一个模块化的API测试工具，用于测试校园LLM系统的各项功能。

## 目录结构

```
api_test_v3/
├── config.py          # 配置文件
├── utils.py           # 通用工具函数
├── database.py        # 数据库操作模块
├── reset_system.py    # 系统重置功能
├── README.md          # 使用说明
└── requirements.txt   # 依赖包
```

## 功能模块

### 1. 系统重置 (reset_system.py)

**功能**: 完整重置系统到初始状态

**包含操作**:
- 清空所有数据库表
- 重置自增ID
- 创建默认用户 (admin, user)
- 创建默认邀请码
- 清空本地存储目录
- 清空向量数据库

**使用方法**:
```bash
cd api_test_v3
python reset_system.py
```

### 2. 配置管理 (config.py)

**功能**: 统一管理所有配置信息

**包含配置**:
- API服务配置
- 数据库连接配置
- 测试用户配置
- 文件路径配置

### 3. 工具函数 (utils.py)

**功能**: 提供通用的工具函数

**主要功能**:
- API客户端封装
- 请求响应处理
- 服务状态检查
- 日志记录

### 4. 数据库操作 (database.py)

**功能**: 数据库相关操作

**主要功能**:
- 数据库连接管理
- 表数据清空
- 默认数据创建
- 存储目录管理

## 默认配置

### 测试用户
- **admin**: 管理员账户
  - 用户名: admin
  - 邮箱: admin@test.com
  - 密码: admin123456
  - 角色: admin

- **user**: 普通用户账户
  - 用户名: user
  - 邮箱: user@test.com
  - 密码: user123456
  - 角色: user

### 邀请码
- **ADMIN2024**: 管理员邀请码
- **USER2024**: 普通用户邀请码

## 环境要求

1. Python 3.7+
2. MySQL数据库访问权限
3. API服务运行在localhost:8000

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用注意事项

1. **数据库配置**: 确保数据库连接信息正确
2. **服务状态**: 确保API服务正在运行
3. **权限问题**: 确保有足够的文件系统权限
4. **备份数据**: 重置操作不可逆，请提前备份重要数据

## 环境变量

```bash
export DB_USER="your_db_user"
export DB_PASSWORD="your_db_password"
```

## 扩展开发

### 添加新的测试模块

1. 在根目录创建新的Python文件
2. 导入相关工具类
3. 编写测试函数
4. 更新README文档

### 示例模块结构

```python
from utils import APIClient, print_response
from config import test_config

def test_new_feature():
    """测试新功能"""
    client = APIClient()
    # 测试逻辑
    pass

if __name__ == "__main__":
    test_new_feature()
```

## 版本历史

- **V3.0**: 模块化重构，支持系统重置
- **V2.x**: 统一文件系统测试
- **V1.x**: 基础API测试

## 联系方式

如有问题请联系开发团队。