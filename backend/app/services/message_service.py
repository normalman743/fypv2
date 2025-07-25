from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
import logging

from app.models.chat import Chat
from app.models.message import Message
from app.models.file import File
from app.models.folder import Folder
from app.models.course import Course
from app.models.message_reference import MessageFileReference, MessageRAGSource
from app.models.temporary_file import TemporaryFile
from app.schemas.message import SendMessageRequest, EditMessageRequest
from app.services.production_ai_service import create_ai_service
from app.core.exceptions import NotFoundError, ForbiddenError, BadRequestError

logger = logging.getLogger(__name__)


class MessageService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = create_ai_service()

    def _get_files_from_folders_and_files(self, file_ids: List[int], folder_ids: List[int], user_id: int) -> tuple[List[File], List[int]]:
        """获取文件夹中的文件和直接指定的文件，合并去重"""
        all_files = []
        all_file_ids = []
        
        # 处理直接指定的文件
        if file_ids:
            files = self.db.query(File).filter(File.id.in_(file_ids)).all()
            if len(files) != len(file_ids):
                raise BadRequestError("Some files not found", "FILE_NOT_FOUND")
            all_files.extend(files)
            all_file_ids.extend(file_ids)
        
        # 处理文件夹中的文件
        if folder_ids:
            folders = self.db.query(Folder).filter(Folder.id.in_(folder_ids)).all()
            if len(folders) != len(folder_ids):
                raise BadRequestError("Some folders not found", "FOLDER_NOT_FOUND")
            
            # 验证文件夹权限
            for folder in folders:
                course = self.db.query(Course).filter(
                    Course.id == folder.course_id,
                    Course.user_id == user_id
                ).first()
                if not course:
                    raise ForbiddenError("Access denied to some folders")
            
            # 获取文件夹中的文件
            for folder_id in folder_ids:
                folder_files = self.db.query(File).filter(File.folder_id == folder_id).all()
                all_files.extend(folder_files)
                all_file_ids.extend([f.id for f in folder_files])
        
        # 去重
        unique_file_ids = list(set(all_file_ids))
        unique_files = []
        seen_ids = set()
        
        for file in all_files:
            if file.id not in seen_ids:
                unique_files.append(file)
                seen_ids.add(file.id)
        
        # 验证所有文件的权限
        for file in unique_files:
            if file.course_id:
                course = self.db.query(Course).filter(
                    Course.id == file.course_id,
                    Course.user_id == user_id
                ).first()
                if not course:
                    raise ForbiddenError("Access denied to some files")
        
        return unique_files, unique_file_ids

    def _get_file_contents_for_ai(self, files: List[File]) -> str:
        """获取文件内容用于AI上下文"""
        if not files:
            return ""
        
        context_parts = []
        for file in files:
            # 只处理已处理的文件
            if file.is_processed and file.content_preview:
                context_parts.append(f"文件名: {file.original_name}\n内容预览:\n{file.content_preview}\n")
        
        return "\n" + "="*50 + "\n".join(context_parts) if context_parts else ""

    def get_chat_messages(self, chat_id: int, user_id: int) -> List[Message]:
        """Get all messages in a chat (check chat ownership)"""
        # Check if chat exists and user has access
        chat = self.db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.user_id == user_id
        ).first()
        if not chat:
            raise NotFoundError("Chat not found", "CHAT_NOT_FOUND")

        return self.db.query(Message).options(
            joinedload(Message.file_references),
            joinedload(Message.rag_sources_tracked)
        ).filter(Message.chat_id == chat_id).order_by(Message.created_at.asc()).all()

    def send_message(self, chat_id: int, message_data: SendMessageRequest, user_id: int) -> dict:
        """Send message and get AI response"""
        
        logger.info(f"📨 发送消息到聊天 {chat_id}，用户 {user_id}")
        logger.info(f"   消息内容: {message_data.content[:100]}{'...' if len(message_data.content) > 100 else ''}")
        
        # Check if chat exists and user has access
        chat = self.db.query(Chat).options(joinedload(Chat.course)).filter(
            Chat.id == chat_id,
            Chat.user_id == user_id
        ).first()
        if not chat:
            raise NotFoundError("Chat not found", "CHAT_NOT_FOUND")

        # 处理文件夹和文件ID，合并去重
        files, unique_file_ids = self._get_files_from_folders_and_files(
            message_data.file_ids or [], 
            message_data.folder_ids or [], 
            user_id
        )
        
        if files:
            logger.info(f"📎 附加了 {len(files)} 个普通文件: {[f.original_name for f in files]}")
        
        # 处理临时文件
        temporary_files = []
        expired_file_info = []
        if message_data.temporary_file_tokens:
            logger.info(f"🔄 处理 {len(message_data.temporary_file_tokens)} 个临时文件")
            for i, token in enumerate(message_data.temporary_file_tokens, 1):
                temp_file = self.db.query(TemporaryFile).filter(
                    TemporaryFile.token == token,
                    TemporaryFile.user_id == user_id  # 验证文件属于当前用户
                ).first()
                
                if not temp_file:
                    # 文件不存在，可能已被删除
                    logger.warning(f"   ❌ 临时文件 {i}: token {token[:8]}... 不存在或已被删除")
                    expired_file_info.append(f"临时文件 (token: {token[:8]}...) 不存在或已被删除，用户可能需要重新上传")
                    continue
                
                if temp_file.is_expired:
                    # 文件已过期，记录信息但不阻止对话
                    logger.warning(f"   ⏰ 临时文件 {i}: '{temp_file.original_name}' 已过期 ({temp_file.expires_at})")
                    expired_file_info.append(f"临时文件 '{temp_file.original_name}' 已于 {temp_file.expires_at.strftime('%Y-%m-%d %H:%M:%S')} 过期，用户可能需要重新上传")
                    continue
                
                logger.info(f"   ✅ 临时文件 {i}: '{temp_file.original_name}' ({temp_file.file_size} bytes)")
                temporary_files.append(temp_file)
        
        # 获取文件内容用于AI上下文（包括临时文件）
        file_context = self._get_file_contents_for_ai(files)
        
        # 添加临时文件内容到上下文
        if temporary_files:
            temp_context_parts = []
            for temp_file in temporary_files:
                # 读取临时文件内容预览
                if temp_file.physical_file:
                    try:
                        with open(temp_file.physical_file.storage_path, 'r', encoding='utf-8') as f:
                            content_preview = f.read(1000)  # 读取前1000个字符作为预览
                            temp_context_parts.append(f"临时文件: {temp_file.original_name}\n内容预览:\n{content_preview}\n")
                    except:
                        # 如果无法读取文件内容，仅添加文件名
                        temp_context_parts.append(f"临时文件: {temp_file.original_name}\n")
            
            if temp_context_parts:
                file_context += "\n" + "="*50 + "\n".join(temp_context_parts)
        
        # 添加过期文件信息到上下文
        if expired_file_info:
            logger.warning(f"⚠️ 有 {len(expired_file_info)} 个文件无法访问，将告知AI")
            file_context += "\n" + "="*50 + "\n注意：以下文件无法访问：\n" + "\n".join(expired_file_info) + "\n"

        # 记录上下文信息
        if file_context:
            context_preview = file_context[:200].replace('\n', ' ')
            logger.info(f"📋 文件上下文长度: {len(file_context)} 字符")
            logger.info(f"   预览: {context_preview}...")

        try:
            # Create user message
            logger.info(f"💾 创建用户消息记录")
            user_message = Message(
                chat_id=chat_id,
                content=message_data.content,
                role="user",
                tokens_used=None,
                cost=None
            )
            self.db.add(user_message)
            self.db.flush()

            # Add file attachments for all unique files
            file_attachments = []
            for file in files:
                attachment = MessageFileReference(
                    message_id=user_message.id,
                    file_id=file.id,
                    reference_type='file'
                )
                self.db.add(attachment)
                file_attachments.append({
                    "id": file.id,
                    "filename": file.original_name,
                    "original_name": file.original_name,
                    "file_size": file.file_size
                })
            
            # Add folder references if any
            if message_data.folder_ids:
                for folder_id in message_data.folder_ids:
                    folder_ref = MessageFileReference(
                        message_id=user_message.id,
                        file_id=folder_id,
                        reference_type='folder'
                    )
                    self.db.add(folder_ref)
            
            # Add temporary file references
            for temp_file in temporary_files:
                temp_attachment = MessageFileReference(
                    message_id=user_message.id,
                    temporary_file_id=temp_file.id,
                    reference_type='temporary_file'
                )
                self.db.add(temp_attachment)
                file_attachments.append({
                    "id": temp_file.id,
                    "filename": temp_file.original_name,
                    "original_name": temp_file.original_name,
                    "file_size": temp_file.file_size,
                    "is_temporary": True,
                    "token": temp_file.token
                })

            # Generate AI response with file context
            logger.info(f"🤖 调用AI服务生成回复...")
            ai_response = self.ai_service.generate_response(
                message=message_data.content,
                chat_type=chat.chat_type,
                course_id=chat.course_id,
                file_context=file_context
            )
            
            logger.info(f"✅ AI回复生成完成")
            logger.info(f"   回复长度: {len(ai_response.content)} 字符")
            logger.info(f"   使用token: {ai_response.tokens_used}")
            logger.info(f"   花费: ${ai_response.cost:.4f}")

            # Create AI message
            logger.info(f"💾 创建AI消息记录")
            ai_message = Message(
                chat_id=chat_id,
                content=ai_response.content,
                role="assistant",
                tokens_used=ai_response.tokens_used,
                cost=ai_response.cost
            )
            self.db.add(ai_message)
            self.db.flush()

            # Add RAG sources (V2.1: 存储在message的rag_sources JSON字段中)
            if hasattr(ai_response, 'rag_sources') and ai_response.rag_sources:
                logger.info(f"📚 添加 {len(ai_response.rag_sources)} 个RAG来源")
                ai_message.rag_sources = ai_response.rag_sources

            # Check if this is the first user message (excluding system messages)
            message_count = self.db.query(Message).filter(
                Message.chat_id == chat_id,
                Message.role == "user"
            ).count()
            
            chat_title_updated = False
            new_chat_title = None
            
            # If this is the first user message and chat has default title, update it
            if message_count == 1 and chat.title == "新聊天":
                logger.info(f"🏷️ 生成聊天标题...")
                new_chat_title = self.ai_service.generate_chat_title(message_data.content)
                chat.title = new_chat_title
                chat_title_updated = True
                logger.info(f"   新标题: {new_chat_title}")

            # Update chat timestamp
            self.db.query(Chat).filter(Chat.id == chat_id).update({
                "updated_at": user_message.created_at
            })

            self.db.commit()
            logger.info(f"✅ 消息对话完成，用户消息ID: {user_message.id}，AI消息ID: {ai_message.id}")

            # Build response
            return {
                "user_message": {
                    "id": user_message.id,
                    "chat_id": user_message.chat_id,
                    "content": user_message.content,
                    "role": user_message.role,
                    "tokens_used": user_message.tokens_used,
                    "cost": user_message.cost,
                    "created_at": user_message.created_at,
                    "file_attachments": file_attachments
                },
                "ai_message": {
                    "id": ai_message.id,
                    "chat_id": ai_message.chat_id,
                    "content": ai_message.content,
                    "role": ai_message.role,
                    "tokens_used": ai_message.tokens_used,
                    "cost": ai_message.cost,
                    "created_at": ai_message.created_at,
                    "rag_sources": ai_response.rag_sources,
                    "file_attachments": []
                },
                "chat_title_updated": chat_title_updated,
                "new_chat_title": new_chat_title
            }

        except IntegrityError:
            self.db.rollback()
            raise BadRequestError("Failed to send message", "MESSAGE_SEND_FAILED")

    def edit_message(self, message_id: int, message_data: EditMessageRequest, user_id: int) -> Message:
        """Edit message content (only user messages)"""
        
        # Get message with chat info
        message = self.db.query(Message).options(
            joinedload(Message.chat)
        ).filter(Message.id == message_id).first()
        
        if not message:
            raise NotFoundError("Message not found", "MESSAGE_NOT_FOUND")
        
        # Check if user owns the chat
        if message.chat.user_id != user_id:
            raise ForbiddenError("You don't have permission to edit this message")
        
        # Only allow editing user messages
        if message.role != "user":
            raise BadRequestError("Can only edit user messages", "INVALID_MESSAGE_TYPE")

        message.content = message_data.content
        self.db.commit()
        self.db.refresh(message)
        return message

    def delete_message(self, message_id: int, user_id: int) -> bool:
        """Delete message"""
        
        # Get message with chat info
        message = self.db.query(Message).options(
            joinedload(Message.chat)
        ).filter(Message.id == message_id).first()
        
        if not message:
            raise NotFoundError("Message not found", "MESSAGE_NOT_FOUND")
        
        # Check if user owns the chat
        if message.chat.user_id != user_id:
            raise ForbiddenError("You don't have permission to delete this message")

        self.db.delete(message)
        self.db.commit()
        return True

    def format_message_response(self, message: Message) -> dict:
        """Format message for API response"""
        file_attachments = []
        if hasattr(message, 'file_references') and message.file_references:
            for attachment in message.file_references:
                if attachment.reference_type == 'temporary_file' and attachment.temporary_file:
                    # 临时文件
                    temp_file = attachment.temporary_file
                    file_attachments.append({
                        "id": temp_file.id,
                        "filename": temp_file.original_name,
                        "original_name": temp_file.original_name,
                        "file_size": temp_file.file_size,
                        "is_temporary": True,
                        "token": temp_file.token,
                        "expires_at": temp_file.expires_at.isoformat(),
                        "is_expired": temp_file.is_expired
                    })
                elif attachment.reference_type == 'file' and attachment.file:
                    # 普通文件
                    file_attachments.append({
                        "id": attachment.file.id,
                        "filename": attachment.file.original_name,
                        "original_name": attachment.file.original_name,
                        "file_size": attachment.file.file_size,
                        "is_temporary": False
                    })

        rag_sources = []
        if hasattr(message, 'rag_sources_tracked') and message.rag_sources_tracked:
            for source in message.rag_sources_tracked:
                rag_sources.append({
                    "source_file": source.source_file,
                    "chunk_id": source.chunk_id
                })

        return {
            "id": message.id,
            "chat_id": message.chat_id,
            "content": message.content,
            "role": message.role,
            "tokens_used": message.tokens_used,
            "cost": message.cost,
            "created_at": message.created_at,
            "file_attachments": file_attachments,
            "rag_sources": rag_sources if rag_sources else []
        }