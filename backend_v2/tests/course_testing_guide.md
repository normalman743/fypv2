# Course模块测试指南

## 概述

Course模块包含comprehensive pytest test suite，基于FastAPI最佳实践设计，确保学期和课程管理功能的完整测试覆盖。

## 测试文件结构

```
backend_v2/tests/
├── test_course_api.py     # API集成测试 - 完整HTTP请求流程
├── test_course_unit.py    # Service层单元测试 - 业务逻辑验证  
├── conftest.py           # 全局配置和Course模块fixtures
└── docs/
    └── course_testing_guide.md  # 本文档
```

## 测试覆盖范围

### 1. API集成测试 (test_course_api.py)

#### 学期管理API (需要管理员权限)
- **GET /api/v1/semesters** - 获取学期列表
  - ✅ 空列表场景
  - ✅ 有数据场景（按时间倒序）
  - ✅ 只返回活跃学期
  - ✅ 未认证访问错误

- **POST /api/v1/semesters** - 创建学期
  - ✅ 成功创建（201状态码）
  - ✅ 重复代码错误 (409)
  - ✅ 无效日期范围 (422)
  - ✅ 缺少必需字段 (422)
  - ✅ 非管理员权限 (403)
  - ✅ 未认证访问 (403)

- **GET /api/v1/semesters/{id}** - 获取学期详情
  - ✅ 成功获取
  - ✅ 学期不存在 (404)
  - ✅ 停用学期不可见 (404)

- **PUT /api/v1/semesters/{id}** - 更新学期
  - ✅ 成功更新
  - ✅ 重复代码错误 (409)
  - ✅ 违反日期逻辑 (400)
  - ✅ 学期不存在 (404)
  - ✅ 权限检查 (403)

- **DELETE /api/v1/semesters/{id}** - 删除学期
  - ✅ 成功软删除
  - ✅ 有关联课程时禁止删除 (409)
  - ✅ 学期不存在 (404)
  - ✅ 权限检查 (403)

- **GET /api/v1/semesters/{id}/courses** - 获取学期课程
  - ✅ 空课程列表
  - ✅ 有数据场景（包含学期和统计信息）
  - ✅ 按创建时间倒序排列
  - ✅ 学期不存在 (404)

#### 课程管理API (需要用户权限)
- **GET /api/v1/courses** - 获取课程列表
  - ✅ 空列表场景
  - ✅ 用户隔离（只返回当前用户的课程）
  - ✅ 按学期过滤
  - ✅ 无效学期ID验证 (422)
  - ✅ 未认证访问 (403)

- **POST /api/v1/courses** - 创建课程
  - ✅ 成功创建 (201)
  - ✅ 同用户同学期重复代码 (409)
  - ✅ 不同学期允许相同代码
  - ✅ 停用学期禁止创建 (400)
  - ✅ 不存在学期 (400)
  - ✅ 缺少必需字段 (422)

- **GET /api/v1/courses/{id}** - 获取课程详情
  - ✅ 成功获取（包含学期和统计信息）
  - ✅ 课程不存在 (404)
  - ✅ 访问其他用户课程 (403)

- **PUT /api/v1/courses/{id}** - 更新课程
  - ✅ 成功更新
  - ✅ 重复代码错误 (409)
  - ✅ 课程不存在 (404)
  - ✅ 权限检查 (403)

- **DELETE /api/v1/courses/{id}** - 删除课程
  - ✅ 成功物理删除
  - ✅ 课程不存在 (404)
  - ✅ 权限检查 (403)

#### 权限安全测试
- ✅ 学期管理端点需要管理员权限
- ✅ 所有端点需要认证
- ✅ 用户数据隔离验证

#### 数据验证测试
- ✅ 学期日期范围验证
- ✅ 课程字段验证
- ✅ Pydantic模型验证

### 2. Service层单元测试 (test_course_unit.py)

#### SemesterService测试 (6个方法)
- **get_semesters**
  - ✅ 空列表处理
  - ✅ 活跃学期过滤
  - ✅ 按开始时间倒序排列
  - ✅ 异常处理

- **get_semester**
  - ✅ 成功获取
  - ✅ 不存在处理 (NotFoundError)
  - ✅ 非活跃学期处理
  - ✅ 异常处理

