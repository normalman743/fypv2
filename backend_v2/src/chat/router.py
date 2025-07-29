"""Chat模块API路由"""
from fastapi import APIRouter, Depends, Path, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List

from src.shared.dependencies import get_db, get_current_user
from src.shared.exceptions import handle_service_exceptions
from src.shared.schemas import BaseResponse, MessageResponse
from src.auth.models import User
from .service import ChatService, MessageService
from .schemas import (
    CreateChatRequest, UpdateChatRequest, SendMessageRequest, EditMessageRequest,
    ChatListResponse, CreateChatResponse, UpdateChatResponse,
    MessageListResponse, SendMessageResponse, UpdateMessageResponse,
    ChatResponse, ChatStats, CourseInfo, MessageResponse as ChatMessageResponse
)


# 创建路由器 (移除prefix，由main.py统一管理)
chat_router = APIRouter(tags=["聊天管理/Chat Management"])
message_router = APIRouter(tags=["消息管理/Message Management"])


# ===== 聊天管理路由 =====

@chat_router.get("/chats", response_model=ChatListResponse)
@handle_service_exceptions
async def get_chats(
    chat_type: Optional[str] = Query(None, description="聊天类型过滤"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的聊天列表"""
    service = ChatService(db)
    chats = service.get_user_chats(current_user.id, chat_type)
    
    # 转换为响应格式
    chat_list = []
    for chat in chats:
        # 获取统计信息
        stats = service.get_chat_stats(chat.id)
        
        # 构造课程信息
        course_info = None
        if chat.course:
            course_info = CourseInfo(
                id=chat.course.id,
                name=chat.course.name,
                code=chat.course.code
            )
        
        # 获取最后一条消息的时间
        last_message_at = None
        if chat.messages:
            last_message_at = max(msg.created_at for msg in chat.messages)
        
        chat_data = ChatResponse(
            id=chat.id,
            title=chat.title,
            chat_type=chat.chat_type,
            course_id=chat.course_id,
            user_id=chat.user_id,
            custom_prompt=chat.custom_prompt,
            ai_model=chat.ai_model,
            search_enabled=chat.search_enabled,
            context_mode=chat.context_mode,
            rag_enabled=chat.rag_enabled,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            last_message_at=last_message_at,
            course=course_info,
            stats=ChatStats(**stats)
        )
        chat_list.append(chat_data)
    
    return ChatListResponse(
        success=True,
        data={
            "chats": chat_list,
            "total": len(chat_list)
        }
    )


@chat_router.post("/chats", response_model=CreateChatResponse)
@handle_service_exceptions
async def create_chat(
    chat_data: CreateChatRequest = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建聊天"""
    service = ChatService(db)
    result = service.create_chat(chat_data, current_user.id)
    
    return CreateChatResponse(
        success=True,
        data=result
    )


@chat_router.put("/chats/{chat_id}", response_model=UpdateChatResponse)
@handle_service_exceptions
async def update_chat(
    chat_id: int = Path(..., description="Chat ID"),
    chat_data: UpdateChatRequest = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新聊天"""
    service = ChatService(db)
    chat = service.update_chat(chat_id, chat_data, current_user.id)
    
    return UpdateChatResponse(
        success=True,
        data={
            "chat": {
                "id": chat.id,
                "title": chat.title,
                "updated_at": chat.updated_at
            }
        }
    )


@chat_router.delete("/chats/{chat_id}", response_model=MessageResponse)
@handle_service_exceptions
async def delete_chat(
    chat_id: int = Path(..., description="Chat ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除聊天"""
    service = ChatService(db)
    service.delete_chat(chat_id, current_user.id)
    
    return MessageResponse(
        success=True,
        data={},
        message="聊天删除成功"
    )


# ===== 消息管理路由 =====

@message_router.get("/chats/{chat_id}/messages", response_model=MessageListResponse)
@handle_service_exceptions
async def get_chat_messages(
    chat_id: int = Path(..., description="Chat ID"),
    limit: int = Query(50, ge=1, le=100, description="消息数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取聊天消息列表"""
    service = MessageService(db)
    messages = service.get_chat_messages(chat_id, current_user.id, limit, offset)
    
    # 转换为响应格式
    message_list = []
    for message in messages:
        message_data = ChatMessageResponse(
            id=message.id,
            chat_id=message.chat_id,
            content=message.content,
            role=message.role,
            model_name=message.model_name,
            tokens_used=message.tokens_used,
            input_tokens=message.input_tokens,
            output_tokens=message.output_tokens,
            cost=message.cost,
            response_time_ms=message.response_time_ms,
            rag_sources=message.rag_sources,
            context_size=message.context_size,
            direct_file_count=message.direct_file_count,
            rag_source_count=message.rag_source_count,
            created_at=message.created_at
        )
        message_list.append(message_data)
    
    return MessageListResponse(
        success=True,
        data={
            "messages": message_list,
            "total": len(message_list)
        }
    )


@message_router.post("/chats/{chat_id}/messages", response_model=SendMessageResponse)
@handle_service_exceptions
async def send_message(
    chat_id: int = Path(..., description="Chat ID"),
    message_data: SendMessageRequest = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发送消息"""
    service = MessageService(db)
    result = service.send_message(chat_id, message_data, current_user.id)
    
    # 转换为响应格式
    user_message = ChatMessageResponse(
        id=result["user_message"]["id"],
        chat_id=chat_id,
        content=result["user_message"]["content"],
        role=result["user_message"]["role"],
        created_at=result["user_message"]["created_at"]
    )
    
    ai_message = ChatMessageResponse(
        id=result["ai_message"]["id"],
        chat_id=chat_id,
        content=result["ai_message"]["content"],
        role=result["ai_message"]["role"],
        created_at=result["ai_message"]["created_at"]
    )
    
    return SendMessageResponse(
        success=True,
        data={
            "user_message": user_message,
            "ai_message": ai_message
        }
    )


@message_router.put("/messages/{message_id}", response_model=UpdateMessageResponse)
@handle_service_exceptions
async def edit_message(
    message_id: int = Path(..., description="Message ID"),
    message_data: EditMessageRequest = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """编辑消息"""
    service = MessageService(db)
    message = service.edit_message(message_id, message_data, current_user.id)
    
    return UpdateMessageResponse(
        success=True,
        data={
            "message": {
                "id": message.id,
                "content": message.content,
                "is_edited": message.is_edited,
                "edited_at": message.edited_at
            }
        }
    )


@message_router.delete("/messages/{message_id}", response_model=MessageResponse)
@handle_service_exceptions
async def delete_message(
    message_id: int = Path(..., description="Message ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除消息"""
    service = MessageService(db)
    service.delete_message(message_id, current_user.id)
    
    return MessageResponse(
        success=True,
        data={},
        message="消息删除成功"
    )


# 合并路由器 (使用统一命名规范)
router = APIRouter()
router.include_router(chat_router)
router.include_router(message_router)

# 保持向后兼容性
chat_management_router = router