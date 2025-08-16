"""
AI Service Response Classes
定义AI服务的响应数据结构
"""

from typing import List, Dict, Any


class AIResponse:
    """AI response with metadata"""
    
    def __init__(self, content: str, tokens_used: int, cost: float, rag_sources: List[Dict[str, Any]] = None, 
                 input_tokens: int = None, output_tokens: int = None, response_time_ms: int = None):
        self.content = content
        self.tokens_used = tokens_used
        self.cost = cost
        self.rag_sources = rag_sources or []
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.response_time_ms = response_time_ms