- **create_semester**
  - ✅ 成功创建
  - ✅ 重复代码 (ConflictError)
  - ✅ 代码大小写不敏感
  - ✅ 字段标准化（去空格、转大写）
  - ✅ 数据库约束错误处理

- **update_semester**
  - ✅ 成功更新
  - ✅ 不存在处理 (NotFoundError)
  - ✅ 重复代码 (ConflictError)
  - ✅ 相同代码允许更新
  - ✅ 无效日期范围 (BadRequestError)
  - ✅ 部分字段更新

- **delete_semester**
  - ✅ 成功软删除
  - ✅ 不存在处理 (NotFoundError)
  - ✅ 有关联课程 (ConflictError)
  - ✅ 多课程数量显示

- **get_semester_courses**  
  - ✅ 空课程列表
  - ✅ 有数据按时间排序
  - ✅ joinedload关联加载
  - ✅ 学期不存在 (NotFoundError)
  - ✅ 非活跃学期处理

#### CourseService测试 (5个方法)
- **get_courses**
  - ✅ 空列表处理
  - ✅ 用户数据隔离
  - ✅ 按学期过滤
  - ✅ 不存在学期过滤
  - ✅ 异常处理

- **get_course**
  - ✅ 成功获取（含关联数据）
  - ✅ 不存在处理 (NotFoundError)
  - ✅ 权限检查 (ForbiddenError)

- **create_course**
  - ✅ 成功创建
  - ✅ 学期不存在 (BadRequestError)
  - ✅ 停用学期处理
  - ✅ 同用户同学期重复代码 (ConflictError)
  - ✅ 跨用户相同代码允许
  - ✅ 跨学期相同代码允许
  - ✅ 字段标准化

- **update_course**
  - ✅ 成功更新
  - ✅ 不存在处理 (NotFoundError)
  - ✅ 权限检查 (ForbiddenError)
  - ✅ 重复代码 (ConflictError)
  - ✅ 相同代码允许更新
  - ✅ 部分字段更新

- **delete_course**
  - ✅ 成功物理删除
  - ✅ 不存在处理 (NotFoundError)
  - ✅ 权限检查 (ForbiddenError)

#### 异常覆盖测试
- ✅ METHOD_EXCEPTIONS声明完整性验证
- ✅ 各方法异常类型声明准确性
- ✅ SemesterService: 6个方法异常覆盖
- ✅ CourseService: 5个方法异常覆盖

#### Service集成测试
- ✅ 学期-课程完整生命周期
- ✅ 跨用户数据隔离验证
- ✅ 学期停用对课程影响测试

### 3. 测试基础设施 (conftest.py)

#### 新增Fixtures
- ✅ `semester_service` - SemesterService实例
- ✅ `course_service` - CourseService实例
- ✅ `active_semester` - 活跃测试学期
- ✅ `inactive_semester` - 停用测试学期
- ✅ `sample_course` - 标准测试课程
- ✅ `admin_course` - 管理员测试课程

#### 测试隔离策略
- ✅ 每个测试使用独立数据库事务
- ✅ 自动事务回滚清理
- ✅ Fixture作用域控制（function级别）

## 运行测试

### 环境准备

```bash
# 进入backend_v2目录
cd backend_v2

# 激活虚拟环境
source v2env/bin/activate

# 确保依赖已安装
pip install -r requirements.txt

# 确保数据库已启动且配置正确
# 检查.env.test文件中的DATABASE_URL配置
```

### 运行方式

#### 1. 运行所有Course模块测试
```bash
# API集成测试 + Service单元测试
python -m pytest tests/test_course_api.py tests/test_course_unit.py -v
```

#### 2. 分别运行不同类型测试
```bash
# 只运行API集成测试
python -m pytest tests/test_course_api.py -v

# 只运行Service单元测试
python -m pytest tests/test_course_unit.py -v
```

#### 3. 按测试类运行
```bash
# 只测试学期管理API
python -m pytest tests/test_course_api.py::TestSemesterManagementAPI -v

# 只测试课程管理API
python -m pytest tests/test_course_api.py::TestCourseManagementAPI -v

# 只测试SemesterService
python -m pytest tests/test_course_unit.py::TestSemesterService -v

# 只测试CourseService
python -m pytest tests/test_course_unit.py::TestCourseService -v
```

