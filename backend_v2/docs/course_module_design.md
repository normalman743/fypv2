# Course 模块设计文档 📚

## 概述

Course模块负责管理学期(Semester)和课程(Course)，是校园LLM系统的核心业务模块之一。该模块提供完整的学期/课程生命周期管理功能。

## 业务需求分析

### 学期管理 (Semester Management)
- **学期CRUD**: 创建、查询、更新、删除学期
- **时间管理**: 学期开始/结束时间验证
- **状态管理**: 活跃/非活跃状态控制
- **权限控制**: 管理员专用操作

### 课程管理 (Course Management)  
- **课程CRUD**: 创建、查询、更新、删除课程
- **关联管理**: 课程与学期、用户的关联
- **统计信息**: 文件数量、聊天数量统计
- **权限控制**: 用户只能操作自己的课程

## 数据模型设计

### Semester 模型
```python
class Semester(Base):
    __tablename__ = "semesters"
    
    # 基础字段
    id: int (PK)
    name: str (100, 索引)           # 学期名称
    code: str (20, 唯一索引)        # 学期代码 
    start_date: datetime            # 开始时间
    end_date: datetime              # 结束时间
    is_active: bool (默认True, 索引) # 激活状态
    
    # 时间戳
    created_at: datetime
    updated_at: datetime
    
    # 关系
    courses: List[Course]           # 一对多关系
    
    # 约束
    - end_date > start_date
    - code 唯一
    - 复合索引: (is_active, start_date, end_date)
```

### Course 模型
```python
class Course(Base):
    __tablename__ = "courses"
    
    # 基础字段
    id: int (PK)
    name: str (100)                 # 课程名称
    code: str (20)                  # 课程代码
    description: text               # 课程描述
    
    # 外键关系
    semester_id: int (FK -> semesters.id)
    user_id: int (FK -> users.id)
    
    # 时间戳
    created_at: datetime
    
    # 关系
    semester: Semester              # 多对一关系
    user: User                      # 多对一关系
    folders: List[Folder]           # 一对多关系(未来)
    files: List[File]               # 一对多关系(未来)
    chats: List[Chat]               # 一对多关系(未来)
    
    # 约束
    - (user_id, semester_id, code) 唯一
```

## API 接口设计

### 学期管理接口

#### 1. GET /api/v1/semesters - 获取学期列表
- **权限**: 已认证用户
- **响应**: 活跃学期列表
- **状态码**: 200

#### 2. POST /api/v1/semesters - 创建学期
- **权限**: 管理员
- **请求**: name, code, start_date, end_date
- **响应**: 创建的学期基本信息
- **状态码**: 201, 400(参数错误), 409(代码冲突), 403(权限不足)

#### 3. PUT /api/v1/semesters/{id} - 更新学期
- **权限**: 管理员  
- **请求**: name?, code?, start_date?, end_date?, is_active?
- **响应**: 更新的学期基本信息
- **状态码**: 200, 400(参数错误), 404(不存在), 409(代码冲突), 403(权限不足)

#### 4. GET /api/v1/semesters/{id} - 获取学期详情
- **权限**: 已认证用户
- **响应**: 完整学期信息
- **状态码**: 200, 404(不存在)

#### 5. DELETE /api/v1/semesters/{id} - 删除学期
- **权限**: 管理员
- **逻辑**: 软删除(设置is_active=false)
- **限制**: 有关联课程时不能删除
- **状态码**: 200, 404(不存在), 409(有关联数据), 403(权限不足)

#### 6. GET /api/v1/semesters/{id}/courses - 获取学期课程
- **权限**: 已认证用户
- **响应**: 学期下所有课程(含统计信息)
- **状态码**: 200, 404(学期不存在)

### 课程管理接口

#### 1. GET /api/v1/courses - 获取课程列表
- **权限**: 已认证用户(只能看自己的课程)
- **查询参数**: semester_id?(按学期过滤)
- **响应**: 课程列表(含学期信息和统计)
- **状态码**: 200

#### 2. POST /api/v1/courses - 创建课程
- **权限**: 已认证用户
- **请求**: name, code, description?, semester_id
- **验证**: 学期存在且活跃, 同学期内课程代码唯一
- **响应**: 创建的课程基本信息
- **状态码**: 201, 400(参数错误/学期不存在), 409(代码冲突)

#### 3. PUT /api/v1/courses/{id} - 更新课程
- **权限**: 课程所有者
- **请求**: name?, code?, description?
- **验证**: 课程代码唯一性
- **响应**: 更新的课程基本信息  
- **状态码**: 200, 400(参数错误), 404(不存在), 403(无权限), 409(代码冲突)

#### 4. GET /api/v1/courses/{id} - 获取课程详情
- **权限**: 课程所有者
- **响应**: 完整课程信息(含学期信息和统计)
- **状态码**: 200, 404(不存在), 403(无权限)

