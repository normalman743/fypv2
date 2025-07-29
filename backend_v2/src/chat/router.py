"""Chat模块API路由"""
from fastapi import APIRouter, Depends, Path, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List

from src.shared.dependencies import DbDep, UserDep
from src.shared.api_decorator import create_service_route_config, service_api_handler
from src.shared.schemas import BaseResponse, MessageResponse
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

@chat_router.get("/chats", **create_service_route_config(
    ChatService, 'get_user_chats', ChatListResponse,
    summary="获取用户聊天列表",
    description="获取当前用户的所有聊天，支持类型过滤",
    operation_id="get_user_chats"
))
@service_api_handler(ChatService, 'get_user_chats')
async def get_chats(
    current_user: UserDep,
    db: DbDep,
    chat_type: Optional[str] = Query(None, description="聊天类型过滤")
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


@chat_router.post("/chats", **create_service_route_config(
    ChatService, 'create_chat', CreateChatResponse,
    success_status=201,
    summary="创建聊天",
    description="创建新的聊天并发送首条消息",
    operation_id="create_chat"
))
@service_api_handler(ChatService, 'create_chat')
async def create_chat(
    chat_data: CreateChatRequest,
    current_user: UserDep,
    db: DbDep
):
    """创建聊天"""
    service = ChatService(db)
    result = service.create_chat(chat_data, current_user.id)
    
    return CreateChatResponse(
        success=True,
        data=result
    )


@chat_router.put("/chats/{chat_id}", **create_service_route_config(
    ChatService, 'update_chat', UpdateChatResponse,
    summary="更新聊天",
    description="更新聊天的标题、AI模型等配置",
    operation_id="update_chat"
))
@service_api_handler(ChatService, 'update_chat')
async def update_chat(
    chat_data: UpdateChatRequest,
    current_user: UserDep,
    db: DbDep,
    chat_id: int = Path(..., description="Chat ID")
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


@chat_router.delete("/chats/{chat_id}", **create_service_route_config(
    ChatService, 'delete_chat', MessageResponse,
    summary="删除聊天",
    description="删除指定的聊天及其所有消息",
    operation_id="delete_chat"
))
@service_api_handler(ChatService, 'delete_chat')
async def delete_chat(
    current_user: UserDep,
    db: DbDep,
    chat_id: int = Path(..., description="Chat ID")
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

@message_router.get("/chats/{chat_id}/messages", **create_service_route_config(
    MessageService, 'get_chat_messages', MessageListResponse,
    summary="获取聊天消息列表",
    description="获取指定聊天的所有消息，支持分页",
    operation_id="get_chat_messages"
))
@service_api_handler(MessageService, 'get_chat_messages')
async def get_chat_messages(
    current_user: UserDep,
    db: DbDep,
    chat_id: int = Path(..., description="Chat ID"),
    limit: int = Query(50, ge=1, le=100, description="消息数量限制"),
    offset: int = Query(0, ge=0, description="偏移量")
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


@message_router.post("/chats/{chat_id}/messages", **create_service_route_config(
    MessageService, 'send_message', SendMessageResponse,
    success_status=201,
    summary="发送消息",
    description="在指定聊天中发送消息并获取AI回复",
    operation_id="send_message"
))
@service_api_handler(MessageService, 'send_message')
async def send_message(
    message_data: SendMessageRequest,
    current_user: UserDep,
    db: DbDep,
    chat_id: int = Path(..., description="Chat ID")
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


@message_router.put("/messages/{message_id}", **create_service_route_config(
    MessageService, 'edit_message', UpdateMessageResponse,
    summary="编辑消息",
    description="编辑用户消息内容（仅限用户消息）",
    operation_id="edit_message"
))
@service_api_handler(MessageService, 'edit_message')
async def edit_message(
    message_data: EditMessageRequest,
    current_user: UserDep,
    db: DbDep,
    message_id: int = Path(..., description="Message ID")
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


@message_router.delete("/messages/{message_id}", **create_service_route_config(
    MessageService, 'delete_message', MessageResponse,
    summary="删除消息",
    description="删除指定的消息",
    operation_id="delete_message"
))
@service_api_handler(MessageService, 'delete_message')
async def delete_message(
    current_user: UserDep,
    db: DbDep,
    message_id: int = Path(..., description="Message ID")
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