# 聊天@文件功能设计

## 功能概述

在聊天API中支持@文件夹/文件，直接将文件内容作为长上下文传递给LLM，而不使用RAG检索。

## 核心特性

### 1. @文件语法
```
用户输入示例:
"请帮我总结一下 @文件/报告.pdf 的主要内容"
"对比 @文件夹/课件 中的第一章和第二章有什么区别"
"基于 @文件/数据.csv 生成一个分析报告"
```

### 2. 权限集成
利用可扩展权限架构，确保用户只能@自己有权限访问的文件。

## 技术架构

### 1. 消息解析器

```python
import re
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class MentionedResource:
    type: str  # 'file' or 'folder'
    id: int
    name: str
    content: str
    size: int

class MessageParser:
    """消息@资源解析器"""
    
    FILE_MENTION_PATTERN = r'@文件/([^/\s]+)|@file/([^/\s]+)'
    FOLDER_MENTION_PATTERN = r'@文件夹/([^/\s]+)|@folder/([^/\s]+)'
    
    def __init__(self, db: Session, permission_engine: PermissionEngine):
        self.db = db
        self.permission_engine = permission_engine
    
    def parse_mentions(self, message: str, user_id: int) -> Dict[str, Any]:
        """解析消息中的@资源"""
        
        result = {
            'cleaned_message': message,
            'mentioned_files': [],
            'mentioned_folders': [],
            'total_context_size': 0,
            'errors': []
        }
        
        # 解析@文件
        file_mentions = re.findall(self.FILE_MENTION_PATTERN, message, re.IGNORECASE)
        for mention in file_mentions:
            file_name = mention[0] or mention[1]  # 支持中英文
            try:
                file_resource = self._resolve_file_mention(file_name, user_id)
                if file_resource:
                    result['mentioned_files'].append(file_resource)
                    result['total_context_size'] += file_resource.size
                    # 从消息中移除@标记
                    message = re.sub(f'@文件/{file_name}|@file/{file_name}', 
                                   f'[文件:{file_name}]', message, flags=re.IGNORECASE)
            except PermissionError as e:
                result['errors'].append(f"无权限访问文件: {file_name}")
            except FileNotFoundError:
                result['errors'].append(f"文件不存在: {file_name}")
        
        # 解析@文件夹
        folder_mentions = re.findall(self.FOLDER_MENTION_PATTERN, message, re.IGNORECASE)
        for mention in folder_mentions:
            folder_name = mention[0] or mention[1]
            try:
                folder_files = self._resolve_folder_mention(folder_name, user_id)
                result['mentioned_folders'].extend(folder_files)
                total_folder_size = sum(f.size for f in folder_files)
                result['total_context_size'] += total_folder_size
                # 从消息中移除@标记
                message = re.sub(f'@文件夹/{folder_name}|@folder/{folder_name}', 
                               f'[文件夹:{folder_name}]', message, flags=re.IGNORECASE)
            except PermissionError as e:
                result['errors'].append(f"无权限访问文件夹: {folder_name}")
            except FileNotFoundError:
                result['errors'].append(f"文件夹不存在: {folder_name}")
        
        result['cleaned_message'] = message
        return result
    
    def _resolve_file_mention(self, file_name: str, user_id: int) -> MentionedResource:
        """解析文件@引用"""
        
        # 查找文件（支持模糊匹配）
        file_record = self.db.query(File).filter(
            File.original_name.like(f'%{file_name}%')
        ).first()
        
        if not file_record:
            raise FileNotFoundError(f"File {file_name} not found")
        
        # 权限检查
        if not self.permission_engine.check_permission(
            resource_type='file',
            resource_id=str(file_record.id),
            subject_type='user',
            subject_id=str(user_id),
            action='read'
        ):
            raise PermissionError(f"No permission to access file {file_name}")
        
        # 读取文件内容
        content = self._read_file_content(file_record)
        
        return MentionedResource(
            type='file',
            id=file_record.id,
            name=file_record.original_name,
            content=content,
            size=len(content)
        )
    
    def _resolve_folder_mention(self, folder_name: str, user_id: int) -> List[MentionedResource]:
        """解析文件夹@引用"""
        
        # 查找文件夹
        folder = self.db.query(Folder).filter(
            Folder.name.like(f'%{folder_name}%')
        ).first()
        
        if not folder:
            raise FileNotFoundError(f"Folder {folder_name} not found")
        
        # 权限检查 - 检查文件夹权限
        if not self.permission_engine.check_permission(
            resource_type='folder',
            resource_id=str(folder.id),
            subject_type='user',
            subject_id=str(user_id),
            action='read'
        ):
            raise PermissionError(f"No permission to access folder {folder_name}")
        
        # 获取文件夹中的所有文件
        files = self.db.query(File).filter(File.folder_id == folder.id).all()
        
        mentioned_files = []
        for file_record in files:
            # 检查每个文件的权限
            if self.permission_engine.check_permission(
                resource_type='file',
                resource_id=str(file_record.id),
                subject_type='user',
                subject_id=str(user_id),
                action='read'
            ):
                content = self._read_file_content(file_record)
                mentioned_files.append(MentionedResource(
                    type='file',
                    id=file_record.id,
                    name=file_record.original_name,
                    content=content,
                    size=len(content)
                ))
        
        return mentioned_files
    
    def _read_file_content(self, file_record: File) -> str:
        """读取文件内容"""
        try:
            # 通过 physical_file 获取文件路径
            from app.services.local_file_storage import local_file_storage
            
            file_path = local_file_storage.base_dir / file_record.physical_file.storage_path
            
            # 根据文件类型选择读取方式
            if file_record.file_type == 'pdf':
                return self._extract_pdf_content(file_path)
            elif file_record.file_type in ['txt', 'md']:
                return self._read_text_file(file_path)
            elif file_record.file_type in ['doc', 'docx']:
                return self._extract_word_content(file_path)
            else:
                return f"[不支持的文件类型: {file_record.file_type}]"
                
        except Exception as e:
            return f"[文件读取失败: {str(e)}]"
    
    def _extract_pdf_content(self, file_path: str) -> str:
        """提取PDF内容"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                content = ""
                for page in reader.pages:
                    content += page.extract_text() + "\n"
                return content
        except ImportError:
            return "[需要安装 PyPDF2 来读取PDF文件]"
        except Exception as e:
            return f"[PDF读取失败: {str(e)}]"
    
    def _read_text_file(self, file_path: str) -> str:
        """读取文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as file:
                    return file.read()
            except:
                return "[文件编码不支持]"
        except Exception as e:
            return f"[文本文件读取失败: {str(e)}]"
```

