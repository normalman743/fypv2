# 简化版聊天文件API设计

## API设计思路

前端处理@语法和UI，后端只需要接收文件ID列表，然后构建长上下文。

## 核心API

### 1. 发送带文件的消息

```python
class MessageWithFilesRequest(BaseModel):
    content: str                    # 用户消息内容
    file_ids: List[int] = []       # 引用的文件ID列表
    folder_ids: List[int] = []     # 引用的文件夹ID列表
    use_long_context: bool = True  # 使用长上下文而不是RAG

@router.post("/chats/{chat_id}/messages", response_model=ResponseModel)
async def send_message_with_files(
    chat_id: int,
    request: MessageWithFilesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送包含文件引用的消息"""
    try:
        service = ChatFileService(db)
        
        # 权限检查 + 内容读取
        context_data = service.build_file_context(
            file_ids=request.file_ids,
            folder_ids=request.folder_ids,
            user_id=current_user.id
        )
        
        # 调用AI (长上下文)
        if request.use_long_context:
            ai_response = await service.call_ai_with_long_context(
                user_message=request.content,
                file_context=context_data['context']
            )
        else:
            # 降级到RAG
            ai_response = await service.call_ai_with_rag(
                user_message=request.content,
                file_ids=request.file_ids
            )
        
        # 保存消息
        message = service.save_message_with_files(
            chat_id=chat_id,
            user_id=current_user.id,
            content=request.content,
            ai_response=ai_response,
            file_ids=request.file_ids,
            folder_ids=request.folder_ids,
            context_size=len(context_data['context'])
        )
        
        return ResponseModel(success=True, data=message)
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## 简化服务实现

```python
class ChatFileService:
    def __init__(self, db: Session):
        self.db = db
        self.permission_service = FilePermissionService(db)
    
    def build_file_context(self, file_ids: List[int], folder_ids: List[int], user_id: int) -> dict:
        """构建文件上下文"""
        
        all_files = []
        context_parts = []
        
        # 处理直接指定的文件
        for file_id in file_ids:
            file_record = self._get_and_check_file(file_id, user_id)
            content = self._read_file_content(file_record)
            all_files.append(file_record)
            context_parts.append(f"=== {file_record.original_name} ===\n{content}\n")
        
        # 处理文件夹中的文件
        for folder_id in folder_ids:
            folder_files = self._get_folder_files(folder_id, user_id)
            for file_record in folder_files:
                content = self._read_file_content(file_record)
                all_files.append(file_record)
                context_parts.append(f"=== {file_record.original_name} ===\n{content}\n")
        
        full_context = "\n".join(context_parts)
        
        return {
            'context': full_context,
            'files': all_files,
            'total_size': len(full_context)
        }
    
    def _get_and_check_file(self, file_id: int, user_id: int) -> File:
        """获取文件并检查权限"""
        file_record = self.db.query(File).filter(File.id == file_id).first()
        if not file_record:
            raise ValueError(f"文件ID {file_id} 不存在")
        
        if not self.permission_service.can_access_file(file_id, user_id):
            raise PermissionError(f"无权限访问文件: {file_record.original_name}")
        
        return file_record
    
    def _get_folder_files(self, folder_id: int, user_id: int) -> List[File]:
        """获取文件夹中用户有权限的文件"""
        folder = self.db.query(Folder).filter(Folder.id == folder_id).first()
        if not folder:
            raise ValueError(f"文件夹ID {folder_id} 不存在")
        
        # TODO: 检查文件夹权限
        
        files = self.db.query(File).filter(File.folder_id == folder_id).all()
        accessible_files = []
        
        for file_record in files:
            if self.permission_service.can_access_file(file_record.id, user_id):
                accessible_files.append(file_record)
        
        return accessible_files
    
    def _read_file_content(self, file_record: File) -> str:
        """读取文件内容 - 简化版"""
        try:
            from app.services.local_file_storage import local_file_storage
            file_path = local_file_storage.base_dir / file_record.physical_file.storage_path
            
            # 简单处理：只支持文本文件，其他返回文件信息
            if file_record.file_type in ['txt', 'md']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return f"[{file_record.file_type}文件: {file_record.original_name}, 大小: {file_record.file_size}字节]"
                
        except Exception as e:
            return f"[文件读取失败: {str(e)}]"
    
    async def call_ai_with_long_context(self, user_message: str, file_context: str) -> dict:
        """调用AI with长上下文"""
        
        full_prompt = f"""以下是相关文件内容：

{file_context}

用户问题：{user_message}

请基于上述文件内容回答用户问题。"""
        
        # 这里调用你的AI服务
        # 示例：
        from app.services.ai_service import AIService
        ai_service = AIService()
        
        response = await ai_service.generate_response(
            prompt=full_prompt,
            model="gpt-4-turbo",
            max_tokens=4000
        )
        
        return {
            'content': response.content,
            'tokens_used': response.tokens_used,
            'cost': response.cost,
            'model': response.model
        }
    
    def save_message_with_files(self, **kwargs) -> dict:
        """保存消息和文件关联"""
        
        # 保存用户消息
        user_message = Message(
            chat_id=kwargs['chat_id'],
            content=kwargs['content'],
            role='user',
            user_id=kwargs['user_id']
        )
        self.db.add(user_message)
        self.db.flush()
        
        # 保存文件关联
        for file_id in kwargs['file_ids']:
            file_ref = MessageFileReference(
                message_id=user_message.id,
                file_id=file_id,
                reference_type='file'
            )
            self.db.add(file_ref)
        
        for folder_id in kwargs['folder_ids']:
            folder_ref = MessageFileReference(
                message_id=user_message.id,
                file_id=folder_id,
                reference_type='folder'
            )
            self.db.add(folder_ref)
        
        # 保存AI回复
        ai_message = Message(
            chat_id=kwargs['chat_id'],
            content=kwargs['ai_response']['content'],
            role='assistant',
            model_name=kwargs['ai_response']['model'],
            tokens_used=kwargs['ai_response']['tokens_used'],
            cost=kwargs['ai_response']['cost'],
            context_size=kwargs['context_size']
        )
        self.db.add(ai_message)
        self.db.commit()
        
        return {
            'user_message': user_message,
            'ai_message': ai_message
        }
```

## 数据表

```sql
-- 消息文件引用表 (简化)
CREATE TABLE message_file_references (
    id INT PRIMARY KEY AUTO_INCREMENT,
    message_id INT NOT NULL,
    file_id INT NOT NULL,               -- 可以是文件ID或文件夹ID
    reference_type ENUM('file', 'folder') NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    INDEX idx_message_refs (message_id),
    INDEX idx_file_refs (file_id, reference_type)
);

-- 扩展messages表
ALTER TABLE messages ADD COLUMN context_size INT NULL COMMENT '长上下文字符数';
```

## 前端调用示例

```javascript
// 发送带文件的消息
const response = await fetch('/api/v1/chats/123/messages', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        content: '请总结这些文件的要点',
        file_ids: [456, 789],        // 用户选择的文件
        folder_ids: [12],            // 用户选择的文件夹
        use_long_context: true
    })
});
```

## 优势

1. **API简单**: 只需传递ID列表
2. **前端灵活**: @语法完全由前端处理
3. **权限安全**: 后端统一权限检查
4. **扩展性好**: 可以轻松添加新的引用类型
5. **降级支持**: 可以选择长上下文或RAG

这样设计是不是更简洁实用？