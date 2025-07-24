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
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./local_campus_llm.db")
    test_database_url: Optional[str] = os.getenv("TEST_DATABASE_URL")
    
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
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001")
    cors_allow_credentials: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    
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
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    @property
    def cors_origins_for_credentials(self) -> List[str]:
        """
        获取用于带凭据请求的CORS源列表
        当启用credentials时，不能使用通配符"*"，必须指定具体的源
        """
        if self.cors_origins == "*":
            # 如果设置为通配符，返回常用的开发环境源
            return [
                "http://localhost:3000",
                "http://localhost:3001", 
                "http://localhost:5173",  # Vite 默认端口
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001",
                "http://127.0.0.1:5173"
            ]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    class Config:
        env_file = ".env"

settings = Settings()
