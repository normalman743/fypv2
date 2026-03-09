"""
Production AI Service - Pure RAG + OpenAI Implementation
只使用真实的RAG和OpenAI API，不包含Mock逻辑
"""

import os
import random
from typing import Dict, List, Any, Optional, AsyncGenerator
from openai import AsyncOpenAI
from app.services.ai_service import AIResponse

# Import RAG service
try:
    from app.services.rag_service import get_rag_service, ProductionRAGService
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

# Import OpenAI
try:
    from openai import AsyncOpenAI
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
        
        # 初始化OpenAI客户端（异步）
        try:
            self.openai_client = AsyncOpenAI(api_key=api_key)
            print("🚀 AsyncOpenAI Client initialized")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenAI client: {e}")
        
        print("✅ Production AI Service ready")
    
    async def generate_response(self, message: str, chat_type: str = "general", course_id: int = None, 
                         file_context: str = "", ai_model: str = "Star", search_enabled: bool = False,
                         conversation_history: list = None, stream: bool = False, images: list = None, 
                         custom_prompt: str = None) -> AIResponse:
        """使用真实RAG和OpenAI生成响应"""
        
        # 获取实际的OpenAI模型名称
        from app.core.model_config import get_openai_model, get_model_config
        try:
            openai_model = get_openai_model(ai_model, search_enabled)
            model_config = get_model_config(ai_model)
            print(f"🤖 Using model: {ai_model} -> {openai_model} (search: {search_enabled})")
        except ValueError as e:
            raise RuntimeError(f"Invalid model configuration: {e}")
        
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
        system_prompt = self._build_system_prompt(chat_type, context_text, file_context, custom_prompt)
        
        # 3. 构建完整的消息列表
        messages = [{"role": "system", "content": system_prompt}]
        
        # 调试：打印系统提示词
        print(f"🔧 DEBUG - System Prompt:")
        print(f"   Length: {len(system_prompt)} characters")
        print(f"   Full Content:\n{system_prompt}")
        print(f"   ==================== END SYSTEM PROMPT ====================")
        if custom_prompt:
            print(f"   Custom Prompt: {custom_prompt}")
        if file_context.strip():
            print(f"   File Context ({len(file_context)} chars):\n{file_context}")
            print(f"   ==================== END FILE CONTEXT ====================")
        
        # 添加历史对话
        if conversation_history:
            messages.extend(conversation_history)
            print(f"💬 Added {len(conversation_history)} history messages")
            for i, msg in enumerate(conversation_history[-3:]):  # 显示最后3条历史消息
                content = msg['content']
                # 检查是否是包含图片的消息
                if isinstance(content, list):
                    # 提取文本部分
                    text_parts = [item['text'] for item in content if item.get('type') == 'text']
                    text_content = ' '.join(text_parts) if text_parts else '(包含图片)'
                    image_count = len([item for item in content if item.get('type') == 'image_url'])
                    if image_count > 0:
                        print(f"   History {i}: {msg['role']}: {text_content[:500]}... [含{image_count}张图片]")
                    else:
                        print(f"   History {i}: {msg['role']}: {text_content[:500]}...")
                else:
                    # 普通文本消息，可以选择显示完整内容或截断
                    if len(content) <= 500:  # 短消息显示完整内容
                        print(f"   History {i}: {msg['role']}: {content}")
                    else:  # 长消息截断显示
                        print(f"   History {i}: {msg['role']}: {content[:500]}...")
        
        # 添加当前用户消息
        if images:
            # 如果有图片，构建包含图片的消息格式
            content = [{"type": "text", "text": message}]
            content.extend(images)
            messages.append({"role": "user", "content": content})
            print(f"🖼️ Added {len(images)} images to user message")
        else:
            # 没有图片，使用普通文本格式
            messages.append({"role": "user", "content": message})
        
        print(f"📝 Current User Message: {message}")
        print(f"📊 Total Messages to AI: {len(messages)} (1 system + {len(conversation_history or [])} history + 1 current)")
        
        # 调用OpenAI API (异步)
        try:
            # 为搜索预览模型准备特殊参数
            api_params = {
                "model": openai_model,
                "messages": messages,
                "max_tokens": model_config["max_tokens"]
            }
            
            # 搜索预览模型有特殊限制
            if "search-preview" in openai_model:
                # 搜索预览模型不支持 temperature 参数
                api_params["response_format"] = {"type": "text"}
                print(f"🔍 Using search preview model (no temperature)")
            else:
                # 非搜索模型可以使用 temperature
                api_params["temperature"] = 0.7
            
            if stream:
                # 流式响应
                api_params.update({
                    "stream": True,
                    "stream_options": {
                        "include_usage": True
                    }
                })
                response = await self.openai_client.chat.completions.create(**api_params)
                
                # 返回async generator用于流式响应
                return self._handle_stream_response(response, model_config, rag_sources)
            else:
                # 非流式响应
                response = await self.openai_client.chat.completions.create(**api_params)
                
                content = response.choices[0].message.content
                
                # 获取详细的token使用情况
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                total_tokens = response.usage.total_tokens
                
                # 按input/output分别计算成本
                input_cost = (input_tokens / 1_000_000) * model_config["input_cost_per_million"]
                output_cost = (output_tokens / 1_000_000) * model_config["output_cost_per_million"]
                total_cost = input_cost + output_cost
                
                return AIResponse(
                    content=content,
                    tokens_used=total_tokens,
                    cost=total_cost,
                    rag_sources=rag_sources,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens
                )
            
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {e}")
    
    async def _handle_stream_response(self, response, model_config, rag_sources):
        """处理流式响应（异步生成器）"""
        content = ""
        input_tokens = 0
        output_tokens = 0
        
        async for chunk in response:
            print(f"🔍 Received chunk: {chunk}")  # 调试信息
            if hasattr(chunk, 'choices') and chunk.choices and chunk.choices[0].delta.content:
                # 流式内容
                content_delta = chunk.choices[0].delta.content
                content += content_delta
                yield {
                    "type": "content",
                    "content": content_delta
                }
            elif hasattr(chunk, 'usage') and chunk.usage:
                # 最终的usage信息（如果有的话）
                input_tokens = chunk.usage.prompt_tokens
                output_tokens = chunk.usage.completion_tokens
                total_tokens = chunk.usage.total_tokens
                
                # 计算成本
                input_cost = (input_tokens / 1_000_000) * model_config["input_cost_per_million"]
                output_cost = (output_tokens / 1_000_000) * model_config["output_cost_per_million"]
                total_cost = input_cost + output_cost
                
                # 发送最终的usage信息
                yield {
                    "type": "usage",
                    "content": content,
                    "tokens_used": total_tokens,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": total_cost,
                    "rag_sources": rag_sources
                }
        
        # 添加调试信息：打印接收到的所有chunk信息
        print(f"🔍 Stream completed. Content length: {len(content)}, Input tokens: {input_tokens}, Output tokens: {output_tokens}")
        
        # 如果没有收到usage信息，发送一个没有usage的完成信号
        if input_tokens == 0 and output_tokens == 0:
            print("⚠️ No usage information received from OpenAI stream")
            yield {
                "type": "usage",
                "content": content,
                "tokens_used": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": 0.0,
                "rag_sources": rag_sources
            }
    
    async def generate_chat_title(self, first_message: str) -> str:
        """根据用户的第一条消息生成聊天标题"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
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
    
    def _build_system_prompt(self, chat_type: str, context_text: str, file_context: str = "", custom_prompt: str = None) -> str:
        """构建系统提示"""
        
        base_prompt = """你是香港中文大学(CUHK)的AI助手。你的使命是帮助学生更好地学习和生活，提供准确、友好和专业的回答。

