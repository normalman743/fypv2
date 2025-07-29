"""Chat模块Service层业务逻辑"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from datetime import datetime
from decimal import Decimal

from src.shared.exceptions import BaseServiceException
from .models import Chat, Message, MessageFileReference, MessageRAGSource
from .schemas import CreateChatRequest, UpdateChatRequest, SendMessageRequest, EditMessageRequest
from src.ai.service import AIService
from src.ai.schemas import AIRequest


class ChatServiceException(BaseServiceException):
    """Chat服务异常基类"""
    pass


class ChatService:
    """聊天管理服务"""
    
    # 定义方法可能抛出的异常
    METHOD_EXCEPTIONS = {
        "get_user_chats": [ChatServiceException],
        "create_chat": [ChatServiceException],
        "update_chat": [ChatServiceException],
        "delete_chat": [ChatServiceException],
        "get_chat_stats": [ChatServiceException],
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService(db)
    
    def get_user_chats(self, user_id: int, chat_type: Optional[str] = None) -> List[Chat]:
        """获取用户的聊天列表"""
        try:
            query = self.db.query(Chat)\
                .options(
                    joinedload(Chat.course),
                    joinedload(Chat.messages)
                )\
                .filter(Chat.user_id == user_id)
            
            if chat_type:
                query = query.filter(Chat.chat_type == chat_type)
            
            chats = query.order_by(desc(Chat.updated_at)).all()
            
            return chats
            
        except Exception as e:
            raise ChatServiceException(f"获取聊天列表失败: {str(e)}", "DATABASE_ERROR")
    
    def create_chat(self, chat_data: CreateChatRequest, user_id: int) -> Dict[str, Any]:
        """创建聊天并发送首条消息"""
        try:
            # 验证课程权限（如果是课程聊天）
            if chat_data.chat_type == 'course' and chat_data.course_id:
                from src.course.models import Course
                course = self.db.query(Course).filter(
                    Course.id == chat_data.course_id,
                    or_(Course.user_id == user_id, Course.user.has(role="admin"))
                ).first()
                
                if not course:
                    raise ChatServiceException("课程不存在或无权限访问", "COURSE_NOT_FOUND")
            
            # 创建聊天
            chat = Chat(
                title=self._generate_chat_title(chat_data.first_message),
                chat_type=chat_data.chat_type,
                course_id=chat_data.course_id,
                user_id=user_id,
                custom_prompt=chat_data.custom_prompt,
                ai_model=chat_data.ai_model,
                search_enabled=chat_data.search_enabled,
                context_mode=chat_data.context_mode,
                rag_enabled=chat_data.rag_enabled
            )
            
            self.db.add(chat)
            self.db.flush()  # 获取chat_id但不提交
            
            # 创建用户消息
            user_message = Message(
                chat_id=chat.id,
                content=chat_data.first_message,
                role='user'
            )
            
            self.db.add(user_message)
            self.db.flush()
            
            # 处理文件引用
            if chat_data.file_ids:
                for file_id in chat_data.file_ids:
                    file_ref = MessageFileReference(
                        message_id=user_message.id,
                        file_id=file_id
                    )
                    self.db.add(file_ref)
            
            # 生成AI回复
            ai_response = self._generate_ai_response_with_service(
                chat_data.first_message,
                chat_data.ai_model,
                chat_data.rag_enabled,
                chat_data.context_mode,
                chat_data.chat_type,
                chat_data.course_id,
                chat_data.file_ids,
                chat_data.custom_prompt
            )
            
            # 创建AI消息
            ai_message = Message(
                chat_id=chat.id,
                content=ai_response['content'],
                role='assistant',
                model_name=chat_data.ai_model,
                tokens_used=ai_response.get('tokens_used'),
                input_tokens=ai_response.get('input_tokens'),
                output_tokens=ai_response.get('output_tokens'),
                cost=ai_response.get('cost'),
                response_time_ms=ai_response.get('response_time_ms'),
                rag_sources=ai_response.get('rag_sources'),
                context_size=ai_response.get('context_size'),
                direct_file_count=len(chat_data.file_ids) if chat_data.file_ids else 0,
                rag_source_count=len(ai_response.get('rag_sources', []))
            )
            
            self.db.add(ai_message)
            self.db.commit()
            
            # 刷新获取完整数据
            self.db.refresh(chat)
            self.db.refresh(user_message)
            self.db.refresh(ai_message)
            
            return {
                "chat": {
                    "id": chat.id,
                    "title": chat.title,
                    "chat_type": chat.chat_type,
                    "created_at": chat.created_at
                },
                "user_message": {
                    "id": user_message.id,
                    "content": user_message.content,
                    "role": user_message.role,
                    "created_at": user_message.created_at
                },
                "ai_message": {
                    "id": ai_message.id,
                    "content": ai_message.content,
                    "role": ai_message.role,
                    "created_at": ai_message.created_at
                }
            }
            
        except ChatServiceException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise ChatServiceException(f"创建聊天失败: {str(e)}", "CREATE_ERROR")
    
    def update_chat(self, chat_id: int, chat_data: UpdateChatRequest, user_id: int) -> Chat:
        """更新聊天信息"""
        try:
            # 获取聊天并验证权限
            chat = self.db.query(Chat).filter(
                Chat.id == chat_id,
                Chat.user_id == user_id
            ).first()
            
            if not chat:
                raise ChatServiceException("聊天不存在或无权限访问", "CHAT_NOT_FOUND")
            
            # 更新字段
            if chat_data.title is not None:
                chat.title = chat_data.title
            
            if chat_data.ai_model is not None:
                chat.ai_model = chat_data.ai_model
            
            if chat_data.rag_enabled is not None:
                chat.rag_enabled = chat_data.rag_enabled
            
            self.db.commit()
            self.db.refresh(chat)
            
            return chat
            
        except ChatServiceException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise ChatServiceException(f"更新聊天失败: {str(e)}", "UPDATE_ERROR")
    
    def delete_chat(self, chat_id: int, user_id: int) -> None:
        """删除聊天"""
        try:
            # 获取聊天并验证权限
            chat = self.db.query(Chat).filter(
                Chat.id == chat_id,
                Chat.user_id == user_id
            ).first()
            
            if not chat:
                raise ChatServiceException("聊天不存在或无权限访问", "CHAT_NOT_FOUND")
            
            # 删除聊天（级联删除消息）
            self.db.delete(chat)
            self.db.commit()
            
        except ChatServiceException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise ChatServiceException(f"删除聊天失败: {str(e)}", "DELETE_ERROR")
    
    def get_chat_stats(self, chat_id: int) -> dict:
        """获取聊天统计信息"""
        try:
            message_count = self.db.query(Message).filter(Message.chat_id == chat_id).count()
            
            return {
                "message_count": message_count
            }
            
        except Exception as e:
            raise ChatServiceException(f"获取聊天统计失败: {str(e)}", "DATABASE_ERROR")
    
    def _generate_chat_title(self, first_message: str) -> str:
        """根据首条消息生成聊天标题"""
        # 简单实现：取前20个字符
        title = first_message[:20]
        if len(first_message) > 20:
            title += "..."
        return title
    
    def _generate_ai_response_with_service(self, message: str, ai_model: str, rag_enabled: bool, 
                                          context_mode: str, chat_type: str, course_id: Optional[int],
                                          file_ids: Optional[List[int]] = None, custom_prompt: Optional[str] = None,
                                          chat_id: Optional[int] = None) -> Dict[str, Any]:
        """使用AI服务生成回复"""
        try:
            # 构建AI请求
            ai_request = AIRequest(
                message=message,
                ai_model=ai_model,
                context_mode=context_mode,
                rag_enabled=rag_enabled,
                chat_type=chat_type,
                course_id=course_id,
                file_ids=file_ids,
                custom_prompt=custom_prompt
            )
            
            # 获取对话历史（如果有chat_id）
            conversation_history = None
            if chat_id:
                conversation_history = self._get_conversation_history(chat_id)
            
            # 调用AI服务
            ai_response = self.ai_service.generate_response(ai_request, conversation_history)
            
            # 转换为字典格式
            return {
                "content": ai_response.content,
                "tokens_used": ai_response.tokens_used,
                "input_tokens": ai_response.input_tokens,
                "output_tokens": ai_response.output_tokens,
                "cost": ai_response.cost,
                "response_time_ms": ai_response.response_time_ms,
                "rag_sources": [{
                    "source_file": source.source_file,
                    "chunk_id": source.chunk_id,
                    "content": source.content,
                    "score": source.score,
                    "file_id": source.file_id,
                    "course_id": source.course_id
                } for source in (ai_response.rag_sources or [])],
                "context_size": ai_response.context_size
            }
            
        except Exception as e:
            # 降级到简单回复
            print(f"⚠️ AI服务调用失败，使用降级回复: {e}")
            return {
                "content": f"抱歉，AI服务暂时不可用。您的消息已收到：{message[:50]}...",
                "tokens_used": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": Decimal("0"),
                "response_time_ms": 0,
                "rag_sources": [],
                "context_size": 0
            }


class MessageService:
    """消息管理服务"""
    
    METHOD_EXCEPTIONS = {
        "get_chat_messages": [ChatServiceException],
        "send_message": [ChatServiceException],
        "edit_message": [ChatServiceException],
        "delete_message": [ChatServiceException],
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService(db)
    
    def get_chat_messages(self, chat_id: int, user_id: int, limit: int = 50, offset: int = 0) -> List[Message]:
        """获取聊天消息列表"""
        try:
            # 验证聊天权限
            chat = self.db.query(Chat).filter(
                Chat.id == chat_id,
                Chat.user_id == user_id
            ).first()
            
            if not chat:
                raise ChatServiceException("聊天不存在或无权限访问", "CHAT_NOT_FOUND")
            
            # 获取消息列表
            messages = self.db.query(Message)\
                .filter(Message.chat_id == chat_id)\
                .order_by(Message.created_at.asc())\
                .offset(offset)\
                .limit(limit)\
                .all()
                
            return messages
            
        except ChatServiceException:
            raise
        except Exception as e:
            raise ChatServiceException(f"获取消息列表失败: {str(e)}", "DATABASE_ERROR")
    
    def send_message(self, chat_id: int, message_data: SendMessageRequest, user_id: int) -> Dict[str, Any]:
        """发送消息并获取AI回复"""
        try:
            # 验证聊天权限
            chat = self.db.query(Chat).filter(
                Chat.id == chat_id,
                Chat.user_id == user_id
            ).first()
            
            if not chat:
                raise ChatServiceException("聊天不存在或无权限访问", "CHAT_NOT_FOUND")
            
            # 创建用户消息
            user_message = Message(
                chat_id=chat_id,
                content=message_data.content,
                role='user'
            )
            
            self.db.add(user_message)
            self.db.flush()
            
            # 处理文件引用
            if message_data.file_ids:
                for file_id in message_data.file_ids:
                    file_ref = MessageFileReference(
                        message_id=user_message.id,
                        file_id=file_id
                    )
                    self.db.add(file_ref)
            
            # 生成AI回复
            ai_response = self._generate_ai_response_with_service(
                message_data.content,
                chat.ai_model,
                chat.rag_enabled,
                chat.context_mode,
                chat.chat_type,
                chat.course_id,
                message_data.file_ids,
                chat.custom_prompt,
                chat_id
            )
            
            # 创建AI消息
            ai_message = Message(
                chat_id=chat_id,
                content=ai_response['content'],
                role='assistant',
                model_name=chat.ai_model,
                tokens_used=ai_response.get('tokens_used'),
                input_tokens=ai_response.get('input_tokens'),
                output_tokens=ai_response.get('output_tokens'),
                cost=ai_response.get('cost'),
                response_time_ms=ai_response.get('response_time_ms'),
                rag_sources=ai_response.get('rag_sources'),
                context_size=ai_response.get('context_size'),
                direct_file_count=len(message_data.file_ids) if message_data.file_ids else 0,
                rag_source_count=len(ai_response.get('rag_sources', []))
            )
            
            self.db.add(ai_message)
            
            # 更新聊天的最后更新时间
            chat.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # 刷新获取完整数据
            self.db.refresh(user_message)
            self.db.refresh(ai_message)
            
            return {
                "user_message": {
                    "id": user_message.id,
                    "content": user_message.content,
                    "role": user_message.role,
                    "created_at": user_message.created_at
                },
                "ai_message": {
                    "id": ai_message.id,
                    "content": ai_message.content,
                    "role": ai_message.role,
                    "created_at": ai_message.created_at
                }
            }
            
        except ChatServiceException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise ChatServiceException(f"发送消息失败: {str(e)}", "SEND_ERROR")
    
    def edit_message(self, message_id: int, message_data: EditMessageRequest, user_id: int) -> Message:
        """编辑消息"""
        try:
            # 获取消息并验证权限
            message = self.db.query(Message)\
                .join(Message.chat)\
                .filter(
                    Message.id == message_id,
                    Message.role == 'user',  # 只能编辑用户消息
                    Chat.user_id == user_id
                ).first()
            
            if not message:
                raise ChatServiceException("消息不存在或无权限编辑", "MESSAGE_NOT_FOUND")
            
            # 更新消息内容
            message.content = message_data.content
            message.is_edited = True
            message.edited_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(message)
            
            return message
            
        except ChatServiceException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise ChatServiceException(f"编辑消息失败: {str(e)}", "EDIT_ERROR")
    
    def delete_message(self, message_id: int, user_id: int) -> None:
        """删除消息"""
        try:
            # 获取消息并验证权限
            message = self.db.query(Message)\
                .join(Message.chat)\
                .filter(
                    Message.id == message_id,
                    Chat.user_id == user_id
                ).first()
            
            if not message:
                raise ChatServiceException("消息不存在或无权限删除", "MESSAGE_NOT_FOUND")
            
            # 删除消息
            self.db.delete(message)
            self.db.commit()
            
        except ChatServiceException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise ChatServiceException(f"删除消息失败: {str(e)}", "DELETE_ERROR")
    
    def _generate_ai_response_with_service(self, message: str, ai_model: str, rag_enabled: bool, 
                                          context_mode: str, chat_type: str, course_id: Optional[int],
                                          file_ids: Optional[List[int]] = None, custom_prompt: Optional[str] = None,
                                          chat_id: Optional[int] = None) -> Dict[str, Any]:
        """使用AI服务生成回复"""
        try:
            # 构建AI请求
            ai_request = AIRequest(
                message=message,
                ai_model=ai_model,
                context_mode=context_mode,
                rag_enabled=rag_enabled,
                chat_type=chat_type,
                course_id=course_id,
                file_ids=file_ids,
                custom_prompt=custom_prompt
            )
            
            # 获取对话历史（如果有chat_id）
            conversation_history = None
            if chat_id:
                conversation_history = self._get_conversation_history(chat_id)
            
            # 调用AI服务
            ai_response = self.ai_service.generate_response(ai_request, conversation_history)
            
            # 转换为字典格式
            return {
                "content": ai_response.content,
                "tokens_used": ai_response.tokens_used,
                "input_tokens": ai_response.input_tokens,
                "output_tokens": ai_response.output_tokens,
                "cost": ai_response.cost,
                "response_time_ms": ai_response.response_time_ms,
                "rag_sources": [{
                    "source_file": source.source_file,
                    "chunk_id": source.chunk_id,
                    "content": source.content,
                    "score": source.score,
                    "file_id": source.file_id,
                    "course_id": source.course_id
                } for source in (ai_response.rag_sources or [])],
                "context_size": ai_response.context_size
            }
            
        except Exception as e:
            # 降级到简单回复
            print(f"⚠️ AI服务调用失败，使用降级回复: {e}")
            return {
                "content": f"抱歉，AI服务暂时不可用。您的消息已收到：{message[:50]}...",
                "tokens_used": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": Decimal("0"),
                "response_time_ms": 0,
                "rag_sources": [],
                "context_size": 0
            }
    
    def _get_conversation_history(self, chat_id: int, limit: int = 10) -> List[Dict[str, str]]:
        """获取对话历史"""
        try:
            messages = self.db.query(Message)\
                .filter(Message.chat_id == chat_id)\
                .order_by(Message.created_at.desc())\
                .limit(limit)\
                .all()
            
            # 按时间正序排列并转换格式
            history = []
            for message in reversed(messages):
                history.append({
                    "role": message.role,
                    "content": message.content
                })
            
            return history
            
        except Exception as e:
            print(f"⚠️ 获取对话历史失败: {e}")
            return []