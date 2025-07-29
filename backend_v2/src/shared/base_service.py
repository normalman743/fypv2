"""共享的Service基类"""
from typing import Dict, Set, Type, Optional, List, Any, Awaitable
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from abc import ABC
import asyncio

from .exceptions import BaseServiceException
from .async_utils import AsyncServiceMixin


class BaseService(ABC, AsyncServiceMixin):
    """Service基类，提供通用功能和异常声明"""
    
    # 子类需要声明的异常映射
    METHOD_EXCEPTIONS: Dict[str, Set[Type[BaseServiceException]]] = {}
    
    def __init__(self, db: Session):
        """初始化Service
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def validate_method_exceptions(self) -> None:
        """验证子类是否正确声明了异常映射"""
        if not hasattr(self, 'METHOD_EXCEPTIONS') or not self.METHOD_EXCEPTIONS:
            print(f"⚠️ Warning: {self.__class__.__name__} 没有声明 METHOD_EXCEPTIONS")
    
    def get_method_exceptions(self, method_name: str) -> Set[Type[BaseServiceException]]:
        """获取指定方法可能抛出的异常类型
        
        Args:
            method_name: 方法名
            
        Returns:
            异常类型集合
        """
        return self.METHOD_EXCEPTIONS.get(method_name, set())
    
    def handle_database_error(self, operation: str, error: Exception) -> None:
        """统一的数据库错误处理
        
        Args:
            operation: 操作名称
            error: 原始异常
        """
        self.db.rollback()
        print(f"❌ Database error in {operation}: {error}")
    
    def safe_commit(self, operation: str = "unknown") -> bool:
        """安全的数据库提交
        
        Args:
            operation: 操作名称，用于日志
            
        Returns:
            是否提交成功
        """
        try:
            self.db.commit()
            return True
        except Exception as e:
            self.handle_database_error(operation, e)
            return False
    
    async def safe_commit_async(self, operation: str = "unknown") -> bool:
        """安全的异步数据库提交
        
        Args:
            operation: 操作名称，用于日志
            
        Returns:
            是否提交成功
        """
        if isinstance(self.db, AsyncSession):
            try:
                await self.db.commit()
                return True
            except Exception as e:
                self.handle_database_error(operation, e)
                return False
        else:
            # 如果不是异步session，降级到同步提交
            return self.safe_commit(operation)
    
    def safe_refresh(self, instance, operation: str = "unknown") -> bool:
        """安全的实例刷新
        
        Args:
            instance: 要刷新的实例
            operation: 操作名称
            
        Returns:
            是否刷新成功
        """
        try:
            self.db.refresh(instance)
            return True
        except Exception as e:
            print(f"⚠️ Failed to refresh instance in {operation}: {e}")
            return False


class AIResponseMixin:
    """AI响应处理混入类"""
    
    def _format_ai_response_dict(self, ai_response) -> Dict[str, Any]:
        """将AI响应对象转换为字典格式
        
        Args:
            ai_response: AI响应对象
            
        Returns:
            字典格式的响应
        """
        return {
            "content": ai_response.content,
            "tokens_used": ai_response.tokens_used,
            "input_tokens": ai_response.input_tokens,
            "output_tokens": ai_response.output_tokens,
            "cost": ai_response.cost,
            "response_time_ms": ai_response.response_time_ms,
            "rag_sources": [
                {
                    "source_file": source.source_file,
                    "chunk_id": source.chunk_id,
                    "content": source.content,
                    "score": source.score,
                    "file_id": source.file_id,
                    "course_id": source.course_id
                } 
                for source in (ai_response.rag_sources or [])
            ],
            "context_size": ai_response.context_size
        }
    
    def _generate_fallback_response(self, message: str, reason: str = "AI服务暂时不可用") -> Dict[str, Any]:
        """生成降级回复
        
        Args:
            message: 用户消息
            reason: 降级原因
            
        Returns:
            降级响应字典
        """
        from decimal import Decimal
        
        return {
            "content": f"抱歉，{reason}。您的消息已收到：{message[:50]}...",
            "tokens_used": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost": Decimal("0"),
            "response_time_ms": 0,
            "rag_sources": [],
            "context_size": 0
        }


class ConversationHistoryMixin:
    """对话历史处理混入类"""
    
    def _get_conversation_history(self, chat_id: int, limit: int = 10) -> List[Dict[str, str]]:
        """获取对话历史
        
        Args:
            chat_id: 聊天ID
            limit: 历史消息数量限制
            
        Returns:
            对话历史列表
        """
        try:
            from src.chat.models import Message
            
            messages = self.db.query(Message)\
                .filter(Message.chat_id == chat_id)\
                .order_by(Message.created_at.desc())\
                .limit(limit)\
                .all()
            
            # 按时间正序排列并转换格式
            history = []
            for message in reversed(messages):
                history.append({
                    "role": message.role,
                    "content": message.content
                })
            
            return history
            
        except Exception as e:
            print(f"⚠️ 获取对话历史失败: {e}")
            return []