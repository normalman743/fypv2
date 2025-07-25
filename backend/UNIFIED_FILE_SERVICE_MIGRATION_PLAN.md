# 统一文件服务迁移实施计划

> 分支: fix/unified-file-service  
> 方案: 完全统一 - 废弃 TemporaryFileService，全面使用 UnifiedFileService

## 🎯 目标

- ✅ 统一所有文件操作到 UnifiedFileService
- ✅ 消除路径生成不一致问题  
- ✅ 统一引用计数管理
- ✅ 提升安全性和可维护性

## 📋 实施步骤

### 阶段1: 安全修复 (优先级: 🚨 Critical)

#### 1.1 修复路径安全漏洞
**文件**: `app/api/v1/files.py:259`
```python
# 当前危险代码:
with open(physical_file.storage_path, 'rb') as f:

# 需要改为安全的路径处理
```

#### 1.2 添加UnifiedFileService临时文件下载方法
**目标**: 在 `UnifiedFileService` 中添加 `download_temporary_file()` 方法

#### 1.3 添加UnifiedFileService临时文件删除方法  
**目标**: 在 `UnifiedFileService` 中添加 `delete_temporary_file()` 方法

### 阶段2: API端点统一 (优先级: 🚨 High)

#### 2.1 修改临时文件下载端点
**文件**: `app/api/v1/files.py:239-272`
- 移除 `TemporaryFileService` 导入
- 使用 `UnifiedFileService.download_temporary_file()`

#### 2.2 修改临时文件删除端点
**文件**: `app/api/v1/files.py:275-298`  
- 移除 `TemporaryFileService` 导入
- 使用 `UnifiedFileService.delete_temporary_file()`

### 阶段3: 数据一致性修复 (优先级: 🚨 High)

#### 3.1 检查现有临时文件存储情况
```bash
# 检查是否存在使用旧路径格式的临时文件
find storage/uploads -name "*" -type f | head -10
```

#### 3.2 数据迁移脚本 (如需要)
如果发现不一致数据，创建迁移脚本

### 阶段4: 代码清理 (优先级: 🔶 Medium)

#### 4.1 移除废弃的 TemporaryFileService
**文件**: `app/services/temporary_file_service.py`
- 确认无其他地方使用后删除

#### 4.2 清理重复导入
**文件**: `app/services/unified_file_service.py:1,18`
- 移除重复的 `import hashlib`

#### 4.3 更新导入引用
- 搜索所有使用 `TemporaryFileService` 的地方
- 确保都已迁移到 `UnifiedFileService`

### 阶段5: 安全增强 (优先级: 🔶 Medium)

#### 5.1 路径验证函数
添加安全的路径处理工具函数

#### 5.2 统一错误处理
标准化所有文件操作的错误处理机制

#### 5.3 安全审计日志
完善文件访问日志记录

### 阶段6: 测试验证 (优先级: 🔷 Low)

#### 6.1 功能测试
- 临时文件上传下载流程
- 物理文件去重验证  
- 引用计数正确性
- 文件删除清理

#### 6.2 安全测试
- 路径遍历攻击测试
- 文件类型绕过测试
- 权限验证测试

## 🔧 技术实现细节

### UnifiedFileService 需要添加的方法

```python
def download_temporary_file(self, token: str) -> Tuple[TemporaryFile, bytes]:
    """通过token下载临时文件"""
    
def delete_temporary_file(self, temp_file: TemporaryFile) -> bool:
    """删除临时文件"""
    
def get_temporary_file_by_token(self, token: str) -> Optional[TemporaryFile]:
    """通过token获取临时文件"""
    
def get_temporary_file_by_id(self, file_id: int, user_id: int) -> Optional[TemporaryFile]:
    """通过ID获取用户的临时文件"""
```

### 路径安全处理

```python
def _validate_and_resolve_path(self, storage_path: str) -> str:
    """验证并解析安全的文件路径"""
    # 防止目录遍历攻击
    # 确保路径在允许的存储目录内
```

## ⚠️ 风险评估

### 高风险
- **数据丢失风险**: 路径迁移可能导致文件无法访问
- **服务中断**: API变更可能影响现有功能

### 中风险  
- **引用计数错误**: 可能导致文件无法正确删除
- **权限问题**: 路径变更可能影响文件访问权限

### 低风险
- **性能影响**: 统一服务可能略微影响性能
- **兼容性**: 需要确保向后兼容

## 🧪 测试计划

### 回归测试重点
1. **临时文件完整流程**: 上传 → 下载 → 删除
2. **多图片聊天功能**: 确保图片处理不受影响  
3. **物理文件去重**: 验证相同文件只存储一份
4. **引用计数管理**: 确保文件删除时正确更新计数

### 测试用例
```bash
# 1. 基础功能测试
curl -X POST -F "file=@test.png" "localhost:8000/files/temporary"
curl "localhost:8000/files/temporary/{token}/download"  
curl -X DELETE "localhost:8000/files/temporary/{id}"

# 2. 去重验证
curl -X POST -F "file=@same_file.pdf" "localhost:8000/files/temporary"
curl -X POST -F "file=@same_file.pdf" "localhost:8000/files/temporary"
# 应该使用相同物理文件

# 3. 安全测试
curl -X POST -F "file=@../../etc/passwd" "localhost:8000/files/temporary"
# 应该被拒绝
```

## 📈 成功指标

- ✅ 所有临时文件API使用统一服务
- ✅ 消除路径生成不一致
- ✅ 通过所有现有测试用例  
- ✅ 物理文件去重率 > 95%
- ✅ 零安全漏洞
- ✅ API响应时间无明显下降

## 🚀 部署计划

1. **开发环境验证**: 完成所有功能测试
2. **代码审查**: 同行审查所有变更
3. **测试环境部署**: 完整回归测试
4. **生产环境部署**: 分阶段灰度部署
5. **监控验证**: 观察关键指标24小时

---

*这个计划将分阶段执行，每个阶段完成后进行验证，确保系统稳定性。*