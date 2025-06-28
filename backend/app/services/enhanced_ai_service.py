from typing import List, Dict, Any, Optional
import random
import time
import os
from datetime import datetime

# Try to import real RAG service
try:
    from app.services.rag_service import get_rag_service, ProductionRAGService
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Import the existing AIResponse class
from app.services.ai_service import AIResponse, MockAIService


class EnhancedAIService:
    """
    Enhanced AI Service with automatic mock/real switching
    
    Features:
    - Automatic RAG integration when available
    - OpenAI LLM integration with fallback to mock
    - Seamless upgrade path from mock to production
    """
    
    def __init__(self, force_mock: bool = False):
        """
        Initialize Enhanced AI Service
        
        Args:
            force_mock: Force use of mock responses even if real APIs are available
        """
        self.force_mock = force_mock
        
        # Initialize RAG service if available
        self.rag_service = None
        if RAG_AVAILABLE and not force_mock:
            try:
                self.rag_service = get_rag_service()
                print("🚀 Real RAG Service initialized")
            except Exception as e:
                print(f"⚠️ RAG Service initialization failed: {e}")
        
        # Initialize OpenAI client if available
        self.openai_client = None
        if OPENAI_AVAILABLE and not force_mock:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key and api_key != "sk-test-key":
                try:
                    self.openai_client = OpenAI(api_key=api_key)
                    # Test the connection
                    self.openai_client.models.list()
                    print("🚀 OpenAI Client initialized")
                except Exception as e:
                    print(f"⚠️ OpenAI Client initialization failed: {e}")
        
        # Fallback to mock service
        self.mock_service = MockAIService()
        
        # Determine mode
        self.mode = "production" if (self.rag_service or self.openai_client) else "mock"
        print(f"🤖 AI Service running in {self.mode} mode")
    
    def generate_response(self, message: str, chat_type: str = "general", course_id: int = None) -> AIResponse:
        """Generate AI response with automatic RAG integration"""
        
        if self.force_mock or (not self.rag_service and not self.openai_client):
            # Pure mock mode
            return self.mock_service.generate_response(message, chat_type, course_id)
        
        # Production mode with real RAG/LLM
        return self._generate_production_response(message, chat_type, course_id)
    
    def _generate_production_response(self, message: str, chat_type: str, course_id: int) -> AIResponse:
        """Generate response using real RAG and/or LLM"""
        
        start_time = time.time()
        
        # 1. Retrieve context using RAG
        rag_sources = []
        context_text = ""
        
        if self.rag_service:
            try:
                rag_results = self.rag_service.retrieve_context(
                    query=message,
                    chat_type=chat_type,
                    course_id=course_id,
                    limit=5
                )
                
                # Convert to expected format
                for result in rag_results:
                    rag_sources.append({
                        "source_file": result.source_file,
                        "chunk_id": result.chunk_id
                    })
                    context_text += f"\n[来源: {result.source_file}]\n{result.content}\n"
                
                print(f"📚 Retrieved {len(rag_sources)} RAG sources")
                
            except Exception as e:
                print(f"⚠️ RAG retrieval failed: {e}")
                # Fall back to mock RAG sources
                rag_sources = random.sample(self.mock_service.mock_rag_sources, random.randint(1, 3))
        
        # 2. Generate response using LLM
        if self.openai_client:
            try:
                response_content = self._generate_openai_response(message, context_text, chat_type)
                tokens_used = len(response_content) // 4  # Rough estimation
                cost = tokens_used * 0.000002  # Rough cost estimation
                
            except Exception as e:
                print(f"⚠️ OpenAI response generation failed: {e}")
                print("🔄 Falling back to mock response")
                return self.mock_service.generate_response(message, chat_type, course_id)
        else:
            # Use enhanced mock response with real RAG context
            response_content = self._generate_enhanced_mock_response(message, context_text, chat_type)
            tokens_used = len(response_content) // 4
            cost = tokens_used * 0.000002
        
        processing_time = time.time() - start_time
        print(f"⚡ Response generated in {processing_time:.2f}s")
        
        return AIResponse(
            content=response_content,
            tokens_used=tokens_used,
            cost=cost,
            rag_sources=rag_sources
        )
    
    def _generate_openai_response(self, message: str, context: str, chat_type: str) -> str:
        """Generate response using OpenAI LLM"""
        
        # Build prompt with context
        system_prompt = self._build_system_prompt(chat_type)
        user_prompt = self._build_user_prompt(message, context)
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def _generate_enhanced_mock_response(self, message: str, context: str, chat_type: str) -> str:
        """Generate enhanced mock response using real RAG context"""
        
        # Use mock service base response
        base_response = self.mock_service._generate_contextual_content(message, chat_type)
        
        # Enhance with real context if available
        if context:
            enhanced_response = f"基于相关文档资料：\n\n{base_response}"
            if len(context) > 200:
                enhanced_response += f"\n\n参考资料摘要：\n{context[:200]}..."
            else:
                enhanced_response += f"\n\n参考资料：\n{context}"
            return enhanced_response
        
        return base_response
    
    def _build_system_prompt(self, chat_type: str) -> str:
        """Build system prompt based on chat type"""
        
        if chat_type == "course":
            return """你是一个专业的教学助手，专门帮助学生理解课程内容。请基于提供的课程材料和上下文，为学生提供准确、有帮助的回答。回答要：
1. 准确引用相关材料
2. 用清晰易懂的语言解释
3. 提供具体的例子或步骤
4. 鼓励进一步学习"""
        else:
            return """你是一个友好的校园助手，帮助学生解决校园生活和学习中的问题。请基于提供的信息为学生提供有用的回答。回答要：
1. 准确引用相关信息
2. 提供实用的建议
3. 保持友好和支持的语调"""
    
    def _build_user_prompt(self, message: str, context: str) -> str:
        """Build user prompt with context"""
        
        if context:
            return f"""基于以下参考材料回答问题：

参考材料：
{context}

问题：{message}

请基于参考材料提供准确、有帮助的回答。"""
        else:
            return message
    
    def generate_chat_title(self, first_message: str) -> str:
        """Generate chat title - can be enhanced later"""
        return self.mock_service.generate_chat_title(first_message)
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about current service configuration"""
        return {
            "mode": self.mode,
            "rag_available": self.rag_service is not None,
            "openai_available": self.openai_client is not None,
            "forced_mock": self.force_mock,
            "rag_stats": self.rag_service.get_stats() if self.rag_service else None
        }


# Factory function for easy switching
def create_ai_service(use_production: bool = None, force_mock: bool = False) -> EnhancedAIService:
    """
    Create AI service instance
    
    Args:
        use_production: Whether to use production mode (auto-detect if None)
        force_mock: Force mock mode even if production APIs are available
        
    Returns:
        Configured AI service instance
    """
    
    if use_production is None:
        # Auto-detect based on environment
        use_production = (
            RAG_AVAILABLE and 
            OPENAI_AVAILABLE and 
            os.getenv("OPENAI_API_KEY") and
            os.getenv("OPENAI_API_KEY") != "sk-test-key"
        )
    
    return EnhancedAIService(force_mock=(not use_production) or force_mock)