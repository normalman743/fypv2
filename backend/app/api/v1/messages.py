from fastapi import APIRouter, Depends, Path
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json

from app.dependencies import get_db, get_current_user
from app.services.message_service import MessageService
from app.schemas.message import (
    SendMessageRequest,
    EditMessageRequest,
    MessageListResponse,
    MessageSendResponse,
    MessageUpdateResponse
)
from app.schemas.common import SuccessResponse
from app.models.user import User

router = APIRouter(tags=["messages"])


@router.get("/chats/{chat_id}/messages", response_model=MessageListResponse)
async def get_chat_messages(
    chat_id: int = Path(..., description="Chat ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all messages in a chat"""
    service = MessageService(db)
    messages = service.get_chat_messages(chat_id, current_user.id)
    
    # Convert to response format
    message_list = []
    for message in messages:
        message_data = service.format_message_response(message)
        message_list.append(message_data)
    
    return MessageListResponse(
        success=True,
        data={"messages": message_list}
    )


@router.post("/chats/{chat_id}/messages")
async def send_message(
    chat_id: int = Path(..., description="Chat ID"),
    message_data: SendMessageRequest = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send message and get AI response"""
    service = MessageService(db)
    
    if message_data.stream:
        # 流式响应
        async def generate_stream():
            try:
                async for chunk in service.send_message_stream(chat_id, message_data, current_user.id):
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
        result = await service.send_message(chat_id, message_data, current_user.id)
        return MessageSendResponse(
            success=True,
            data=result
        )


@router.put("/messages/{message_id}", response_model=MessageUpdateResponse)
async def edit_message(
    message_id: int = Path(..., description="Message ID"),
    message_data: EditMessageRequest = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Edit message content"""
    service = MessageService(db)
    message = service.edit_message(message_id, message_data, current_user.id)
    
    return MessageUpdateResponse(
        success=True,
        data={
            "message": {
                "id": message.id,
                "content": message.content,
                "created_at": message.created_at
            }
        }
    )


@router.delete("/messages/{message_id}", response_model=SuccessResponse)
async def delete_message(
    message_id: int = Path(..., description="Message ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete message"""
    service = MessageService(db)
    service.delete_message(message_id, current_user.id)
    
    return SuccessResponse(success=True)