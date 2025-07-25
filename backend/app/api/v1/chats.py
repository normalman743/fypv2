from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.services.chat_service import ChatService
from app.schemas.chat import (
    CreateChatRequest,
    UpdateChatRequest,
    ChatListResponse,
    ChatCreateResponse,
    ChatUpdateResponse,
    ChatResponse,
    ChatStats,
    CourseInfo
)
from app.schemas.common import SuccessResponse
from app.models.user import User

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=ChatListResponse)
async def get_chats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's chat list"""
    service = ChatService(db)
    chats = service.get_user_chats(current_user.id)
    
    # Convert to response format
    chat_list = []
    for chat in chats:
        # Get course info if exists
        course_info = None
        if chat.course:
            course_info = CourseInfo(
                id=chat.course.id,
                name=chat.course.name,
                code=chat.course.code
            )
        
        # Get chat stats
        stats = service.get_chat_stats(chat)
        
        chat_data = ChatResponse(
            id=chat.id,
            title=chat.title,
            chat_type=chat.chat_type,
            course_id=chat.course_id,
            user_id=chat.user_id,
            custom_prompt=chat.custom_prompt,
            ai_model=chat.ai_model,
            search_enabled=chat.search_enabled,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            course=course_info,
            stats=ChatStats(**stats)
        )
        chat_list.append(chat_data)
    
    return ChatListResponse(
        success=True,
        data={"chats": [chat.model_dump() for chat in chat_list]}
    )


@router.post("", response_model=ChatCreateResponse)
async def create_chat(
    chat_data: CreateChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create chat with first message and AI response"""
    service = ChatService(db)
    result = service.create_chat_with_first_message(chat_data, current_user.id)
    
    return ChatCreateResponse(
        success=True,
        data=result
    )


@router.put("/{chat_id}", response_model=ChatUpdateResponse)
async def update_chat(
    chat_id: int = Path(..., description="Chat ID"),
    chat_data: UpdateChatRequest = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update chat title"""
    service = ChatService(db)
    chat = service.update_chat(chat_id, chat_data, current_user.id)
    
    return ChatUpdateResponse(
        success=True,
        data={
            "chat": {
                "id": chat.id,
                "title": chat.title,
                "updated_at": chat.updated_at
            }
        }
    )


@router.delete("/{chat_id}", response_model=SuccessResponse)
async def delete_chat(
    chat_id: int = Path(..., description="Chat ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete chat"""
    service = ChatService(db)
    service.delete_chat(chat_id, current_user.id)
    
    return SuccessResponse(success=True)