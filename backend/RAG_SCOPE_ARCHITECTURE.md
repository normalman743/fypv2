# RAG作用域架构分析

## 当前RAG实现

### 1. 作用域分离策略

RAG服务按照文件的作用域创建不同的向量数据库集合：

```python
# 文件上传时的集合选择逻辑
file_scope = getattr(file, "scope", "course")
if file_scope == "global":
    collection_name = "global"
elif hasattr(file, "course_id") and getattr(file, "course_id", None):
    collection_name = f"course_{file.course_id}"
else:
    collection_name = "personal"
```

### 2. 实际存储结构

```
data/chroma/
├── global/              # 全局文件的向量库
├── course_1/           # 课程1的向量库  
├── course_22/          # 课程22的向量库
├── personal/           # 个人文件的向量库 (新增)
└── ...
```

### 3. 检索策略

#### 课程聊天检索
```python
def search_documents(self, query: str, chat_type: str = "general", course_id: int = None):
    if chat_type == "course" and course_id:
        # 1. 先搜索课程特定的向量库
        course_collection = f"course_{course_id}"
        course_results = course_vectorstore.similarity_search_with_score(query)
        
        # 2. 再搜索全局向量库
        global_results = global_vectorstore.similarity_search_with_score(query)
        
        # 3. 合并结果
        return combine_results(course_results, global_results)
    else:
        # 纯全局搜索
        return global_vectorstore.similarity_search_with_score(query)
```

## 优势分析

### ✅ 当前设计的优点

1. **数据隔离**: 每个课程的数据完全隔离，避免权限泄露
2. **检索精准**: 课程内检索更准确，减少无关干扰
3. **性能优化**: 小范围检索速度更快
4. **扩展性好**: 容易添加新的作用域

### ⚠️ 潜在问题

1. **跨课程共享**: 如果文件需要跨课程共享，会存在重复
2. **全局检索不够**: 用户可能希望在所有有权限的文件中检索
3. **权限复杂性**: 实际权限检查可能比作用域更复杂

## 针对聊天文件集成的改进

### 1. 增强的检索策略

```python
class EnhancedRAGService:
    def search_with_file_context(self, query: str, user_id: int, 
                                specified_files: List[int] = None,
                                course_id: int = None) -> str:
        """
        智能检索策略:
        1. 如果指定了文件，直接读取内容
        2. 基于用户权限，在可访问的作用域中检索相关内容
        3. 排除已指定的文件，避免重复
        """
        
        context_parts = []
        
        # 1. 直接指定的文件内容 (最高优先级)
        if specified_files:
            direct_content = self._read_specified_files(specified_files, user_id)
            context_parts.append("=== 指定文件内容 ===")
            context_parts.append(direct_content)
        
        # 2. RAG检索相关内容 (排除已指定的文件)
        accessible_scopes = self._get_accessible_scopes(user_id, course_id)
        rag_content = self._search_in_scopes(
            query=query, 
            scopes=accessible_scopes,
            exclude_files=specified_files or []
        )
        
        if rag_content:
            context_parts.append("=== 相关文件内容 ===")
            context_parts.append(rag_content)
        
        return "\n\n".join(context_parts)
    
    def _get_accessible_scopes(self, user_id: int, course_id: int = None) -> List[str]:
        """根据用户权限获取可访问的RAG作用域"""
        
        scopes = ["global"]  # 全局文件都可以访问
        
        # 添加用户的个人作用域
        scopes.append("personal")  # 如果实现了个人文件
        
        # 添加用户有权限的课程作用域
        user_courses = self._get_user_accessible_courses(user_id)
        for course in user_courses:
            scopes.append(f"course_{course.id}")
        
        # 如果指定了特定课程，优先搜索该课程
        if course_id and f"course_{course_id}" in scopes:
            scopes.remove(f"course_{course_id}")
            scopes.insert(0, f"course_{course_id}")  # 放在最前面
        
        return scopes
    
    def _search_in_scopes(self, query: str, scopes: List[str], 
                         exclude_files: List[int] = None) -> str:
        """在多个作用域中检索"""
        
        all_results = []
        
        for scope in scopes:
            vectorstore = self._get_vectorstore(scope)
            if vectorstore:
                results = vectorstore.similarity_search_with_score(query, k=3)
                
                # 过滤掉已指定的文件
                filtered_results = self._filter_exclude_files(results, exclude_files)
                all_results.extend(filtered_results)
        
        # 按相似度排序，取top-k
        all_results.sort(key=lambda x: x[1], reverse=True)
        return self._format_search_results(all_results[:5])
```

### 2. 权限感知的RAG

```python
def _filter_by_permissions(self, search_results: List, user_id: int) -> List:
    """基于权限过滤搜索结果"""
    
    permission_service = FilePermissionService(self.db_session)
    filtered_results = []
    
    for doc, score in search_results:
        # 从文档metadata中获取文件ID
        file_id = doc.metadata.get('file_id')
        if file_id and permission_service.can_access_file(file_id, user_id):
            filtered_results.append((doc, score))
    
    return filtered_results
```

## 建议的实现方向

### 方案1: 保持当前架构 + 权限过滤 (推荐)

- ✅ **保持作用域隔离**: 继续使用course_X/global/personal分离
- ✅ **增加权限过滤**: 在搜索结果上应用权限检查
- ✅ **智能多域检索**: 根据用户权限在多个作用域中检索
- ✅ **避免重复**: 排除已指定的文件

### 方案2: 统一向量库 + 权限标签

- 所有文件存在一个向量库
- 通过metadata标签进行权限过滤
- 可能存在权限泄露风险

## 实际使用场景

### 场景1: 课程内聊天
```python
# 用户在"数据结构"课程中聊天
query = "什么是二叉树？"
course_id = 1

# 检索顺序: course_1 -> global -> 用户其他有权限的课程
context = rag_service.search_with_file_context(
    query=query,
    user_id=current_user.id,
    course_id=course_id
)
```

### 场景2: 指定文件聊天
```python
# 用户指定特定文件进行对话
query = "总结这个文件的要点"
specified_files = [123, 456]

# 直接读取指定文件 + 检索相关内容 (排除指定的文件)
context = rag_service.search_with_file_context(
    query=query,
    user_id=current_user.id,
    specified_files=specified_files
)
```

### 场景3: 跨课程检索
```python
# 用户在全局聊天中提问
query = "比较不同算法的时间复杂度"

# 在用户所有有权限的课程中检索
context = rag_service.search_with_file_context(
    query=query,
    user_id=current_user.id
    # 不指定course_id，会在所有可访问的作用域中检索
)
```

## 总结

当前的RAG作用域架构设计很合理：

1. **✅ 数据隔离好**: 每个课程独立的向量库
2. **✅ 检索效率高**: 作用域内检索更精准
3. **✅ 扩展性强**: 容易添加新的作用域

需要增强的部分：

1. **权限感知检索**: 基于实际权限而不仅仅是作用域
2. **智能多域搜索**: 在用户有权限的所有作用域中检索
3. **文件去重**: 避免指定文件和RAG检索的重复

这个架构为聊天文件集成提供了很好的基础！