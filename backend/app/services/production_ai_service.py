"""
Production AI Service - Pure RAG + OpenAI Implementation
只使用真实的RAG和OpenAI API，不包含Mock逻辑
"""

import os
import random
from typing import Dict, List, Any, Optional
from openai import OpenAI
from app.services.ai_service import AIResponse

# Import RAG service
try:
    from app.services.rag_service import get_rag_service, ProductionRAGService
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

# Import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class ProductionAIService:
    """
    Production AI Service - 只使用真实的RAG和OpenAI
    
    要求:
    - 必须配置有效的OpenAI API密钥
    - 必须有可用的RAG服务
    """
    
    def __init__(self):
        """初始化Production AI Service"""
        
        # 检查依赖
        if not RAG_AVAILABLE:
            raise RuntimeError("RAG service not available. Please install required dependencies.")
        
        if not OPENAI_AVAILABLE:
            raise RuntimeError("OpenAI library not available. Please install: pip install openai")
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "sk-test-key":
            raise RuntimeError("Valid OpenAI API key required. Please set OPENAI_API_KEY environment variable.")
        
        # 初始化RAG服务
        try:
            self.rag_service = get_rag_service()
            print("🚀 RAG Service initialized")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize RAG service: {e}")
        
        # 初始化OpenAI客户端
        try:
            self.openai_client = OpenAI(api_key=api_key)
            # 测试连接
            self.openai_client.models.list()
            print("🚀 OpenAI Client initialized")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenAI client: {e}")
        
        print("✅ Production AI Service ready")
    
    def generate_response(self, message: str, chat_type: str = "general", course_id: int = None) -> AIResponse:
        """使用真实RAG和OpenAI生成响应"""
        
        # 1. 使用RAG检索相关文档
        rag_sources = []
        context_text = ""
        
        try:
            if self.rag_service:
                # 根据聊天类型决定检索范围
                if chat_type == "course" and course_id:
                    sources = self.rag_service.retrieve_context(message, chat_type="course", course_id=course_id, limit=5)
                else:
                    sources = self.rag_service.retrieve_context(message, chat_type="general", limit=5)
                
                for source in sources:
                    rag_sources.append({
                        "source_file": source.source_file,
                        "chunk_id": source.chunk_id
                    })
                    context_text += f"{source.content}\n\n"
                
                print(f"📚 Retrieved {len(rag_sources)} RAG sources")
        except Exception as e:
            print(f"⚠️ RAG retrieval failed: {e}")
            # 继续执行，但没有RAG上下文
        
        # 2. 构建系统提示
        system_prompt = self._build_system_prompt(chat_type, context_text)
        
        # 3. 调用OpenAI API
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # 使用更经济的模型
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            # 估算成本（gpt-4o-mini的定价）
            cost = tokens_used * 0.00000015  # $0.15 per 1M tokens
            
            return AIResponse(
                content=content,
                tokens_used=tokens_used,
                cost=cost,
                rag_sources=rag_sources
            )
            
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {e}")
    
    def generate_chat_title(self, first_message: str) -> str:
        """根据用户的第一条消息生成聊天标题"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "根据用户的第一条消息，生成一个简洁的聊天标题。标题应该：1）不超过20个字符 2）简洁明了 3）概括消息主题 4）用中文。只返回标题内容，不要其他解释。"
                    },
                    {
                        "role": "user", 
                        "content": first_message
                    }
                ],
                max_tokens=50,
                temperature=0.3
            )
            
            title = response.choices[0].message.content.strip()
            # 确保标题不超过20个字符
            if len(title) > 20:
                title = title[:20]
            
            return title
            
        except Exception as e:
            print(f"⚠️ Generate chat title failed: {e}")
            # 如果生成失败，返回默认标题
            return "新聊天"
    
    def _build_system_prompt(self, chat_type: str, context_text: str) -> str:
        """构建系统提示"""
        
        base_prompt = """你是一个智能的校园助手，专门为大学生提供帮助。请基于提供的上下文信息回答问题，如果上下文中没有相关信息，请诚实地告知用户。"""
        
        if chat_type == "course":
            base_prompt += "\n\n你正在协助学生学习课程内容。请专注于教学和学习相关的问题。"
        elif chat_type == "general":
            base_prompt += "\n\n你正在帮助学生了解校园生活、设施和服务。"
        
        if context_text.strip():
            base_prompt += f"\n\n相关上下文信息：\n{context_text}"
        
        base_prompt += "\n\n请用中文回答，语言要友好、准确、有帮助。"
        
        return base_prompt


def create_ai_service() -> ProductionAIService:
    """
    创建AI服务实例 - 只返回Production版本
    
    Returns:
        ProductionAIService实例
        
    Raises:
        RuntimeError: 如果无法初始化Production服务
    """
    return ProductionAIService()