#### 5. DELETE /api/v1/courses/{id} - 删除课程
- **权限**: 课程所有者
- **逻辑**: 物理删除
- **响应**: 删除确认
- **状态码**: 200, 404(不存在), 403(无权限)

## Service 层设计

### SemesterService
```python
class SemesterService:
    METHOD_EXCEPTIONS = {
        'get_semesters': set(),
        'get_semester': {NotFoundError},
        'create_semester': {BadRequestError, ConflictError},
        'update_semester': {NotFoundError, BadRequestError, ConflictError},
        'delete_semester': {NotFoundError, ConflictError},
        'get_semester_courses': {NotFoundError}
    }
    
    def get_semesters(self) -> List[Semester]
    def get_semester(self, semester_id: int) -> Semester
    def create_semester(self, data: CreateSemesterRequest, admin_id: int) -> Dict
    def update_semester(self, id: int, data: UpdateSemesterRequest, admin_id: int) -> Dict
    def delete_semester(self, semester_id: int, admin_id: int) -> Dict
    def get_semester_courses(self, semester_id: int) -> Dict
```

### CourseService
```python
class CourseService:
    METHOD_EXCEPTIONS = {
        'get_courses': set(),
        'get_course': {NotFoundError, ForbiddenError},
        'create_course': {BadRequestError, ConflictError},
        'update_course': {NotFoundError, ForbiddenError, BadRequestError, ConflictError},
        'delete_course': {NotFoundError, ForbiddenError}
    }
    
    def get_courses(self, user_id: int, semester_id: Optional[int] = None) -> Dict
    def get_course(self, course_id: int, user_id: int) -> Dict
    def create_course(self, data: CreateCourseRequest, user_id: int) -> Dict
    def update_course(self, id: int, data: UpdateCourseRequest, user_id: int) -> Dict
    def delete_course(self, course_id: int, user_id: int) -> Dict
```

## Schema 设计

### 请求模型
```python
# 学期
class CreateSemesterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20) 
    start_date: datetime
    end_date: datetime

class UpdateSemesterRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None

# 课程  
class CreateCourseRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = None
    semester_id: int = Field(..., gt=0)

class UpdateCourseRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=20)  
    description: Optional[str] = None
```

### 响应模型
```python
# 数据模型
class SemesterData(BaseModel):
    id: int
    name: str
    code: str
    start_date: datetime
    end_date: datetime
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class CourseData(BaseModel):  
    id: int
    name: str
    code: str
    description: Optional[str]
    semester_id: int
    user_id: int
    created_at: datetime
    semester: Optional[SemesterBasicData] = None
    stats: Optional[CourseStatsData] = None

# 响应模型
class SemesterListResponse(BaseResponse[Dict]):
    # data.semesters: List[SemesterData]

class CreateSemesterResponse(BaseResponse[Dict]):
    # data.semester: CreateResultData

class CourseListResponse(BaseResponse[Dict]):
    # data.courses: List[CourseData]
```

## 依赖注入设计

### 权限依赖
```python
# 学期管理需要管理员权限
AdminDep = Annotated[UserProtocol, Depends(require_admin)]

# 课程管理需要普通用户权限  
UserDep = Annotated[UserProtocol, Depends(get_current_user)]
```

## 文件结构
```
src/course/
├── __init__.py
├── models.py          # Semester, Course 模型
├── schemas.py         # 请求/响应模型
├── service.py         # SemesterService, CourseService
├── router.py          # API 路由
├── dependencies.py    # 模块特定依赖(如果需要)
└── exceptions.py      # 模块特定异常(如果需要)
```

## 关键设计决策

### 1. 学期软删除 vs 物理删除
- **决策**: 学期使用软删除(is_active=false)
- **原因**: 保持历史数据完整性，避免关联数据丢失

### 2. 课程权限控制
- **决策**: 用户只能操作自己创建的课程
- **实现**: Service层检查user_id匹配

### 3. 统计信息设计
- **决策**: 在API响应中包含课程统计(文件数、聊天数)
- **实现**: Service层动态计算(当前返回默认值，等文件/聊天模块完成后实现)

### 4. 数据库索引策略
- **复合索引**: (user_id, semester_id, code) 确保课程代码唯一性
- **单字段索引**: name, code, is_active 支持常用查询

## 测试策略

### 单元测试
- Service层业务逻辑测试
- 模型验证测试
- 异常处理测试

### 集成测试  
- API端点完整流程测试
- 权限控制测试
- 数据一致性测试

### 边界测试
- 日期范围验证
- 字符串长度限制
- 外键约束测试

这个设计遵循FastAPI最佳实践，与现有的Auth/Admin模块保持一致的架构模式。