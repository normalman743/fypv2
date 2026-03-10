from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
import os
import logging

from app.models.chat import Chat
from app.models.course import Course
from app.models.message import Message
from app.models.file import File
from app.models.folder import Folder
from app.models.user import User
from app.models.message_reference import MessageFileReference, MessageRAGSource
from app.models.temporary_file import TemporaryFile
from app.schemas.chat import CreateChatRequest, UpdateChatRequest
from app.schemas.message import SendMessageRequest
from app.services.production_ai_service import create_ai_service
from app.core.exceptions import NotFoundError, ForbiddenError, BadRequestError
from app.utils.file_processing_utils import FileProcessingUtils
from app.utils.image_utils import image_to_base64, get_image_mime_type, is_image_file

logger = logging.getLogger(__name__)


class ChatService:
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
        """获取文件内容用于AI上下文 - 直接从磁盘读取，与临时文件处理保持一致"""
        if not files:
            return ""
        
        context_parts = []
        for file in files:
            try:
                # 获取物理文件路径
                if file.physical_file and file.physical_file.storage_path:
                    from app.core.config import settings
                    full_path = os.path.join(settings.upload_dir, file.physical_file.storage_path)
                    
                    if os.path.exists(full_path):
                        # 使用与RAG服务相同的文件解析逻辑
                        file_ext = os.path.splitext(file.original_name)[1].lower()
                        content_preview = self._extract_file_content(full_path, file_ext, file.original_name)
                        
                        context_parts.append(
                            f"文件: {file.original_name}\n"
                            f"类型: 正式文件\n"
                            f"内容:\n{content_preview}\n"
                        )
                    else:
                        # 文件不存在，回退到使用数据库中的预览
                        if file.is_processed and file.content_preview:
                            context_parts.append(f"文件名: {file.original_name}\n内容预览:\n{file.content_preview}\n")
                else:
                    # 没有物理文件路径，回退到使用数据库中的预览
                    if file.is_processed and file.content_preview:
                        context_parts.append(f"文件名: {file.original_name}\n内容预览:\n{file.content_preview}\n")
            except Exception as e:
                logger.error(f"无法读取文件内容: {file.original_name}, 错误: {str(e)}")
                # 回退到使用数据库中的预览
                if file.is_processed and file.content_preview:
                    context_parts.append(f"文件名: {file.original_name}\n内容预览:\n{file.content_preview}\n")
        
        return "\n---\n".join(context_parts) if context_parts else ""

    def _extract_file_content(self, file_path: str, file_ext: str, original_name: str) -> str:
        """使用与RAG服务相同的文件解析逻辑提取文件内容"""
        try:
            # 导入RAG服务的文档加载器
            from langchain_community.document_loaders import (
                PyPDFLoader, 
                Docx2txtLoader, 
                TextLoader,
                UnstructuredMarkdownLoader
            )
            
            # 与RAG服务相同的专门解析器配置
            specialized_loaders = {
                '.pdf': PyPDFLoader,
                '.docx': Docx2txtLoader,
                '.doc': Docx2txtLoader,
                '.md': UnstructuredMarkdownLoader,
            }
            
            # 选择合适的解析器
            if file_ext in specialized_loaders:
                loader_class = specialized_loaders[file_ext]
                logger.info(f"使用专门解析器: {loader_class.__name__} for {file_ext}")
            else:
                loader_class = TextLoader
                logger.info(f"使用通用TextLoader for {file_ext}")
            
            # 加载文档内容
            loader = loader_class(file_path)
            documents = loader.load()
            
            # 合并所有文档内容并限制长度
            full_content = "\n\n".join([doc.page_content for doc in documents])
            
            # 限制内容长度（与临时文件处理保持一致）
            if len(full_content) > 2000:
                content_preview = full_content[:2000] + "\n\n[内容已截断...]"
            else:
                content_preview = full_content
                
            return content_preview
            
        except Exception as e:
            logger.error(f"使用专门解析器失败 {original_name}: {e}")
            # 回退到简单的文本读取
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read(2000)
            except Exception as fallback_e:
                logger.error(f"回退文本读取也失败 {original_name}: {fallback_e}")
                return f"[无法读取文件内容: {str(fallback_e)}]"

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

    def get_user_chats(self, user_id: int) -> List[Chat]:
        """Get all chats for a user with course info and stats"""
        return self.db.query(Chat).options(
            joinedload(Chat.course),
            joinedload(Chat.messages)
        ).filter(Chat.user_id == user_id).order_by(Chat.updated_at.desc()).all()

    def create_chat_with_first_message(self, chat_data: CreateChatRequest, user_id: int) -> dict:
        """Create chat with first message and AI response"""
        
        # Validate course_id if provided
        if chat_data.chat_type == "course":
            if not chat_data.course_id:
                raise BadRequestError("Course ID is required for course chats", "COURSE_ID_REQUIRED")
            
            course = self.db.query(Course).filter(
                Course.id == chat_data.course_id,
                Course.user_id == user_id
            ).first()
            if not course:
                raise NotFoundError("Course not found or access denied", "COURSE_NOT_FOUND")

        # 处理文件夹和文件ID，合并去重
        files, unique_file_ids = self._get_files_from_folders_and_files(
            chat_data.file_ids or [], 
            chat_data.folder_ids or [], 
            user_id
        )
        
        # 处理临时文件
        temp_files = []
        expired_messages = []
        if chat_data.temporary_file_tokens:
            temp_files, expired_messages = FileProcessingUtils.process_temporary_files(
                self.db,
                chat_data.temporary_file_tokens,
                user_id
            )
        
        # 获取文件内容用于AI上下文
        file_context = self._get_file_contents_for_ai(files)
        
        # 获取临时文件内容
        if temp_files:
            temp_file_context = FileProcessingUtils.get_temporary_file_contents_for_ai(temp_files, self.db)
            if temp_file_context:
                file_context = file_context + ("\n" if file_context else "") + temp_file_context
        
        # 如果有过期文件，添加到上下文中
        if expired_messages:
            expired_context = "\n\n【注意】以下文件已过期无法访问：\n" + "\n".join(expired_messages)
            file_context = file_context + expired_context

        try:
            # Validate model and search combination
            from app.core.model_config import validate_model_search_combination
            from app.core.context_config import validate_context_mode
            
            if not validate_model_search_combination(chat_data.ai_model, chat_data.search_enabled):
                raise BadRequestError(
                    f"Model {chat_data.ai_model} does not support search functionality" if chat_data.search_enabled 
                    else f"Invalid AI model: {chat_data.ai_model}",
                    "INVALID_MODEL_CONFIG"
                )
            
            # Validate context mode
            if not validate_context_mode(chat_data.context_mode):
                raise BadRequestError(
                    f"Invalid context mode: {chat_data.context_mode}",
                    "INVALID_CONTEXT_MODE"
                )
            
            # Check user balance
            from app.core.exceptions import InsufficientBalanceError
            user = self.db.query(User).filter(User.id == user_id).first()
            if user.balance <= 0:
                raise InsufficientBalanceError("余额不足，请充值后继续使用AI模型")
            
            # 如果是课程相关聊天，检查课程权限
            if chat_data.chat_type == 'course' and chat_data.course_id:
                course = self.db.query(Course).filter(
                    Course.id == chat_data.course_id,
                    Course.user_id == user_id
                ).first()
                if not course:
                    raise BadRequestError("Course not found or access denied", "COURSE_NOT_FOUND")
            
            # 对于general类型聊天，course_id应该为None
            course_id = chat_data.course_id if chat_data.chat_type == 'course' and chat_data.course_id != 0 else None
            
            # Create chat with temporary title
            chat = Chat(
                title="新聊天",  # Will be updated after AI response
                chat_type=chat_data.chat_type,
                course_id=course_id,
                user_id=user_id,
                custom_prompt=chat_data.custom_prompt,
                ai_model=chat_data.ai_model,
                search_enabled=chat_data.search_enabled,
                context_mode=chat_data.context_mode
            )
            self.db.add(chat)
            self.db.flush()  # Get chat ID without committing

            # Create user message
            user_message = Message(
                chat_id=chat.id,
                content=chat_data.first_message,
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
            if chat_data.folder_ids:
                for folder_id in chat_data.folder_ids:
                    folder_ref = MessageFileReference(
                        message_id=user_message.id,
                        file_id=folder_id,
                        reference_type='folder'
                    )
                    self.db.add(folder_ref)
            
            # Add temporary file references
            temp_file_attachments = []
            for temp_file in temp_files:
                temp_ref = MessageFileReference(
                    message_id=user_message.id,
                    temporary_file_id=temp_file.id,
                    reference_type='temporary_file'
                )
                self.db.add(temp_ref)
                temp_file_attachments.append({
                    "id": temp_file.id,
                    "token": temp_file.token,
                    "filename": temp_file.original_name,
                    "file_size": temp_file.file_size,
                    "expires_at": temp_file.expires_at.isoformat()
                })

            # Prepare images for AI
            images = self._prepare_images_for_ai(temp_files)
            if images:
                logger.info(f"🖼️ 准备了 {len(images)} 张图片用于AI处理")
            
            # Generate AI response with file context and model settings (first message, no history)
            ai_response = self.ai_service.generate_response(
                message=chat_data.first_message,
                chat_type=chat_data.chat_type,
                course_id=chat_data.course_id,
                file_context=file_context,
                ai_model=chat.ai_model,
                search_enabled=chat.search_enabled,
                conversation_history=[],  # 第一条消息没有历史
                stream=False,
                images=images  # 传递图片数据
            )

            # Create AI message
            ai_message = Message(
                chat_id=chat.id,
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
                ai_message.rag_sources = ai_response.rag_sources

            # Update user balance
            from decimal import Decimal
            cost_decimal = Decimal(str(ai_response.cost))
            user.balance -= cost_decimal
            user.total_spent += cost_decimal
            
            # Generate and update chat title
            new_title = self.ai_service.generate_chat_title(chat_data.first_message)
            chat.title = new_title
            
            self.db.commit()

            # Reload chat with course info
            chat = self.db.query(Chat).options(joinedload(Chat.course)).filter(Chat.id == chat.id).first()

            # Build response
            return {
                "chat": {
                    "id": chat.id,
                    "title": chat.title,
                    "chat_type": chat.chat_type,
                    "course_id": chat.course_id,
                    "user_id": chat.user_id,
                    "custom_prompt": chat.custom_prompt,
                    "ai_model": chat.ai_model,
                    "search_enabled": chat.search_enabled,
                    "context_mode": chat.context_mode,
                    "created_at": chat.created_at,
                    "updated_at": chat.updated_at
                },
                "user_message": {
                    "id": user_message.id,
                    "chat_id": user_message.chat_id,
                    "content": user_message.content,
                    "role": user_message.role,
                    "tokens_used": user_message.tokens_used,
                    "cost": user_message.cost,
                    "created_at": user_message.created_at,
                    "file_attachments": file_attachments,
                    "temporary_file_attachments": temp_file_attachments
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
                "chat_title_updated": True,
                "new_chat_title": new_title
            }

        except IntegrityError:
            self.db.rollback()
            raise BadRequestError("Failed to create chat", "CHAT_CREATE_FAILED")

    def create_chat_with_first_message_stream(self, chat_data: CreateChatRequest, user_id: int):
        """流式创建聊天和首条消息"""
        # 暂时使用非流式方式，完整实现需要重构较多代码
        result = self.create_chat_with_first_message(chat_data, user_id)
        
        # 转换datetime和Decimal对象为字符串以便JSON序列化
        def convert_for_json(obj):
            from decimal import Decimal
            if isinstance(obj, dict):
                return {k: convert_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_for_json(item) for item in obj]
            elif hasattr(obj, 'isoformat'):  # datetime对象
                return obj.isoformat()
            elif isinstance(obj, Decimal):  # Decimal对象
                return float(obj)
            return obj
        
        serializable_result = convert_for_json(result)
        
        # 发送创建完成的消息
        yield {
            "type": "chat_created",
            "data": serializable_result
        }

    def update_chat(self, chat_id: int, chat_data: UpdateChatRequest, user_id: int) -> Chat:
        """Update chat title"""
        chat = self.db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.user_id == user_id
        ).first()
        
        if not chat:
            raise NotFoundError("Chat not found", "CHAT_NOT_FOUND")

        chat.title = chat_data.title
        self.db.commit()
        self.db.refresh(chat)
        return chat

    def delete_chat(self, chat_id: int, user_id: int) -> bool:
        """Delete chat and all its messages"""
        chat = self.db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.user_id == user_id
        ).first()
        
        if not chat:
            raise NotFoundError("Chat not found", "CHAT_NOT_FOUND")

        self.db.delete(chat)
        self.db.commit()
        return True

    def get_chat_stats(self, chat: Chat) -> dict:
        """Get chat statistics"""
        message_count = len(chat.messages) if hasattr(chat, 'messages') and chat.messages else 0
        return {"message_count": message_count}