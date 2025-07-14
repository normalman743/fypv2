# 统一文件系统迁移指南

## 概述

本指南详细说明如何将现有的 `files` 和 `global_files` 双表架构迁移到统一的 `files` 表架构，并实现文件共享功能。

## 迁移内容摘要

### 已完成的修改

✅ **1. 数据库迁移脚本**
- 📁 `scripts/migrate_to_unified_files.py` - 完整的数据库迁移脚本

✅ **2. 模型更新**
- 📁 `app/models/file.py` - 更新为统一文件模型 (增加 scope, visibility 等字段)
- 📁 `app/models/file_share.py` - 新增文件共享相关模型
- 📁 `app/models/document_chunk.py` - 增加 file_id 字段支持统一关联
- 📁 `app/models/__init__.py` - 更新模型导入

✅ **3. 服务层重构** 
- 📁 `app/services/unified_file_service.py` - 新的统一文件服务
- 📁 `app/services/rag_service.py` - 更新以支持统一文件模型

✅ **4. API 端点更新**
- 📁 `app/api/v1/admin.py` - 更新全局文件上传端点
- 📁 `app/api/v1/unified_files.py` - 新的统一文件管理API
- 📁 `app/main.py` - 注册新的API路由

## 实施步骤

### 第一阶段：数据库迁移 (关键步骤)

#### 1. 备份数据库
```bash
# 创建数据库备份
mysqldump -u username -p database_name > backup_$(date +%Y%m%d_%H%M%S).sql
```

#### 2. 运行迁移脚本
```bash
cd /Users/mannormal/Downloads/fyp/backend
python scripts/migrate_to_unified_files.py
```

**迁移脚本将执行：**
- ✅ 备份原始表 (`files_backup`, `global_files_backup`)
- ✅ 为 `files` 表添加新字段 (scope, visibility, tags, etc.)
- ✅ 迁移 `global_files` 数据到 `files` 表
- ✅ 创建缺失的 `physical_files` 记录
- ✅ 更新 `document_chunks` 表添加 `file_id` 字段
- ✅ 创建文件共享相关表
- ✅ 添加性能优化索引

#### 3. 验证迁移结果
```bash
# 检查迁移统计
mysql -u username -p database_name -e "
SELECT 
    (SELECT COUNT(*) FROM files) as total_files,
    (SELECT COUNT(*) FROM files WHERE scope='global') as global_files,
    (SELECT COUNT(*) FROM files WHERE scope='course') as course_files,
    (SELECT COUNT(*) FROM document_chunks WHERE file_id IS NOT NULL) as updated_chunks;
"
```

### 第二阶段：代码部署

#### 1. 更新依赖
```bash
pip install -r requirements.txt
```

#### 2. 重启应用
```bash
# 如果使用systemd
sudo systemctl restart your-app-service

# 如果使用docker
docker-compose restart

# 如果直接运行
pkill -f "python.*main.py"
python app/main.py
```

#### 3. 测试新API
```bash
# 测试统一文件上传
curl -X POST "http://localhost:8000/api/v1/files/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.pdf" \
  -F "scope=global" \
  -F "visibility=public"

# 测试文件列表
curl -X GET "http://localhost:8000/api/v1/files?scope=global" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 第三阶段：前端适配 (需要前端开发)

#### API 变更摘要
```diff
# 原来的全局文件上传
- POST /api/v1/admin/global-files/upload

# 新的统一文件上传  
+ POST /api/v1/files/upload
  - scope: 'course' | 'global' | 'personal'
  - visibility: 'private' | 'course' | 'public' | 'shared'