### 2. 长上下文管理器

```python
class LongContextManager:
    """长上下文管理器"""
    
    MAX_CONTEXT_SIZE = 100000  # 100KB 默认限制
    MAX_FILES_PER_MESSAGE = 10  # 每条消息最多@10个文件
    
    def __init__(self, max_context_size: int = None):
        self.max_context_size = max_context_size or self.MAX_CONTEXT_SIZE
    
    def build_context(self, 
                     original_message: str,
                     mentioned_files: List[MentionedResource],
                     mentioned_folders: List[MentionedResource]) -> Dict[str, Any]:
        """构建长上下文"""
        
        all_files = mentioned_files + mentioned_folders
        
        # 检查文件数量限制
        if len(all_files) > self.MAX_FILES_PER_MESSAGE:
            raise ValueError(f"每条消息最多只能@{self.MAX_FILES_PER_MESSAGE}个文件")
        
        # 检查总大小限制
        total_size = sum(f.size for f in all_files)
        if total_size > self.max_context_size:
            raise ValueError(f"文件总大小超过限制 {self.max_context_size/1024:.1f}KB")
        
        # 构建上下文
        context_parts = []
        
        # 添加文件内容
        for file_resource in all_files:
            context_parts.append(f"=== 文件: {file_resource.name} ===")
            context_parts.append(file_resource.content)
            context_parts.append("=" * 50)
        
        # 添加用户消息
        context_parts.append("=== 用户问题 ===")
        context_parts.append(original_message)
        
        full_context = "\n\n".join(context_parts)
        
        return {
            'context': full_context,
            'total_size': len(full_context),
            'file_count': len(all_files),
            'files': [{'id': f.id, 'name': f.name, 'type': f.type} for f in all_files]
        }
```

