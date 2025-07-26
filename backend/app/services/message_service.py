from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
import logging
import os

from app.models.chat import Chat
from app.models.message import Message
from app.models.file import File
from app.models.folder import Folder
from app.models.course import Course
from app.models.user import User
from app.models.message_reference import MessageFileReference, MessageRAGSource
from app.models.temporary_file import TemporaryFile
from app.schemas.message import SendMessageRequest, EditMessageRequest
from app.services.production_ai_service import create_ai_service
from app.core.exceptions import NotFoundError, ForbiddenError, BadRequestError
from app.utils.image_utils import image_to_base64, get_image_mime_type, is_image_file

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

    def _prepare_images_for_ai(self, temporary_files: List[TemporaryFile]) -> List[Dict[str, Any]]:
        """
        准备图片文件用于AI处理
        
        Args:
            temporary_files: 临时文件列表
            
        Returns:
            图片数据列表，格式适合AI API调用
        """
        images = []
        image_count = 0
        
        for temp_file in temporary_files:
            if is_image_file(temp_file.original_name):
                image_count += 1
                # 获取物理文件路径
                if temp_file.physical_file and temp_file.physical_file.storage_path:
                    storage_path = temp_file.physical_file.storage_path
                    logger.info(f"   原始存储路径: {storage_path}")
                    
                    # 如果路径是相对路径，拼接完整路径
                    if not os.path.isabs(storage_path):
                        from app.services.local_file_storage import local_file_storage
                        base_dir = str(local_file_storage.base_dir)
                        logger.info(f"   Base目录: {base_dir}")
                        
                        # 检查是否已经包含base_dir路径，避免重复拼接
                        if storage_path.startswith('storage/uploads/'):
                            # 去掉前缀，直接使用当前工作目录拼接
                            file_path = os.path.join(os.getcwd(), storage_path)
                        else:
                            file_path = os.path.join(base_dir, storage_path)
                    else:
                        file_path = storage_path
                        
                    logger.info(f"   最终文件路径: {file_path}")
                    logger.info(f"   文件是否存在: {os.path.exists(file_path)}")
                    
                    # 转换为base64
                    base64_image = image_to_base64(file_path)
                    if base64_image:
                        mime_type = get_image_mime_type(temp_file.original_name)
                        images.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        })
                        # 添加base64数据调试日志
                        logger.info(f"🖼️ 准备图片 {image_count}: {temp_file.original_name} ({mime_type})")
                        logger.info(f"   Base64长度: {len(base64_image)} 字符")
                        logger.info(f"   Base64前缀: {base64_image[:50]}...")
                        logger.info(f"   完整URL: data:{mime_type};base64,{base64_image[:100]}...")
                    else:
                        logger.warning(f"❌ 图片 {image_count}: {temp_file.original_name} 转换base64失败")
                else:
                    logger.warning(f"❌ 图片 {image_count}: {temp_file.original_name} 物理文件路径缺失")
        
        if image_count > 0:
            logger.info(f"📊 图片处理总结: 发现 {image_count} 个图片文件，成功准备 {len(images)} 个")
        
        return images

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
        
        # 从历史消息中提取临时文件（如果当前消息没有临时文件）
        historical_temporary_files, historical_expired_files = self._extract_temporary_files_from_history(chat_id, temporary_files)
        logger.info(f"🔍 历史文件提取结果: {len(historical_temporary_files)} 个有效, {len(historical_expired_files)} 个过期")
        
        # 合并当前和历史临时文件
        all_temporary_files = temporary_files + historical_temporary_files
        
        # 合并过期文件信息
        all_expired_files = expired_file_info + [f"临时文件 '{f.original_name}' 已过期" for f in historical_expired_files]
        
        # 如果有历史过期文件，在文件上下文中添加明确说明
        if historical_expired_files and not temporary_files:
            expired_context = "\n".join([f"临时文件 '{f.original_name}' 已过期，无法访问原始内容" for f in historical_expired_files])
            file_context += f"\n\n过期文件说明：\n{expired_context}\n"
            logger.info(f"📋 添加了 {len(historical_expired_files)} 个过期文件的说明到文件上下文")
        
        # 添加临时文件内容到上下文
        if all_temporary_files:
            temp_context_parts = []
            for temp_file in all_temporary_files:
                # 读取临时文件内容预览
                if temp_file.physical_file:
                    # 获取正确的文件路径
                    storage_path = temp_file.physical_file.storage_path
                    if not os.path.isabs(storage_path):
                        from app.services.local_file_storage import local_file_storage
                        file_path = os.path.join(str(local_file_storage.base_dir), storage_path)
                    else:
                        file_path = storage_path
                    
                    file_extension = temp_file.original_name.split('.')[-1].lower() if '.' in temp_file.original_name else ''
                    
                    try:
                        content_preview = None
                        
                        # 根据文件类型选择合适的解析器
                        if file_extension == 'pdf':
                            from langchain.document_loaders import PyPDFLoader
                            loader = PyPDFLoader(file_path)
                            documents = loader.load()
                            # 合并所有页面的内容
                            content_preview = "\n".join([doc.page_content[:500] for doc in documents[:3]])  # 前3页，每页500字符
                            logger.info(f"✅ 成功解析PDF: {temp_file.original_name}")
                        
                        elif file_extension in ['doc', 'docx']:
                            from langchain.document_loaders import Docx2txtLoader
                            loader = Docx2txtLoader(file_path)
                            documents = loader.load()
                            content_preview = documents[0].page_content[:1500] if documents else ""
                            logger.info(f"✅ 成功解析Word文档: {temp_file.original_name}")
                        
                        elif file_extension in ['txt', 'md', 'py', 'js', 'html', 'css', 'json', 'csv', 'xml']:
                            # 文本文件直接读取
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content_preview = f.read(1500)
                            logger.info(f"✅ 成功读取文本文件: {temp_file.original_name}")
                        
                        else:
                            # 其他文件类型，尝试作为文本读取
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content_preview = f.read(1000)
                            except:
                                content_preview = None
                        
                        if content_preview:
                            temp_context_parts.append(f"临时文件: {temp_file.original_name}\n文件类型: {file_extension}\n内容:\n{content_preview}\n")
                        else:
                            temp_context_parts.append(f"临时文件: {temp_file.original_name} (类型: {file_extension}，无法解析内容)\n")
                            
                    except Exception as e:
                        logger.warning(f"解析临时文件失败 {temp_file.original_name}: {str(e)}")
                        temp_context_parts.append(f"临时文件: {temp_file.original_name} (解析失败: {str(e)})\n")
            
            if temp_context_parts:
                file_context += "\n" + "="*50 + "\n".join(temp_context_parts)
        
        # 添加过期文件信息到上下文
        if all_expired_files:
            logger.warning(f"⚠️ 有 {len(all_expired_files)} 个文件无法访问，将告知AI")
            file_context += "\n" + "="*50 + "\n注意：以下文件无法访问：\n" + "\n".join(all_expired_files) + "\n"

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

            # Check user balance before generating response
            from app.core.exceptions import InsufficientBalanceError
            user = self.db.query(User).filter(User.id == chat.user_id).first()
            if user.balance <= 0:
                raise InsufficientBalanceError("余额不足，请充值后继续使用AI模型")
            
            # Get conversation history based on context mode
            from app.core.context_config import get_context_message_limit
            message_limit = get_context_message_limit(chat.context_mode)
            
            history_messages = self.db.query(Message).filter(
                Message.chat_id == chat_id
            ).order_by(Message.created_at.desc()).limit(message_limit).all()
            
            # Build conversation history for AI (reverse to chronological order)
            conversation_history = []
            for msg in reversed(history_messages):
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            logger.info(f"📚 历史对话({chat.context_mode}模式): {len(conversation_history)} 条消息 (限制:{message_limit})")
            
            # Prepare images for AI
            images = self._prepare_images_for_ai(all_temporary_files)
            
            # Generate AI response with file context
            logger.info(f"🤖 调用AI服务生成回复...")
            logger.info(f"   模型: {chat.ai_model} (搜索: {chat.search_enabled})")
            ai_response = self.ai_service.generate_response(
                message=message_data.content,
                chat_type=chat.chat_type,
                course_id=chat.course_id,
                file_context=file_context,
                ai_model=chat.ai_model,
                search_enabled=chat.search_enabled,
                conversation_history=conversation_history,
                stream=False,
                images=images,  # 传递图片数据
                custom_prompt=chat.custom_prompt  # 传递自定义提示词
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
                input_tokens=ai_response.input_tokens,
                output_tokens=ai_response.output_tokens,
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

            # Update user balance
            from decimal import Decimal
            cost_decimal = Decimal(str(ai_response.cost))
            user.balance -= cost_decimal
            user.total_spent += cost_decimal

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

    def send_message_stream(self, chat_id: int, message_data: SendMessageRequest, user_id: int):
        """流式发送消息和获取AI回复"""
        
        logger.info(f"📨 流式发送消息到聊天 {chat_id}，用户 {user_id}")
        
        # Check if chat exists and user has access
        chat = self.db.query(Chat).options(joinedload(Chat.course)).filter(
            Chat.id == chat_id,
            Chat.user_id == user_id
        ).first()
        if not chat:
            raise NotFoundError("Chat not found", "CHAT_NOT_FOUND")

        # Check user balance before generating response
        from app.core.exceptions import InsufficientBalanceError
        user = self.db.query(User).filter(User.id == chat.user_id).first()
        if user.balance <= 0:
            raise InsufficientBalanceError("余额不足，请充值后继续使用AI模型")

        # 处理文件夹和文件ID，合并去重
        files, unique_file_ids = self._get_files_from_folders_and_files(
            message_data.file_ids or [], 
            message_data.folder_ids or [], 
            user_id
        )
        
        # 处理临时文件
        temporary_files = []
        expired_file_info = []
        if message_data.temporary_file_tokens:
            for token in message_data.temporary_file_tokens:
                temp_file = self.db.query(TemporaryFile).filter(
                    TemporaryFile.token == token,
                    TemporaryFile.user_id == user_id
                ).first()
                
                if not temp_file:
                    expired_file_info.append(f"临时文件 (token: {token[:8]}...) 不存在或已被删除")
                    continue
                
                if temp_file.is_expired:
                    expired_file_info.append(f"临时文件 '{temp_file.original_name}' 已过期")
                    continue
                
                temporary_files.append(temp_file)

        # 获取文件内容用于AI上下文
        file_context = self._get_file_contents_for_ai(files)
        
        # 从历史消息中提取临时文件（如果当前消息没有临时文件）
        historical_temporary_files, historical_expired_files = self._extract_temporary_files_from_history(chat_id, temporary_files)
        
        # 合并当前和历史临时文件
        all_temporary_files = temporary_files + historical_temporary_files
        
        # 合并过期文件信息
        all_expired_files = expired_file_info + [f"临时文件 '{f.original_name}' 已过期" for f in historical_expired_files]
        
        # 如果有历史过期文件，在文件上下文中添加明确说明
        if historical_expired_files and not temporary_files:
            expired_context = "\n".join([f"临时文件 '{f.original_name}' 已过期，无法访问原始内容" for f in historical_expired_files])
            file_context += f"\n\n过期文件说明：\n{expired_context}\n"
            logger.info(f"📋 添加了 {len(historical_expired_files)} 个过期文件的说明到文件上下文")
        
        # 添加临时文件内容到上下文
        if all_temporary_files:
            temp_context_parts = []
            for temp_file in all_temporary_files:
                if temp_file.physical_file:
                    # 获取正确的文件路径
                    storage_path = temp_file.physical_file.storage_path
                    if not os.path.isabs(storage_path):
                        from app.services.local_file_storage import local_file_storage
                        file_path = os.path.join(str(local_file_storage.base_dir), storage_path)
                    else:
                        file_path = storage_path
                    
                    file_extension = temp_file.original_name.split('.')[-1].lower() if '.' in temp_file.original_name else ''
                    
                    try:
                        content_preview = None
                        
                        # 根据文件类型选择合适的解析器
                        if file_extension == 'pdf':
                            from langchain.document_loaders import PyPDFLoader
                            loader = PyPDFLoader(file_path)
                            documents = loader.load()
                            content_preview = "\\n".join([doc.page_content[:500] for doc in documents[:3]])
                        
                        elif file_extension in ['doc', 'docx']:
                            from langchain.document_loaders import Docx2txtLoader
                            loader = Docx2txtLoader(file_path)
                            documents = loader.load()
                            content_preview = documents[0].page_content[:1500] if documents else ""
                        
                        elif file_extension in ['txt', 'md', 'py', 'js', 'html', 'css', 'json', 'csv', 'xml']:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content_preview = f.read(1500)
                        
                        else:
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content_preview = f.read(1000)
                            except:
                                content_preview = None
                        
                        if content_preview:
                            temp_context_parts.append(f"临时文件: {temp_file.original_name}\\n文件类型: {file_extension}\\n内容:\\n{content_preview}\\n")
                        else:
                            temp_context_parts.append(f"临时文件: {temp_file.original_name} (类型: {file_extension}，无法解析内容)\\n")
                            
                    except Exception as e:
                        temp_context_parts.append(f"临时文件: {temp_file.original_name} (解析失败: {str(e)})\\n")
            
            if temp_context_parts:
                file_context += "\\n" + "="*50 + "\\n".join(temp_context_parts)
        
        # 添加过期文件信息到上下文
        if all_expired_files:
            file_context += "\\n" + "="*50 + "\\n注意：以下文件无法访问：\\n" + "\\n".join(all_expired_files) + "\\n"

        try:
            # Create user message
            user_message = Message(
                chat_id=chat_id,
                content=message_data.content,
                role="user",
                tokens_used=None,
                cost=None
            )
            self.db.add(user_message)
            self.db.flush()

            # Add file attachments
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
            
            # Add folder references
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

            # Get conversation history
            from app.core.context_config import get_context_message_limit
            message_limit = get_context_message_limit(chat.context_mode)
            
            history_messages = self.db.query(Message).filter(
                Message.chat_id == chat_id
            ).order_by(Message.created_at.desc()).limit(message_limit).all()
            
            conversation_history = []
            for msg in reversed(history_messages):
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content
                })

            # 发送用户消息信息
            yield {
                "type": "user_message",
                "user_message": {
                    "id": user_message.id,
                    "chat_id": user_message.chat_id,
                    "content": user_message.content,
                    "role": user_message.role,
                    "created_at": user_message.created_at.isoformat(),
                    "file_attachments": file_attachments
                }
            }

            # Prepare images for AI
            images = self._prepare_images_for_ai(all_temporary_files)
            
            # Generate AI response with streaming
            ai_stream = self.ai_service.generate_response(
                message=message_data.content,
                chat_type=chat.chat_type,
                course_id=chat.course_id,
                file_context=file_context,
                ai_model=chat.ai_model,
                search_enabled=chat.search_enabled,
                conversation_history=conversation_history,
                stream=True,
                images=images,  # 传递图片数据
                custom_prompt=chat.custom_prompt  # 传递自定义提示词
            )

            # Create AI message placeholder
            ai_message = Message(
                chat_id=chat_id,
                content="",
                role="assistant",
                tokens_used=None,
                input_tokens=None,
                output_tokens=None,
                cost=None
            )
            self.db.add(ai_message)
            self.db.flush()

            # Process stream
            full_content = ""
            for chunk in ai_stream:
                if chunk["type"] == "content":
                    full_content += chunk["content"]
                    yield {
                        "type": "content",
                        "content": chunk["content"],
                        "ai_message_id": ai_message.id
                    }
                elif chunk["type"] == "usage":
                    # Update AI message with final content and usage
                    ai_message.content = full_content
                    ai_message.tokens_used = chunk["tokens_used"]
                    ai_message.input_tokens = chunk["input_tokens"]
                    ai_message.output_tokens = chunk["output_tokens"]
                    ai_message.cost = chunk["cost"]
                    ai_message.rag_sources = chunk["rag_sources"]

                    # Update user balance
                    from decimal import Decimal
                    cost_decimal = Decimal(str(chunk["cost"]))
                    user.balance -= cost_decimal
                    user.total_spent += cost_decimal

                    # Update chat title if needed
                    message_count = self.db.query(Message).filter(
                        Message.chat_id == chat_id,
                        Message.role == "user"
                    ).count()
                    
                    chat_title_updated = False
                    new_chat_title = None
                    if message_count == 1 and chat.title == "新聊天":
                        new_chat_title = self.ai_service.generate_chat_title(message_data.content)
                        chat.title = new_chat_title
                        chat_title_updated = True

                    # Update chat timestamp
                    self.db.query(Chat).filter(Chat.id == chat_id).update({
                        "updated_at": user_message.created_at
                    })

                    self.db.commit()

                    # Send final usage info (确保Decimal类型转换)
                    yield {
                        "type": "completion",
                        "ai_message": {
                            "id": ai_message.id,
                            "chat_id": ai_message.chat_id,
                            "content": ai_message.content,
                            "role": ai_message.role,
                            "tokens_used": ai_message.tokens_used,
                            "cost": float(ai_message.cost) if ai_message.cost else None,
                            "created_at": ai_message.created_at.isoformat(),
                            "rag_sources": chunk["rag_sources"]
                        },
                        "chat_title_updated": chat_title_updated,
                        "new_chat_title": new_chat_title
                    }

        except Exception as e:
            self.db.rollback()
            raise e

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

    def _extract_temporary_files_from_history(self, chat_id: int, current_temporary_files: List[TemporaryFile]) -> tuple[List[TemporaryFile], List[TemporaryFile]]:
        """
        从历史消息中提取临时文件，处理过期和有效的文件
        
        Args:
            chat_id: 聊天ID
            current_temporary_files: 当前消息的临时文件列表
            
        Returns:
            tuple: (有效的临时文件列表, 过期的临时文件列表)
        """
        # 如果当前消息有临时文件，不需要加载历史文件
        if current_temporary_files:
            return [], []
            
        # 获取聊天的上下文模式和消息限制
        from app.core.context_config import get_context_message_limit
        chat = self.db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            return [], []
            
        message_limit = get_context_message_limit(chat.context_mode)
        
        # 获取历史消息ID
        history_messages = self.db.query(Message.id).filter(
            Message.chat_id == chat_id
        ).order_by(Message.created_at.desc()).limit(message_limit).all()
        
        if not history_messages:
            return [], []
            
        history_message_ids = [msg.id for msg in history_messages]
        
        # 从message_file_references中找到历史消息使用的临时文件
        temp_file_refs = self.db.query(MessageFileReference).filter(
            MessageFileReference.message_id.in_(history_message_ids),
            MessageFileReference.reference_type == 'temporary_file',
            MessageFileReference.temporary_file_id.is_not(None)
        ).all()
        
        if not temp_file_refs:
            return [], []
            
        # 提取临时文件ID
        temp_file_ids = list(set([ref.temporary_file_id for ref in temp_file_refs]))
        
        # 获取临时文件，检查有效性
        temp_files = self.db.query(TemporaryFile).filter(
            TemporaryFile.id.in_(temp_file_ids)
        ).all()
        
        valid_files = []
        expired_files = []
        
        for temp_file in temp_files:
            if temp_file.is_expired:
                expired_files.append(temp_file)
            else:
                valid_files.append(temp_file)
        
        logger.info(f"📚 历史临时文件状态: {len(valid_files)} 个有效, {len(expired_files)} 个过期")
        
        # 处理过期文件：在文件上下文中添加过期提示
        if expired_files:
            expired_info = []
            for expired_file in expired_files:
                expired_info.append(f"临时文件 '{expired_file.original_name}' 已过期")
            logger.warning(f"⚠️ 过期文件: {', '.join([f.original_name for f in expired_files])}")
        
        return valid_files, expired_files

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
            "model_name": message.model_name,
            "tokens_used": message.tokens_used,
            "cost": message.cost,
            "response_time_ms": message.response_time_ms,
            "rag_sources": message.rag_sources,
            "created_at": message.created_at,
            "context_size": message.context_size,
            "direct_file_count": message.direct_file_count,
            "rag_source_count": message.rag_source_count,
            "input_tokens": message.input_tokens,
            "output_tokens": message.output_tokens,
            "file_attachments": file_attachments
        }