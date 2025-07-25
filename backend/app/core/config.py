from pydantic_settings import BaseSettings
from typing import Optional, List
import os
import secrets
import warnings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # 应用配置
    app_name: str = "校园LLM系统"
    app_version: str = "1.9.10"
    debug: bool = False
    environment: str = "development"
    
    # 数据库配置
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./local_campus_llm.db")
    test_database_url: Optional[str] = os.getenv("TEST_DATABASE_URL")
    
    # JWT配置
    # 🔒 SECURITY IMPROVEMENT: Secure secret key management
    secret_key: str = os.getenv("SECRET_KEY", "")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24小时
    
    def __post_init__(self):
        # Validate SECRET_KEY security
        if not self.secret_key:
            # Generate a secure random key for development/testing
            self.secret_key = secrets.token_urlsafe(64)
            warnings.warn(
                "🚨 WARNING: SECRET_KEY not set! Generated temporary key for this session. "
                "For production, set SECRET_KEY environment variable with a secure random key.",
                UserWarning
            )
        elif self.secret_key == "your-secret-key-here-change-in-production":
            raise ValueError(
                "🚨 CRITICAL SECURITY ERROR: Default secret key detected! "
                "You MUST set a secure SECRET_KEY environment variable before running in production. "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
            )
        elif len(self.secret_key) < 32:
            warnings.warn(
                "⚠️  WARNING: SECRET_KEY is too short (< 32 characters). "
                "Use a longer, more secure key for better security.",
                UserWarning
            )
        
        # Validate DEFAULT_INVITE_CODE security
        if not self.default_invite_code:
            # Generate a secure random invite code for this session
            self.default_invite_code = secrets.token_urlsafe(8).upper()
            warnings.warn(
                f"🚨 WARNING: DEFAULT_INVITE_CODE not set! Generated temporary code '{self.default_invite_code}' for this session. "
                "For production, set DEFAULT_INVITE_CODE environment variable with a secure code.",
                UserWarning
            )
        elif self.default_invite_code in ["INVITE2025", "ADMIN2024", "USER2024", "TEST2024"]:
            warnings.warn(
                "⚠️  SECURITY WARNING: Using predictable default invite code. "
                "Consider setting a more secure DEFAULT_INVITE_CODE environment variable.",
                UserWarning
            )
    
    # 邀请码配置  
    # 🔒 SECURITY IMPROVEMENT: Secure default invite code
    default_invite_code: str = os.getenv("DEFAULT_INVITE_CODE", "")
    
    # Redis和Celery配置
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    # 服务器配置
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))
    workers: int = int(os.getenv("WORKERS", "1"))
    
    # CORS配置
    # 🔒 SECURITY IMPROVEMENT: More secure CORS defaults
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080,https://icu.584743.xyz")
    
    # 文件上传配置
    upload_dir: str = os.getenv("UPLOAD_DIR", "./storage/uploads")
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", str(50 * 1024 * 1024)))  # 50MB
    allowed_extensions: str = os.getenv("ALLOWED_EXTENSIONS", "pdf,doc,docx,txt,md")
    
    # 临时文件配置
    temporary_file_expiry_hours: int = int(os.getenv("TEMPORARY_FILE_EXPIRY_HOURS", "5"))  # 默认5小时
    
    # AI 和 RAG 配置
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    chroma_data_dir: str = os.getenv("CHROMA_DATA_DIR", "./data/chroma")
    rag_chunk_size: int = int(os.getenv("RAG_CHUNK_SIZE", "1000"))
    rag_chunk_overlap: int = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))
    
    # 日志配置
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "./logs/app.log")
    
    # 注册配置
    registration_enabled: bool = os.getenv("REGISTRATION_ENABLED", "True").lower() == "true"
    registration_email_verification: bool = os.getenv("REGISTRATION_EMAIL_VERIFICATION", "False").lower() == "true"
    registration_invite_code_verification: bool = os.getenv("REGISTRATION_INVITE_CODE_VERIFICATION", "True").lower() == "true"
    
    # 邮件配置
    resend_api_key: str = os.getenv("RESEND_API_KEY", "")
    email_from_address: str = os.getenv("EMAIL_ADDRESS", "no-reply@icu.584743.xyz")
    email_domain_restriction: str = os.getenv("EMAIL_DOMAIN_RESTRICTION", "")
    verification_code_expire_minutes: int = int(os.getenv("VERIFICATION_CODE_EXPIRE_MINUTES", "5"))
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """将逗号分隔的字符串转换为列表"""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """将逗号分隔的CORS源转换为列表 - 安全版本"""
        if self.cors_origins == "*":
            warnings.warn(
                "⚠️  SECURITY WARNING: CORS is configured to allow ALL origins (*). "
                "This is insecure for production. Set CORS_ORIGINS to specific domains.",
                UserWarning
            )
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def allowed_email_domains_list(self) -> List[str]:
        """将逗号分隔的允许邮箱域名转换为列表"""
        if not self.email_domain_restriction:
            return []
        return [domain.strip() for domain in self.email_domain_restriction.split(",")]
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # 忽略额外的环境变量

settings = Settings()
