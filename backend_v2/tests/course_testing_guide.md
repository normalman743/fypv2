# Course模块测试指南

## 概述

Course模块测试计划：当前专注于功能开发完成度，后续将进行全面的End-to-End API测试以确保系统质量。

## 测试策略

### 当前状态
- ✅ 功能模块已完成开发
- ✅ FastAPI四层架构已规范化
- ✅ Service异常处理已完善
- 🔄 待进行：End-to-End API测试

### 后续测试计划

我们将在功能开发完成后，进行全面的End-to-End API测试，包括：

1. **完整API集成测试**
   - 学期管理API端点测试
   - 课程管理API端点测试
   - 权限和认证验证
   - 数据验证和错误处理

2. **Service层业务逻辑测试**
   - SemesterService完整功能测试
   - CourseService完整功能测试
   - 异常处理覆盖测试
   - 数据隔离和安全测试

3. **系统集成测试**
   - 跨模块功能验证
   - 数据库事务完整性
   - 性能和并发测试

## 测试环境准备

```bash
# 进入backend_v2目录
cd backend_v2

# 激活虚拟环境
source v2env/bin/activate

# 确保依赖已安装
pip install -r requirements.txt

# 数据库配置检查
# 检查.env.test文件中的DATABASE_URL配置
```

## 运行测试

### 基本命令
```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定模块测试
python -m pytest tests/test_course_*.py -v

# 生成覆盖率报告
python -m pytest tests/ --cov=src.course --cov-report=html
```

## 测试质量目标

### 覆盖范围目标
- **API端点覆盖**: 100%
- **业务逻辑覆盖**: 完整的成功和失败路径
- **异常处理覆盖**: 所有SERVICE.METHOD_EXCEPTIONS
- **权限验证覆盖**: 完整的认证和授权测试

### 测试原则
- **端到端验证**: 完整的请求-响应流程测试
- **数据隔离**: 每个测试使用独立的数据环境
- **真实场景**: 模拟实际使用场景和边界条件
- **自动化程度**: 完全自动化，无需人工干预

## 注意事项

当前阶段专注于：
1. 功能实现的完整性和正确性
2. 代码架构的规范性和可维护性
3. 为后续测试阶段做好准备

End-to-End测试将确保：
1. 所有API端点正常工作
2. 业务逻辑正确实现
3. 数据安全和权限控制有效
4. 系统性能满足要求