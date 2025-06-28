from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.models.chat import Chat
from app.models.message import Message
from app.models.file import File
from app.models.course import Course
from app.models.message_attachment import MessageFileAttachment, MessageRAGSource
from app.schemas.message import SendMessageRequest, EditMessageRequest
from app.services.ai_service import MockAIService
from app.core.exceptions import NotFoundError, ForbiddenError, BadRequestError


class MessageService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = MockAIService()

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
            joinedload(Message.file_attachments),
            joinedload(Message.rag_sources)
        ).filter(Message.chat_id == chat_id).order_by(Message.created_at.asc()).all()

    def send_message(self, chat_id: int, message_data: SendMessageRequest, user_id: int) -> dict:
        """Send message and get AI response"""
        
        # Check if chat exists and user has access
        chat = self.db.query(Chat).options(joinedload(Chat.course)).filter(
            Chat.id == chat_id,
            Chat.user_id == user_id
        ).first()
        if not chat:
            raise NotFoundError("Chat not found", "CHAT_NOT_FOUND")

        # Validate file_ids if provided
        files = []
        if message_data.file_ids:
            files = self.db.query(File).filter(File.id.in_(message_data.file_ids)).all()
            if len(files) != len(message_data.file_ids):
                raise BadRequestError("Some files not found", "FILE_NOT_FOUND")
            
            # Check file access permissions
            for file in files:
                if file.course_id:  # Course file
                    course = self.db.query(Course).filter(
                        Course.id == file.course_id,
                        Course.user_id == user_id
                    ).first()
                    if not course:
                        raise ForbiddenError("Access denied to some files")

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

            # Add file attachments if any
            file_attachments = []
            if message_data.file_ids:
                for file_id in message_data.file_ids:
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
                message=message_data.content,
                chat_type=chat.chat_type,
                course_id=chat.course_id
            )

            # Create AI message
            ai_message = Message(
                chat_id=chat_id,
                content=ai_response.content,
                role="assistant",
                tokens_used=ai_response.tokens_used,
                cost=ai_response.cost
            )
            self.db.add(ai_message)
            self.db.flush()

            # Add RAG sources
            for source in ai_response.rag_sources:
                rag_source = MessageRAGSource(
                    message_id=ai_message.id,
                    source_file=source["source_file"],
                    chunk_id=source["chunk_id"]
                )
                self.db.add(rag_source)

            # Check if this is the first user message (excluding system messages)
            message_count = self.db.query(Message).filter(
                Message.chat_id == chat_id,
                Message.role == "user"
            ).count()
            
            chat_title_updated = False
            new_chat_title = None
            
            # If this is the first user message and chat has default title, update it
            if message_count == 1 and chat.title == "新聊天":
                new_chat_title = self.ai_service.generate_chat_title(message_data.content)
                chat.title = new_chat_title
                chat_title_updated = True

            # Update chat timestamp
            self.db.query(Chat).filter(Chat.id == chat_id).update({
                "updated_at": user_message.created_at
            })

            self.db.commit()

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
        if hasattr(message, 'file_attachments') and message.file_attachments:
            for attachment in message.file_attachments:
                file_attachments.append({
                    "id": attachment.file_id,
                    "filename": attachment.filename,
                    "original_name": attachment.file.original_name if attachment.file else attachment.filename,
                    "file_size": attachment.file.file_size if attachment.file else 0
                })

        rag_sources = []
        if hasattr(message, 'rag_sources') and message.rag_sources:
            for source in message.rag_sources:
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