### 3. 增强的聊天API

```python
@router.post("/chats/{chat_id}/messages-with-files", response_model=ResponseModel)
async def send_message_with_file_mentions(
    chat_id: int,
    message_request: MessageWithFilesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送包含@文件的消息"""
    
    try:
        # 初始化服务
        permission_engine = PermissionEngine(db)
        message_parser = MessageParser(db, permission_engine)
        context_manager = LongContextManager()
        
        # 解析消息中的@资源
        parse_result = message_parser.parse_mentions(
            message_request.content, 
            current_user.id
        )
        
        # 检查解析错误
        if parse_result['errors']:
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": "文件访问错误",
                    "errors": parse_result['errors']
                }
            )
        
        # 构建长上下文
        context_data = context_manager.build_context(
            parse_result['cleaned_message'],
            parse_result['mentioned_files'],
            parse_result['mentioned_folders']
        )
        
        # 调用AI服务 (使用长上下文而不是RAG)
        ai_response = await call_llm_with_long_context(
            context=context_data['context'],
            model="gpt-4-turbo",  # 支持长上下文的模型
            max_tokens=4000
        )
        
        # 保存消息记录
        message_record = Message(
            chat_id=chat_id,
            content=message_request.content,
            role='user',
            user_id=current_user.id
        )
        db.add(message_record)
        db.flush()
        
        # 保存文件关联
        for file_info in context_data['files']:
            file_mention = MessageFileMention(
                message_id=message_record.id,
                file_id=file_info['id'],
                mention_type=file_info['type']
            )
            db.add(file_mention)
        
        # 保存AI回复
        ai_message = Message(
            chat_id=chat_id,
            content=ai_response.content,
            role='assistant',
            model_name=ai_response.model,
            tokens_used=ai_response.tokens_used,
            cost=ai_response.cost,
            context_size=context_data['total_size']  # 记录上下文大小
        )
        db.add(ai_message)
        db.commit()
        
        return ResponseModel(
            success=True,
            data={
                "message": ai_message,
                "mentioned_files": context_data['files'],
                "context_stats": {
                    "total_size": context_data['total_size'],
                    "file_count": context_data['file_count']
                }
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"消息发送失败: {str(e)}")
```

### 4. 新增数据表

```sql
-- 消息文件@关联表
CREATE TABLE message_file_mentions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    message_id INT NOT NULL,
    file_id INT NOT NULL,
    mention_type ENUM('file', 'folder') DEFAULT 'file',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES files(id),
    INDEX idx_message_mentions (message_id),
    INDEX idx_file_mentions (file_id)
);

-- 扩展 messages 表
ALTER TABLE messages ADD COLUMN context_size INT NULL COMMENT '长上下文大小';
ALTER TABLE messages ADD COLUMN mention_count INT DEFAULT 0 COMMENT '@文件数量';
```

## 使用示例

### 前端调用示例
```javascript
// 发送包含@文件的消息
const response = await fetch('/api/v1/chats/123/messages-with-files', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        content: '请帮我总结 @文件/研究报告.pdf 的核心观点，并与 @文件夹/参考资料 进行对比分析'
    })
});
```

### API响应示例
```json
{
    "success": true,
    "data": {
        "message": {
            "id": 456,
            "content": "基于您提供的研究报告和参考资料，我总结出以下核心观点...",
            "role": "assistant",
            "tokens_used": 2500,
            "context_size": 45000
        },
        "mentioned_files": [
            {"id": 789, "name": "研究报告.pdf", "type": "file"},
            {"id": 790, "name": "参考文献1.pdf", "type": "file"},
            {"id": 791, "name": "参考文献2.pdf", "type": "file"}
        ],
        "context_stats": {
            "total_size": 45000,
            "file_count": 3
        }
    }
}
```

## 优势特点

1. **精确上下文**: 直接使用完整文件内容，不会丢失信息
2. **权限安全**: 基于可扩展权限架构，确保访问安全
3. **灵活@语法**: 支持中英文@语法，用户体验友好
4. **性能可控**: 内置大小和数量限制，防止滥用
5. **审计追踪**: 完整记录文件使用情况

这个设计很好地利用了我们之前设计的可扩展权限架构，同时为未来的功能扩展留出了空间。