你有两种信息源：
1. 知识库检索结果（RAG）- 来自课程资料和校园信息
2. 用户指定的参考文档 - 学生当前关注的具体文件

请综合这两种信息源，以友好、专业的方式回答学生问题。

回答原则：
- 如果用户指定文档中有相关信息，请优先使用
- 结合知识库信息提供更全面的答案
- 保持学术严谨性，引用具体来源
- 用简洁明了的中文回答（除非用户要求其他语言）
- 当引用知识库信息时，请在相关内容后标注数据贡献者，格式如：(数据提供：contributor_name)
- 如果用户询问之前上传的文档，而该文档已过期无法访问，请明确告知文档已过期，但你仍可以基于之前的对话历史来回答相关问题

你的目标是成为学生学习路上的可靠伙伴。"""
        
        if chat_type == "course":
            base_prompt += "\n\n你正在协助学生学习课程内容。请专注于教学和学习相关的问题。"
        elif chat_type == "general":
            base_prompt += "\n\n你正在帮助学生了解校园生活、设施和服务。"
        
        # 添加用户指定的文档上下文
        if file_context.strip():
            base_prompt += f"\n\n用户指定的参考文档：\n{file_context}"
        
        # 添加RAG检索的上下文
        if context_text.strip():
            base_prompt += f"\n\n知识库检索结果：\n{context_text}"
        
        # 添加用户自定义提示词
        if custom_prompt and custom_prompt.strip():
            base_prompt += f"\n\n用户自定义指令：\n{custom_prompt}"
        
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


_ai_service_instance: ProductionAIService = None

def get_ai_service() -> ProductionAIService:
    """获取全局单例AI服务，避免重复初始化RAG/OpenAI客户端"""
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = ProductionAIService()
    return _ai_service_instance