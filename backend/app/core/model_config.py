"""
AI Model Configuration
定义AI模型映射关系和验证规则
"""

from typing import Dict, Any, Optional
from enum import Enum

class AIModel(str, Enum):
    """支持的AI模型枚举"""
    STAR = "Star"
    STAR_PLUS = "StarPlus"  
    STAR_CODE = "StarCode"

# 模型到OpenAI模型的映射
MODEL_MAPPING = {
    AIModel.STAR: {
        "base": "gpt-4o-mini",
        "search": "gpt-4o-mini-search-preview",
        "supports_search": True,
        "input_cost_per_million": 0.15,  # $0.15 per 1M input tokens
        "output_cost_per_million": 0.60,  # $0.60 per 1M output tokens
        "max_tokens": 1000
    },
    AIModel.STAR_PLUS: {
        "base": "gpt-4o", 
        "search": "gpt-4o-search-preview",
        "supports_search": True,
        "input_cost_per_million": 2.50,  # $2.50 per 1M input tokens
        "output_cost_per_million": 10.00,  # $10.00 per 1M output tokens
        "max_tokens": 2000
    },
    AIModel.STAR_CODE: {
        "base": "gpt-4.1",  # 代码专用模型
        "search": None,  # 不支持搜索
        "supports_search": False,
        "input_cost_per_million": 2.00,  # $2.00 per 1M input tokens
        "output_cost_per_million": 8.00,  # $8.00 per 1M output tokens
        "max_tokens": 4000
    }
}

def get_openai_model(ai_model: str, search_enabled: bool = False) -> str:
    """
    获取实际的OpenAI模型名称
    
    Args:
        ai_model: 自定义模型名称 (Star/StarPlus/StarCode)
        search_enabled: 是否启用搜索功能
        
    Returns:
        OpenAI模型名称
        
    Raises:
        ValueError: 如果模型不支持搜索但请求了搜索功能
    """
    if ai_model not in MODEL_MAPPING:
        raise ValueError(f"Unsupported AI model: {ai_model}")
    
    model_config = MODEL_MAPPING[ai_model]
    
    if search_enabled:
        if not model_config["supports_search"]:
            raise ValueError(f"Model {ai_model} does not support search functionality")
        return model_config["search"]
    else:
        return model_config["base"]

def validate_model_search_combination(ai_model: str, search_enabled: bool) -> bool:
    """
    验证模型和搜索功能的组合是否有效
    
    Args:
        ai_model: 自定义模型名称
        search_enabled: 是否启用搜索
        
    Returns:
        是否有效
    """
    if ai_model not in MODEL_MAPPING:
        return False
    
    if search_enabled and not MODEL_MAPPING[ai_model]["supports_search"]:
        return False
    
    return True

def get_model_config(ai_model: str) -> Dict[str, Any]:
    """
    获取模型的完整配置
    
    Args:
        ai_model: 自定义模型名称
        
    Returns:
        模型配置字典
    """
    if ai_model not in MODEL_MAPPING:
        raise ValueError(f"Unsupported AI model: {ai_model}")
    
    return MODEL_MAPPING[ai_model].copy()