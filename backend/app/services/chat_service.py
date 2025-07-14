from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.models.chat import Chat
from app.models.course import Course
from app.models.message import Message
from app.models.file import File
# from app.models.message_attachment import MessageFileAttachment, MessageRAGSource  # V2.1: 已移除
from app.schemas.chat import CreateChatRequest, UpdateChatRequest
from app.schemas.message import SendMessageRequest
from app.services.enhanced_ai_service import create_ai_service
from app.core.exceptions import NotFoundError, ForbiddenError, BadRequestError


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = create_ai_service()

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

        # Validate file_ids if provided
        if chat_data.file_ids:
            files = self.db.query(File).filter(File.id.in_(chat_data.file_ids)).all()
            if len(files) != len(chat_data.file_ids):
                raise BadRequestError("Some files not found", "FILE_NOT_FOUND")
            
            # Check file access permissions (must belong to user's courses or be global)
            for file in files:
                if file.course_id:  # Course file
                    course = self.db.query(Course).filter(
                        Course.id == file.course_id,
                        Course.user_id == user_id
                    ).first()
                    if not course:
                        raise ForbiddenError("Access denied to some files")

        try:
            # Create chat with temporary title
            chat = Chat(
                title="新聊天",  # Will be updated after AI response
                chat_type=chat_data.chat_type,
                course_id=chat_data.course_id,
                user_id=user_id,
                custom_prompt=chat_data.custom_prompt
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

            # Add file attachments if any
            file_attachments = []
            if chat_data.file_ids:
                for file_id in chat_data.file_ids:
                    file = next(f for f in files if f.id == file_id)
                    attachment = MessageFileAttachment(
                        message_id=user_message.id,
                        file_id=file_id,
                        filename=f"attachment_{file_id}_{file.original_name}"
                    )
                    self.db.add(attachment)
                    file_attachments.append({
                        "id": file_id,
                        "filename": attachment.filename,
                        "original_name": file.original_name,
                        "file_size": file.file_size
                    })

            # Generate AI response
            ai_response = self.ai_service.generate_response(
                message=chat_data.first_message,
                chat_type=chat_data.chat_type,
                course_id=chat_data.course_id
            )

            # Create AI message
            ai_message = Message(
                chat_id=chat.id,
                content=ai_response.content,
                role="assistant",
                tokens_used=ai_response.tokens_used,
                cost=ai_response.cost
            )
            self.db.add(ai_message)
            self.db.flush()

            # Add RAG sources (V2.1: 存储在message的rag_sources JSON字段中)
            if hasattr(ai_response, 'rag_sources') and ai_response.rag_sources:
                ai_message.rag_sources = ai_response.rag_sources

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
                "chat_title_updated": True,
                "new_chat_title": new_title
            }

        except IntegrityError:
            self.db.rollback()
            raise BadRequestError("Failed to create chat", "CHAT_CREATE_FAILED")

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