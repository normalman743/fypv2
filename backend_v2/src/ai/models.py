"""AI模块数据模型"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, func
from src.shared.database import Base


class AIModel(Base):
    """AI模型配置"""
    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True)  # Star, StarPlus, StarCode
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    provider = Column(String(50), nullable=False)  # openai, anthropic, etc.
    model_id = Column(String(100), nullable=False)  # gpt-4, claude-3, etc.
    
    # 模型配置
    max_tokens = Column(Integer, default=4096)
    temperature = Column(String(10), default="0.7")
    top_p = Column(String(10), default="1.0")
    
    # 费用配置
    input_token_cost = Column(String(20), nullable=True)  # 每1K输入token成本
    output_token_cost = Column(String(20), nullable=True)  # 每1K输出token成本
    
    # 状态管理
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # 功能支持
    supports_function_calling = Column(Boolean, default=False)
    supports_vision = Column(Boolean, default=False)
    supports_code_execution = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AIConversationConfig(Base):
    """AI对话配置"""
    __tablename__ = "ai_conversation_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True)  # Economy, Standard, Premium, Max
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # 上下文配置
    max_context_messages = Column(Integer, default=10)  # 最大上下文消息数
    max_context_tokens = Column(Integer, default=4000)  # 最大上下文token数
    
    # RAG配置
    rag_chunk_limit = Column(Integer, default=5)  # RAG检索片段数量
    rag_similarity_threshold = Column(String(10), default="0.7")  # 相似度阈值
    
    # 文件处理配置
    max_file_attachments = Column(Integer, default=3)  # 最大附件数
    max_file_size_mb = Column(Integer, default=10)  # 最大文件大小(MB)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())