#### 4. 运行特定测试方法
```bash
# 测试创建学期功能
python -m pytest tests/test_course_api.py::TestSemesterManagementAPI::test_create_semester_success -v

# 测试权限验证
python -m pytest tests/test_course_api.py::TestCoursePermissionSecurity -v
```

#### 5. 生成测试覆盖率报告
```bash
# 安装coverage工具
pip install coverage pytest-cov

# 运行测试并生成覆盖率报告
python -m pytest tests/test_course_api.py tests/test_course_unit.py --cov=src.course --cov-report=html --cov-report=term
```

### 测试输出示例

```bash
$ python -m pytest tests/test_course_api.py -v

===================== test session starts =====================
tests/test_course_api.py::TestSemesterManagementAPI::test_get_semesters_success_empty PASSED
tests/test_course_api.py::TestSemesterManagementAPI::test_create_semester_success PASSED
tests/test_course_api.py::TestSemesterManagementAPI::test_create_semester_duplicate_code PASSED
tests/test_course_api.py::TestCourseManagementAPI::test_get_courses_success_empty PASSED
tests/test_course_api.py::TestCourseManagementAPI::test_create_course_success PASSED
...
===================== 67 passed in 15.23s =====================
```

## 测试质量指标

### 覆盖范围
- **API端点覆盖**: 11/11 (100%)
- **HTTP状态码覆盖**: 200, 201, 400, 403, 404, 409, 422
- **业务逻辑覆盖**: 学期时间验证、课程唯一性、权限检查、数据关联
- **异常场景覆盖**: 所有SERVICE.METHOD_EXCEPTIONS声明的异常

### 测试原则
- **确定性**: 所有测试结果可重现，无时间依赖
- **隔离性**: 每个测试独立运行，无相互依赖
- **完整性**: 覆盖成功路径、错误路径、边界条件
- **可维护性**: 清晰的测试结构和命名，易于理解和修改

### 性能指标
- **运行时间**: API测试 ~20秒，Unit测试 ~10秒
- **数据库操作**: 使用事务回滚，无数据污染
- **内存使用**: Function级fixture，及时清理

## 最佳实践

### 1. 测试数据管理
- 使用fixtures创建测试数据，避免硬编码ID
- 每个测试使用独立的数据，避免测试间依赖
- 利用事务回滚自动清理数据

### 2. 断言策略
- 使用项目标准断言函数：`assert_success_response`, `assert_error_response`
- 验证完整的响应结构，不只是状态码
- 检查业务逻辑的正确性，如排序、过滤、权限

### 3. 异常测试
- 每个SERVICE.METHOD_EXCEPTIONS声明的异常都有对应测试
- 使用`pytest.raises(ExceptionType)`验证异常类型和错误码
- 测试异常消息的准确性和用户友好性

### 4. 权限测试
- 系统性测试所有需要特定权限的端点
- 验证跨用户数据隔离
- 测试未认证和权限不足的场景

## 常见问题

### Q: 测试运行很慢怎么办？
A: 
1. 检查数据库连接是否正常
2. 确保使用事务而不是真实提交
3. 考虑使用`-x`参数在第一个失败时停止

### Q: 某些测试偶尔失败？
A: 
1. 检查是否有时间依赖（如使用`datetime.utcnow()`）
2. 确保测试数据没有冲突
3. 验证fixtures的scope设置正确

### Q: 如何调试测试失败？
A:
1. 使用`-s`参数查看print输出
2. 使用`--pdb`参数在失败时进入调试器
3. 检查测试日志和数据库状态

### Q: 如何添加新的测试？
A:
1. 遵循现有的测试命名模式
2. 使用合适的fixtures和断言函数
3. 确保新测试的独立性和可重复性
4. 添加到对应的测试类中

## 维护指南

### 代码变更影响
- **添加新API端点**: 在`test_course_api.py`中添加对应测试
- **修改Service方法**: 更新`test_course_unit.py`中的相关测试
- **更改异常类型**: 同步更新METHOD_EXCEPTIONS和对应测试
- **修改数据模型**: 可能需要更新fixtures和断言

### 测试更新checklist
- [ ] 新功能是否有对应的成功路径测试？
- [ ] 是否覆盖了所有可能的错误场景？
- [ ] METHOD_EXCEPTIONS是否已更新？
- [ ] 是否添加了必要的fixtures？
- [ ] 测试是否保持独立性？
- [ ] 是否更新了相关文档？