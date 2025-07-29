"""Chat模块Service层业务逻辑 - 重构版本"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from datetime import datetime
from decimal import Decimal

from src.shared.exceptions import (
    BaseServiceException, NotFoundServiceException, 
    AccessDeniedServiceException, ValidationServiceException,
    BadRequestServiceException
)
from src.shared.error_codes import ErrorCodes
from src.shared.base_service import BaseService
from src.shared.ai_manager import get_ai_manager
from .models import Chat, Message, MessageFileReference, MessageRAGSource
from .schemas import CreateChatRequest, UpdateChatRequest, SendMessageRequest, EditMessageRequest


# 移除自定义异常类，统一使用标准Service异常


class ChatService(BaseService):
    """聊天管理服务"""
    
    # 定义方法可能抛出的异常（使用标准Service异常）
    METHOD_EXCEPTIONS = {
        "get_user_chats": {AccessDeniedServiceException},
        "create_chat": {ValidationServiceException, BadRequestServiceException},
        "update_chat": {NotFoundServiceException, AccessDeniedServiceException, ValidationServiceException},
        "delete_chat": {NotFoundServiceException, AccessDeniedServiceException},
        "get_chat_messages": {NotFoundServiceException, AccessDeniedServiceException},
        "send_message": {NotFoundServiceException, AccessDeniedServiceException, ValidationServiceException},
        "edit_message": {NotFoundServiceException, AccessDeniedServiceException, ValidationServiceException},
        "delete_message": {NotFoundServiceException, AccessDeniedServiceException},
    }
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.ai_manager = get_ai_manager(db)
    
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
            raise BadRequestServiceException(f"获取聊天列表失败: {str(e)}", "DATABASE_ERROR")
    
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
                    raise NotFoundServiceException("课程不存在或无权限访问", ErrorCodes.COURSE_NOT_FOUND)
            
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
            ai_response = self.ai_manager.generate_initial_response(
                message=chat_data.first_message,
                ai_model=chat_data.ai_model,
                rag_enabled=chat_data.rag_enabled,
                context_mode=chat_data.context_mode,
                chat_type=chat_data.chat_type,
                course_id=chat_data.course_id,
                file_ids=chat_data.file_ids,
                custom_prompt=chat_data.custom_prompt
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
            
            if not self.safe_commit("创建聊天"):
                raise BadRequestServiceException("创建聊天失败", "COMMIT_ERROR")
            
            # 刷新获取完整数据
            self.safe_refresh(chat, "创建聊天")
            self.safe_refresh(user_message, "创建聊天")
            self.safe_refresh(ai_message, "创建聊天")
            
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
            
        except BadRequestServiceException:
            self.handle_database_error("创建聊天", BadRequestServiceException("业务错误"))
            raise
        except Exception as e:
            self.handle_database_error("创建聊天", e)
            raise BadRequestServiceException(f"创建聊天失败: {str(e)}", "CREATE_ERROR")
    
    def update_chat(self, chat_id: int, chat_data: UpdateChatRequest, user_id: int) -> Chat:
        """更新聊天信息"""
        try:
            # 获取聊天并验证权限
            chat = self.db.query(Chat).filter(
                Chat.id == chat_id,
                Chat.user_id == user_id
            ).first()
            
            if not chat:
                raise NotFoundServiceException("聊天不存在或无权限访问", "ErrorCodes.CHAT_NOT_FOUND")
            
            # 更新字段
            if chat_data.title is not None:
                chat.title = chat_data.title
            
            if chat_data.ai_model is not None:
                chat.ai_model = chat_data.ai_model
            
            if chat_data.rag_enabled is not None:
                chat.rag_enabled = chat_data.rag_enabled
            
            if not self.safe_commit("更新聊天"):
                raise BadRequestServiceException("更新聊天失败", "COMMIT_ERROR")
            self.safe_refresh(chat, "更新聊天")
            
            return chat
            
        except BadRequestServiceException:
            self.handle_database_error("更新聊天", BadRequestServiceException("业务错误"))
            raise
        except Exception as e:
            self.handle_database_error("更新聊天", e)
            raise BadRequestServiceException(f"更新聊天失败: {str(e)}", "UPDATE_ERROR")
    
    def delete_chat(self, chat_id: int, user_id: int) -> None:
        """删除聊天"""
        try:
            # 获取聊天并验证权限
            chat = self.db.query(Chat).filter(
                Chat.id == chat_id,
                Chat.user_id == user_id
            ).first()
            
            if not chat:
                raise NotFoundServiceException("聊天不存在或无权限访问", "ErrorCodes.CHAT_NOT_FOUND")
            
            # 删除聊天（级联删除消息）
            self.db.delete(chat)
            if not self.safe_commit("删除聊天"):
                raise BadRequestServiceException("删除聊天失败", "COMMIT_ERROR")
            
        except BadRequestServiceException:
            self.handle_database_error("删除聊天", BadRequestServiceException("业务错误"))
            raise
        except Exception as e:
            self.handle_database_error("删除聊天", e)
            raise BadRequestServiceException(f"删除聊天失败: {str(e)}", "DELETE_ERROR")
    
    def get_chat_stats(self, chat_id: int) -> dict:
        """获取聊天统计信息"""
        try:
            message_count = self.db.query(Message).filter(Message.chat_id == chat_id).count()
            
            return {
                "message_count": message_count
            }
            
        except Exception as e:
            raise BadRequestServiceException(f"获取聊天统计失败: {str(e)}", "DATABASE_ERROR")
    
    def _generate_chat_title(self, first_message: str) -> str:
        """根据首条消息生成聊天标题"""
        # 简单实现：取前20个字符
        title = first_message[:20]
        if len(first_message) > 20:
            title += "..."
        return title


class MessageService(BaseService):
    """消息管理服务"""
    
    METHOD_EXCEPTIONS = {
        "get_chat_messages": {BadRequestServiceException},
        "send_message": {BadRequestServiceException},
        "edit_message": {BadRequestServiceException},
        "delete_message": {BadRequestServiceException},
    }
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.ai_manager = get_ai_manager(db)
    
    def get_chat_messages(self, chat_id: int, user_id: int, limit: int = 50, offset: int = 0) -> List[Message]:
        """获取聊天消息列表"""
        try:
            # 验证聊天权限
            chat = self.db.query(Chat).filter(
                Chat.id == chat_id,
                Chat.user_id == user_id
            ).first()
            
            if not chat:
                raise NotFoundServiceException("聊天不存在或无权限访问", "ErrorCodes.CHAT_NOT_FOUND")
            
            # 获取消息列表
            messages = self.db.query(Message)\
                .filter(Message.chat_id == chat_id)\
                .order_by(Message.created_at.asc())\
                .offset(offset)\
                .limit(limit)\
                .all()
                
            return messages
            
        except BadRequestServiceException:
            raise
        except Exception as e:
            raise BadRequestServiceException(f"获取消息列表失败: {str(e)}", "DATABASE_ERROR")
    
    def send_message(self, chat_id: int, message_data: SendMessageRequest, user_id: int) -> Dict[str, Any]:
        """发送消息并获取AI回复"""
        try:
            # 验证聊天权限
            chat = self.db.query(Chat).filter(
                Chat.id == chat_id,
                Chat.user_id == user_id
            ).first()
            
            if not chat:
                raise NotFoundServiceException("聊天不存在或无权限访问", "ErrorCodes.CHAT_NOT_FOUND")
            
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
            ai_response = self.ai_manager.generate_followup_response(
                chat_id=chat_id,
                message=message_data.content,
                ai_model=chat.ai_model,
                rag_enabled=chat.rag_enabled,
                context_mode=chat.context_mode,
                chat_type=chat.chat_type,
                course_id=chat.course_id,
                file_ids=message_data.file_ids,
                custom_prompt=chat.custom_prompt
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
            
            if not self.safe_commit("发送消息"):
                raise BadRequestServiceException("发送消息失败", "COMMIT_ERROR")
            
            # 刷新获取完整数据
            self.safe_refresh(user_message, "发送消息")
            self.safe_refresh(ai_message, "发送消息")
            
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
            
        except BadRequestServiceException:
            self.handle_database_error("发送消息", BadRequestServiceException("业务错误"))
            raise
        except Exception as e:
            self.handle_database_error("发送消息", e)
            raise BadRequestServiceException(f"发送消息失败: {str(e)}", "SEND_ERROR")
    
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
                raise NotFoundServiceException("消息不存在或无权限编辑", "ErrorCodes.MESSAGE_NOT_FOUND")
            
            # 更新消息内容
            message.content = message_data.content
            message.is_edited = True
            message.edited_at = datetime.utcnow()
            
            if not self.safe_commit("编辑消息"):
                raise BadRequestServiceException("编辑消息失败", "COMMIT_ERROR")
            self.safe_refresh(message, "编辑消息")
            
            return message
            
        except BadRequestServiceException:
            self.handle_database_error("编辑消息", BadRequestServiceException("业务错误"))
            raise
        except Exception as e:
            self.handle_database_error("编辑消息", e)
            raise BadRequestServiceException(f"编辑消息失败: {str(e)}", "EDIT_ERROR")
    
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
                raise NotFoundServiceException("消息不存在或无权限删除", "ErrorCodes.MESSAGE_NOT_FOUND")
            
            # 删除消息
            self.db.delete(message)
            if not self.safe_commit("删除消息"):
                raise BadRequestServiceException("删除消息失败", "COMMIT_ERROR")
            
        except BadRequestServiceException:
            self.handle_database_error("删除消息", BadRequestServiceException("业务错误"))
            raise
        except Exception as e:
            self.handle_database_error("删除消息", e)
            raise BadRequestServiceException(f"删除消息失败: {str(e)}", "DELETE_ERROR")