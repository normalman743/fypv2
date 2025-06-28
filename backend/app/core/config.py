from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # 应用配置
    app_name: str = "校园LLM系统"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # 数据库配置
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    test_database_url: str = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")
    
    # JWT配置
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24小时
    
    # 邀请码配置
    default_invite_code: str = "INVITE2025"
    
    # Redis和Celery配置
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    # 服务器配置
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))
    workers: int = int(os.getenv("WORKERS", "1"))
    
    # CORS配置
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    
    # 文件上传配置
    upload_dir: str = os.getenv("UPLOAD_DIR", "./storage/uploads")
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", str(50 * 1024 * 1024)))  # 50MB
    allowed_extensions: str = os.getenv("ALLOWED_EXTENSIONS", "pdf,doc,docx,txt,md")
    
    # AI 和 RAG 配置
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    chroma_data_dir: str = os.getenv("CHROMA_DATA_DIR", "./data/chroma")
    rag_chunk_size: int = int(os.getenv("RAG_CHUNK_SIZE", "1000"))
    rag_chunk_overlap: int = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))
    
    # 日志配置
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "./logs/app.log")
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """将逗号分隔的字符串转换为列表"""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """将逗号分隔的CORS源转换为列表"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"

settings = Settings()