# 新增文件共享
+ POST /api/v1/files/{file_id}/share
+ GET /api/v1/files/{file_id}/access-logs
```

#### 前端需要适配的地方
1. **文件上传组件** - 支持 scope 和 visibility 选择
2. **文件列表页面** - 支持按 scope 过滤
3. **文件共享功能** - 新的共享UI和逻辑
4. **权限控制** - 根据 scope 和 visibility 显示不同操作

## 新功能介绍

### 1. 统一文件作用域 (Scope)
- `course` - 课程文件 (默认)
- `global` - 全局文件 (仅管理员)
- `personal` - 个人文件

### 2. 灵活可见性控制 (Visibility)
- `private` - 私有文件 (默认)
- `course` - 课程可见
- `public` - 公开可见
- `shared` - 通过共享链接可见

### 3. 文件共享系统
```python
# 共享给用户
service.share_file(file_id, 'user', user_id, 'read')

# 共享给课程
service.share_file(file_id, 'course', course_id, 'read')

# 共享给组
service.share_file(file_id, 'group', group_id, 'edit')
```

### 4. 权限级别
- `read` - 只读权限
- `comment` - 评论权限
- `edit` - 编辑权限  
- `manage` - 管理权限

### 5. 访问日志
- 完整的文件访问追踪
- 支持按用户、操作类型过滤
- 文件所有者可查看访问统计

## 兼容性保证

### 向后兼容
- ✅ 保留原有 `global_files` 表结构 (迁移期间)
- ✅ 保留原有 API 端点 (使用新服务实现)
- ✅ `document_chunks` 同时支持新旧字段

### 迁移期API兼容
```python
# 原有的 GlobalFileService 方法仍然可用
def upload_global_file(file, description, tags, user_id):
    # 内部调用新的 UnifiedFileService
    return unified_service.upload_file(
        file=file,
        user_id=user_id, 
        scope='global',
        description=description,
        tags=tags,
        visibility='public'
    )
```

## 性能优化

### 数据库索引
```sql
-- 新增的复合索引
CREATE INDEX idx_scope_visibility ON files(scope, visibility);
CREATE INDEX idx_owner_course ON files(user_id, course_id);
CREATE INDEX idx_file_hash ON files(file_hash);
CREATE INDEX idx_document_chunks_file_id ON document_chunks(file_id);
```

### 查询优化
- 使用 scope 和 visibility 进行高效过滤
- file_id 统一关联减少 JOIN 操作
- 文件去重通过 physical_files 表实现

## 监控和日志

### 关键指标
- 文件上传成功率
- RAG 处理成功率  
- 文件访问频率
- 共享使用情况

### 日志检查点
```bash
# 检查迁移是否成功
grep "迁移完成" /var/log/app.log

# 检查API错误
grep "ERROR" /var/log/app.log | grep "files"

# 检查RAG处理状态
grep "RAG" /var/log/app.log
```

## 回滚计划

如果迁移出现问题，可以按以下步骤回滚：

### 1. 恢复数据库
```sql
-- 恢复原始表
DROP TABLE files;
RENAME TABLE files_backup TO files;

-- 恢复 document_chunks
UPDATE document_chunks SET file_id = NULL;
```

### 2. 恢复代码
```bash
git checkout previous-commit-hash
```

### 3. 重启服务
```bash
sudo systemctl restart your-app-service
```

## 常见问题排查

### Q: 文件上传失败 "physical_file_id is required"
**A:** 检查 PhysicalFile 记录是否正确创建，运行迁移脚本的 `create_missing_physical_files` 部分

### Q: RAG 检索不到全局文件
**A:** 确认 `document_chunks.file_id` 字段已正确更新，检查 RAG 服务是否使用新的查询逻辑

### Q: 权限检查失败
**A:** 验证 `FileShare` 表数据和权限检查逻辑，确保共享记录正确创建

### Q: 性能下降
**A:** 检查新增的索引是否生效，使用 `EXPLAIN` 分析查询计划

## 总结

这次迁移实现了：

1. **简化架构** - 从双表结构简化为单表 + 共享表
2. **增强功能** - 添加了灵活的共享和权限控制
3. **提升扩展性** - 为未来功能预留了扩展空间
4. **保持兼容** - 确保现有功能不受影响

迁移后的系统更加灵活、可扩展，为未来的协作功能奠定了solid的基础。

---
**迁移负责人**: Claude AI Assistant  
**文档版本**: v1.0  
**最后更新**: 2025-07-14