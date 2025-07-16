"""
AI Service Response Classes
定义AI服务的响应数据结构
"""

from typing import List, Dict, Any


class AIResponse:
    """AI response with metadata"""
    
    def __init__(self, content: str, tokens_used: int, cost: float, rag_sources: List[Dict[str, Any]] = None):
        self.content = content
        self.tokens_used = tokens_used
        self.cost = cost
        self.rag_sources = rag_sources or []