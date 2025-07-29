"""共享的AI服务管理器"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from decimal import Decimal

from src.ai.service import AIService
from src.ai.schemas import AIRequest
from .base_service import AIResponseMixin, ConversationHistoryMixin


class AIManager(AIResponseMixin, ConversationHistoryMixin):
    """AI服务管理器，提供统一的AI交互接口"""
    
    def __init__(self, db: Session):
        """初始化AI管理器
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.ai_service = AIService(db)
    
    def generate_ai_response(
        self, 
        message: str, 
        ai_model: str, 
        rag_enabled: bool,
        context_mode: str, 
        chat_type: str, 
        course_id: Optional[int],
        file_ids: Optional[List[int]] = None, 
        custom_prompt: Optional[str] = None,
        chat_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """生成AI响应的统一接口
        
        Args:
            message: 用户消息
            ai_model: AI模型名称
            rag_enabled: 是否启用RAG
            context_mode: 上下文模式
            chat_type: 聊天类型
            course_id: 课程ID
            file_ids: 文件ID列表
            custom_prompt: 自定义提示词
            chat_id: 聊天ID（用于获取历史）
            
        Returns:
            AI响应字典
        """
        try:
            # 构建AI请求
            ai_request = AIRequest(
                message=message,
                ai_model=ai_model,
                context_mode=context_mode,
                rag_enabled=rag_enabled,
                chat_type=chat_type,
                course_id=course_id,
                file_ids=file_ids,
                custom_prompt=custom_prompt
            )
            
            # 获取对话历史（如果有chat_id）
            conversation_history = None
            if chat_id:
                conversation_history = self._get_conversation_history(chat_id)
            
            # 调用AI服务
            ai_response = self.ai_service.generate_response(ai_request, conversation_history)
            
            # 转换为字典格式
            return self._format_ai_response_dict(ai_response)
            
        except Exception as e:
            # 降级到简单回复
            print(f"⚠️ AI服务调用失败，使用降级回复: {e}")
            return self._generate_fallback_response(message, "AI服务调用失败")
    
    def generate_initial_response(
        self,
        message: str,
        ai_model: str,
        rag_enabled: bool,
        context_mode: str,
        chat_type: str,
        course_id: Optional[int],
        file_ids: Optional[List[int]] = None,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成初始响应（创建聊天时）
        
        Args:
            message: 首条消息
            ai_model: AI模型名称
            rag_enabled: 是否启用RAG
            context_mode: 上下文模式
            chat_type: 聊天类型
            course_id: 课程ID
            file_ids: 文件ID列表
            custom_prompt: 自定义提示词
            
        Returns:
            AI响应字典
        """
        return self.generate_ai_response(
            message=message,
            ai_model=ai_model,
            rag_enabled=rag_enabled,
            context_mode=context_mode,
            chat_type=chat_type,
            course_id=course_id,
            file_ids=file_ids,
            custom_prompt=custom_prompt,
            chat_id=None  # 初始响应没有历史
        )
    
    def generate_followup_response(
        self,
        chat_id: int,
        message: str,
        ai_model: str,
        rag_enabled: bool,
        context_mode: str,
        chat_type: str,
        course_id: Optional[int],
        file_ids: Optional[List[int]] = None,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成后续响应（发送消息时）
        
        Args:
            chat_id: 聊天ID
            message: 用户消息
            ai_model: AI模型名称
            rag_enabled: 是否启用RAG
            context_mode: 上下文模式
            chat_type: 聊天类型
            course_id: 课程ID
            file_ids: 文件ID列表
            custom_prompt: 自定义提示词
            
        Returns:
            AI响应字典
        """
        return self.generate_ai_response(
            message=message,
            ai_model=ai_model,
            rag_enabled=rag_enabled,
            context_mode=context_mode,
            chat_type=chat_type,
            course_id=course_id,
            file_ids=file_ids,
            custom_prompt=custom_prompt,
            chat_id=chat_id  # 包含历史上下文
        )


# 全局AI管理器实例
_ai_manager = None

def get_ai_manager(db: Session) -> AIManager:
    """获取AI管理器实例
    
    Args:
        db: 数据库会话
        
    Returns:
        AI管理器实例
    """
    # 每次都创建新实例，确保数据库会话正确
    return AIManager(db)