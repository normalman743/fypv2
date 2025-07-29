"""AI模块Service层业务逻辑"""
import os
import time
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

# LangChain和OpenAI imports
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from src.shared.exceptions import (
    BaseServiceException, NotFoundServiceException, 
    AccessDeniedServiceException, ValidationServiceException,
    BadRequestServiceException
)
from src.shared.error_codes import ErrorCodes
from src.shared.base_service import BaseService
from src.shared.config import settings
from .models import AIModel, AIConversationConfig
from .schemas import AIRequest, AIResponse, RAGSource


# 移除自定义异常类，统一使用标准Service异常


class AIService(BaseService):
    """AI对话服务"""
    
    METHOD_EXCEPTIONS = {
        "generate_response": {ValidationServiceException, BadRequestServiceException},
        "get_available_models": set(),
        "get_conversation_configs": set(),
        "search_knowledge_base": {ValidationServiceException, AccessDeniedServiceException},
        "vectorize_file": {NotFoundServiceException, AccessDeniedServiceException, ValidationServiceException},
        "vectorize_course_files": {NotFoundServiceException, AccessDeniedServiceException},
        "get_vectorization_status": {NotFoundServiceException, AccessDeniedServiceException},
    }
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.openai_client: Optional[OpenAI] = None
        
        # 初始化OpenAI客户端
        self._initialize_openai_client()
    
    def _initialize_openai_client(self) -> None:
        """初始化OpenAI客户端"""
        if OPENAI_AVAILABLE and settings.openai_api_key and settings.openai_api_key != "sk-test-key":
            try:
                self.openai_client = OpenAI(api_key=settings.openai_api_key)
                # 测试连接
                self.openai_client.models.list()
                print("🚀 OpenAI client initialized successfully")
            except Exception as e:
                print(f"⚠️ OpenAI client initialization failed: {e}")
                self.openai_client = None
    
    async def generate_response_async(self, request: AIRequest, conversation_history: Optional[List[Dict[str, str]]] = None) -> AIResponse:
        """生成AI响应"""
        try:
            start_time = time.time()
            
            # 1. 获取AI模型配置
            ai_model = self._get_ai_model(request.ai_model)
            if not ai_model:
                raise BadRequestServiceException(f"AI模型 {request.ai_model} 不存在或未激活", "MODEL_NOT_FOUND")
            
            # 2. 获取对话配置
            config = self._get_conversation_config(request.context_mode)
            if not config:
                raise BadRequestServiceException(f"对话配置 {request.context_mode} 不存在", "CONFIG_NOT_FOUND")
            
            # 3. RAG检索（如果启用）
            rag_sources = []
            if request.rag_enabled:
                rag_sources = self._retrieve_rag_context(
                    request.message,
                    request.chat_type,
                    request.course_id,
                    config.rag_chunk_limit
                )
            
            # 4. 构建上下文
            context = self._build_context(
                request,
                conversation_history,
                rag_sources,
                config
            )
            
            # 5. 调用AI API
            response_content, tokens_info = await self._call_ai_api_async(
                context,
                ai_model,
                config
            )
            
            # 6. 计算成本和响应时间
            response_time_ms = int((time.time() - start_time) * 1000)
            cost = self._calculate_cost(tokens_info, ai_model)
            
            return AIResponse(
                content=response_content,
                model_name=ai_model.name,
                tokens_used=tokens_info.get("total_tokens"),
                input_tokens=tokens_info.get("prompt_tokens"),
                output_tokens=tokens_info.get("completion_tokens"),
                cost=cost,
                response_time_ms=response_time_ms,
                rag_sources=rag_sources,
                context_size=len(context)
            )
            
        except BadRequestServiceException:
            raise
        except Exception as e:
            raise BadRequestServiceException(f"生成AI响应失败: {str(e)}", "GENERATION_ERROR")
    
    def generate_response(self, request: AIRequest, conversation_history: Optional[List[Dict[str, str]]] = None) -> AIResponse:
        """生成AI响应（同步版本，兼容旧代码）"""
        # 在新的事件循环中运行异步方法
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        
        if loop is None:
            # 没有运行中的事件循环，直接运行
            return asyncio.run(self.generate_response_async(request, conversation_history))
        else:
            # 有运行中的事件循环，在线程池中运行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, 
                    self.generate_response_async(request, conversation_history)
                )
                return future.result()
    
    def get_available_models(self) -> List[AIModel]:
        """获取可用的AI模型列表"""
        try:
            models = self.db.query(AIModel).filter(AIModel.is_active == True).all()
            return models
        except Exception as e:
            raise BadRequestServiceException(f"获取AI模型列表失败: {str(e)}", "DATABASE_ERROR")
    
    def get_conversation_configs(self) -> List[AIConversationConfig]:
        """获取对话配置列表"""
        try:
            configs = self.db.query(AIConversationConfig).filter(
                AIConversationConfig.is_active == True
            ).all()
            return configs
        except Exception as e:
            raise BadRequestServiceException(f"获取对话配置失败: {str(e)}", "DATABASE_ERROR")
    
    def _get_ai_model(self, model_name: str) -> Optional[AIModel]:
        """获取AI模型配置"""
        return self.db.query(AIModel).filter(
            AIModel.name == model_name,
            AIModel.is_active == True
        ).first()
    
    def _get_conversation_config(self, config_name: str) -> Optional[AIConversationConfig]:
        """获取对话配置"""
        return self.db.query(AIConversationConfig).filter(
            AIConversationConfig.name == config_name,
            AIConversationConfig.is_active == True
        ).first()
    
    def _retrieve_rag_context(self, query: str, chat_type: str, course_id: Optional[int], limit: int) -> List[RAGSource]:
        """检索RAG上下文"""
        try:
            # 导入向量化服务
            from src.shared.vectorization import get_vectorization_service
            
            vectorization_service = get_vectorization_service()
            return vectorization_service.retrieve_context(query, chat_type, course_id, limit)
            
        except Exception as e:
            print(f"⚠️ RAG检索失败: {e}")
            return []
    
    def _build_context(self, request: AIRequest, conversation_history: Optional[List[Dict[str, str]]], 
                      rag_sources: List[RAGSource], config: AIConversationConfig) -> List[Dict[str, str]]:
        """构建对话上下文"""
        context = []
        
        # 1. 系统提示词
        system_prompt = self._build_system_prompt(request, rag_sources)
        context.append({"role": "system", "content": system_prompt})
        
        # 2. 对话历史（限制数量）
        if conversation_history:
            # 取最新的N条消息
            recent_history = conversation_history[-config.max_context_messages:]
            context.extend(recent_history)
        
        # 3. 当前用户消息
        context.append({"role": "user", "content": request.message})
        
        return context
    
    def _build_system_prompt(self, request: AIRequest, rag_sources: List[RAGSource]) -> str:
        """构建系统提示词"""
        base_prompt = """你是ICU智能学习助手Star，专门为大学生提供学术支持和校园生活帮助。

请遵循以下原则：
1. 提供准确、有用的信息
2. 保持友好和专业的语调
3. 如果不确定答案，请诚实说明
4. 优先使用提供的文档内容回答问题"""
        
        # 添加自定义提示词
        if request.custom_prompt:
            base_prompt += f"\n\n用户自定义指令：{request.custom_prompt}"
        
        # 添加RAG上下文
        if rag_sources:
            base_prompt += "\n\n以下是相关的文档内容，请优先参考这些信息："
            for i, source in enumerate(rag_sources, 1):
                base_prompt += f"\n\n文档{i}（来源：{source.source_file}）：\n{source.content}"
        
        return base_prompt
    
    async def _call_ai_api_async(self, context: List[Dict[str, str]], ai_model: AIModel, 
                                config: AIConversationConfig) -> Tuple[str, Dict[str, int]]:
        """异步调用AI API"""
        if self.openai_client and ai_model.provider == "openai":
            try:
                # 使用asyncio在线程池中运行同步的OpenAI调用
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.openai_client.chat.completions.create(
                        model=ai_model.model_id,
                        messages=context,
                        max_tokens=ai_model.max_tokens,
                        temperature=float(ai_model.temperature),
                        top_p=float(ai_model.top_p)
                    )
                )
                
                content = response.choices[0].message.content
                tokens_info = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
                
                return content, tokens_info
                
            except Exception as e:
                print(f"⚠️ OpenAI API调用失败: {e}")
                # 降级到Mock响应
                pass
        
        # Mock响应（开发环境或API不可用时）
        return self._generate_mock_response(context, ai_model)
    
    def _generate_mock_response(self, context: List[Dict[str, str]], ai_model: AIModel) -> Tuple[str, Dict[str, int]]:
        """生成Mock响应"""
        user_message = context[-1]["content"] if context else "Hello"
        
        mock_response = f"""这是来自{ai_model.display_name}的模拟响应。

你的问题：{user_message[:100]}...

这是一个占位符回复，用于开发和测试。在生产环境中，这里会是真实的AI响应。

如果你看到这条消息，说明：
1. OpenAI API未配置或不可用
2. 系统正在使用Mock模式进行开发测试

请联系管理员配置正确的AI服务。"""

        tokens_info = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
        
        return mock_response, tokens_info
    
    def _calculate_cost(self, tokens_info: Dict[str, int], ai_model: AIModel) -> Optional[Decimal]:
        """计算API调用成本"""
        try:
            if not ai_model.input_token_cost or not ai_model.output_token_cost:
                return None
            
            input_cost = Decimal(ai_model.input_token_cost) * tokens_info.get("prompt_tokens", 0) / 1000
            output_cost = Decimal(ai_model.output_token_cost) * tokens_info.get("completion_tokens", 0) / 1000
            
            return input_cost + output_cost
            
        except Exception:
            return None