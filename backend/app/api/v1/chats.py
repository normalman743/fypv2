import time
import logging
from fastapi import APIRouter, Depends, Path
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json

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
    
    t0 = time.perf_counter()
    chats = service.get_user_chats(current_user.id)
    t1 = time.perf_counter()
    logging.info(f"⏱️ [Chats] Query chats: {(t1 - t0) * 1000:.1f}ms ({len(chats)} rows)")
    
    # 批量查询所有 chat 的 message_count（单条 SQL，避免 N+1）
    t_stats = time.perf_counter()
    chat_ids = [chat.id for chat in chats]
    stats_map = service.get_batch_chat_stats(chat_ids)
    t_stats_done = time.perf_counter()
    logging.info(f"⏱️ [Chats] Batch stats ({len(chats)} chats): {(t_stats_done - t_stats) * 1000:.1f}ms")
    
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
        
        stats = stats_map.get(chat.id, {"message_count": 0})
        
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


@router.post("")
async def create_chat(
    chat_data: CreateChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create chat with first message and AI response"""
    service = ChatService(db)
    
    if chat_data.stream:
        # 流式响应
        async def generate_stream():
            try:
                async for chunk in service.create_chat_with_first_message_stream(chat_data, current_user.id):
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                error_chunk = {"type": "error", "error": str(e)}
                yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    else:
        # 非流式响应
        import logging
        try:
            logging.info(f"[Chat] Creating chat - type: {chat_data.chat_type}, course_id: {chat_data.course_id}, temp_tokens: {len(chat_data.temporary_file_tokens or [])}")
            result = await service.create_chat_with_first_message(chat_data, current_user.id)
            return ChatCreateResponse(
                success=True,
                data=result
            )
        except Exception as e:
            logging.error(f"[Chat] Error creating chat: {type(e).__name__}: {e}")
            raise


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