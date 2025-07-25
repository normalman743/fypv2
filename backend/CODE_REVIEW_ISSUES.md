# 代码审查问题清单

> 生成时间: 2025-07-25  
> 审查范围: 统一文件服务、临时文件服务、API端点

## 🚨 高优先级问题

### 1. API端点服务不一致问题
**文件**: `app/api/v1/files.py`  
**问题**: 临时文件的上传和下载使用了不同的服务类
- **上传** (行41-49): 使用 `UnifiedFileService`
- **下载** (行249-272): 使用 `TemporaryFileService`
- **删除** (行286-298): 使用 `TemporaryFileService`

**影响**: 
- 上传和下载可能使用不同的路径逻辑
- 物理文件去重机制不一致
- 可能导致文件找不到的错误

**建议**: 统一使用 `UnifiedFileService` 或确保两个服务的路径逻辑完全一致

### 2. 路径生成不一致问题
**涉及文件**: 
- `app/services/unified_file_service.py` (行198-199)
- `app/services/temporary_file_service.py` (行42)
- `app/services/local_file_storage.py` (行42-44)

**问题**: 
- `UnifiedFileService` 生成路径: `temporary/{hash}_{filename}`
- `TemporaryFileService` 通过 `LocalFileStorage` 生成: `course_0/folder_0/{uuid}.ext`

**影响**: 
- 文件存储位置不一致
- 下载时可能找不到文件
- 物理文件去重失效

### 3. 物理文件引用计数管理不统一
**问题**: 
- `UnifiedFileService` 有完整的引用计数逻辑 (行153-161)
- `TemporaryFileService` 手动管理引用计数 (行56-75)
- 两套逻辑可能不同步

**影响**: 
- 可能导致物理文件被错误删除或无法删除
- 存储空间浪费

### 4. 临时文件服务集成不完整
**问题**: 
- API端点部分迁移到 `UnifiedFileService`
- 但下载、删除等操作仍使用旧服务
- 缺少统一的临时文件管理接口

## 🔶 中优先级问题

### 5. 重复导入
**文件**: `app/services/unified_file_service.py`  
**问题**: `hashlib` 被导入两次 (行1和18)

### 6. 错误处理不一致
**问题**: 
- 不同服务的错误处理方式不同
- 有些用 `HTTPException`，有些用日志记录
- 错误信息格式不统一

### 7. 文件类型推断逻辑简单
**文件**: `app/services/unified_file_service.py` (行244-253)  
**问题**: 
- 仅基于 MIME type 和文件扩展名
- 缺少对恶意文件的检测
- 可能被绕过

## 🔷 低优先级问题

### 8. 代码注释和文档
**问题**: 
- 部分方法缺少详细注释
- 参数说明不够清晰
- 缺少使用示例

### 9. 日志记录不统一
**问题**: 
- 有些用 `print`，有些用 `logger`
- 日志级别不一致
- 缺少关键操作的审计日志

## 📋 修复建议

### 立即修复 (高优先级)
1. **统一临时文件服务**: 将所有临时文件操作迁移到 `UnifiedFileService`
2. **修复路径生成**: 确保所有服务使用相同的路径生成逻辑
3. **统一引用计数管理**: 移除重复的引用计数逻辑

### 后续优化 (中低优先级)
1. 清理重复导入
2. 统一错误处理机制
3. 改进文件类型检测
4. 完善日志记录

## 🧪 测试建议

### 回归测试重点
1. **临时文件上传下载流程**: 确保文件能正确上传和下载
2. **物理文件去重**: 验证相同文件不会重复存储
3. **引用计数正确性**: 确保文件删除时引用计数正确减少
4. **路径访问**: 验证生成的路径能正确访问到文件

### 测试用例
```bash
# 上传相同临时文件测试去重
curl -X POST -F "file=@test.png" "localhost:8000/files/temporary"
curl -X POST -F "file=@test.png" "localhost:8000/files/temporary"

# 验证下载
curl "localhost:8000/files/temporary/{token}/download"
```

## 🎯 预期收益

修复这些问题后：
- ✅ 文件上传下载流程更稳定
- ✅ 存储空间利用更高效  
- ✅ 代码维护性更好
- ✅ 错误处理更统一
- ✅ 系统安全性提升