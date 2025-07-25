"""
Context Mode Configuration
对话上下文模式配置
"""

from typing import Dict, Any
from enum import Enum

class ContextMode(str, Enum):
    """对话上下文模式枚举"""
    ECONOMY = "Economy"
    STANDARD = "Standard"
    PREMIUM = "Premium"
    MAX = "Max"

# 上下文模式配置
CONTEXT_MODES = {
    ContextMode.ECONOMY: {
        "messages": 3,
        "description": "节约模式",
        "description_en": "Economy Mode",
        "cost_multiplier": 1.0
    },
    ContextMode.STANDARD: {
        "messages": 5,
        "description": "一般模式",
        "description_en": "Standard Mode", 
        "cost_multiplier": 1.0
    },
    ContextMode.PREMIUM: {
        "messages": 10,
        "description": "浪费模式",
        "description_en": "Premium Mode",
        "cost_multiplier": 1.0
    },
    ContextMode.MAX: {
        "messages": 20,
        "description": "最大模式",
        "description_en": "Max Mode",
        "cost_multiplier": 1.0
    }
}

def get_context_mode_config(mode: str) -> Dict[str, Any]:
    """
    获取上下文模式配置
    
    Args:
        mode: 模式名称
        
    Returns:
        模式配置字典
        
    Raises:
        ValueError: 如果模式不存在
    """
    if mode not in CONTEXT_MODES:
        raise ValueError(f"Invalid context mode: {mode}. Available modes: {list(CONTEXT_MODES.keys())}")
    
    return CONTEXT_MODES[mode].copy()

def get_context_message_limit(mode: str) -> int:
    """
    获取指定模式的消息数量限制
    
    Args:
        mode: 模式名称
        
    Returns:
        消息数量限制
    """
    config = get_context_mode_config(mode)
    return config["messages"]

def validate_context_mode(mode: str) -> bool:
    """
    验证上下文模式是否有效
    
    Args:
        mode: 模式名称
        
    Returns:
        是否有效
    """
    return mode in CONTEXT_MODES

def get_available_modes() -> Dict[str, str]:
    """
    获取所有可用模式及其描述
    
    Returns:
        模式名称到描述的映射
    """
    return {mode: config["description"] for mode, config in CONTEXT_MODES.items()}