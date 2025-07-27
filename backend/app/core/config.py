from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # 应用配置
    app_name: str = Field(..., env="APP_NAME",description="Application name")
    app_version: str = Field(..., env="APP_VERSION",description="Application version")
    debug: bool = Field(..., env="DEBUG",description="Debug mode")
    environment: str = Field(..., env="ENVIRONMENT",description="Application environment")

    # 数据库配置
    database_url: str = Field(..., env="DATABASE_URL",description="Database connection URL")
    test_database_url: Optional[str] = Field(None, env="TEST_DATABASE_URL",description="Test database connection URL")

    # JWT配置
    secret_key: str = Field(..., env="SECRET_KEY",description="JWT secret key")
    algorithm: str = Field(..., env="ALGORITHM",description="JWT algorithm")
    access_token_expire_minutes: int = Field(..., env="ACCESS_TOKEN_EXPIRE_MINUTES",description="Access token expire minutes")

    # Redis和Celery配置
    redis_url: str = Field(..., env="REDIS_URL",description="Redis connection URL")
    celery_broker_url: str = Field(..., env="CELERY_BROKER_URL",description="Celery broker URL")
    celery_result_backend: str = Field(..., env="CELERY_RESULT_BACKEND",description="Celery result backend URL")

    # 服务器配置
    host: str = Field(..., env="HOST",description="Server host")
    port: int = Field(..., env="PORT",description="Server port")
    workers: int = Field(..., env="WORKERS",description="Number of workers")

    # CORS配置
    cors_origins: str = Field(..., env="CORS_ORIGINS",description="CORS origins")
    
    # 文件上传配置
    upload_dir: str = Field(..., env="UPLOAD_DIR",description="File upload directory")
    max_file_size: int = Field(..., env="MAX_FILE_SIZE",description="Max file size (bytes)")

    # 临时文件配置
    temporary_file_expiry_hours: int = Field(..., env="TEMPORARY_FILE_EXPIRY_HOURS",description="Temporary file expiry hours")

    # AI 和 RAG 配置
    openai_api_key: str = Field(..., env="OPENAI_API_KEY",description="OpenAI API key")
    chroma_data_dir: str = Field(..., env="CHROMA_DATA_DIR",description="Chroma data directory")
    rag_chunk_size: int = Field(..., env="RAG_CHUNK_SIZE",description="RAG chunk size")
    rag_chunk_overlap: int = Field(..., env="RAG_CHUNK_OVERLAP",description="RAG chunk overlap")

    # 日志配置
    log_level: str = Field(..., env="LOG_LEVEL",description="Log level")
    log_file: str = Field(..., env="LOG_FILE",description="Log file")
    
    # 注册配置
    registration_enabled: bool = Field(..., env="REGISTRATION_ENABLED",description="Enable registration")
    registration_email_verification: bool = Field(..., env="REGISTRATION_EMAIL_VERIFICATION",description="Enable email verification for registration")
    registration_invite_code_verification: bool = Field(..., env="REGISTRATION_INVITE_CODE_VERIFICATION",description="Enable invite code verification for registration")
    
    # 邮件配置
    resend_api_key: str = Field(..., env="RESEND_API_KEY",description="Resend API key")
    email_from_address: str = Field(..., env="EMAIL_ADDRESS",description="Email from address")
    email_verification_enabled: bool = Field(..., env="EMAIL_VERIFICATION_ENABLED",description="Enable email verification")
    email_domain_restriction: str = Field(..., env="EMAIL_DOMAIN_RESTRICTION",description="Email domain restriction")


    @property
    def cors_origins_list(self) -> List[str]:
        """将逗号分隔的CORS源转换为列表"""
        if self.cors_origins == "*":
            raise ValueError("CORS origins cannot be '*' in production mode")
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def allowed_email_domains_list(self) -> List[str]:
        """将逗号分隔的允许邮箱域名转换为列表"""
        if not self.email_domain_restriction:
            return []
        return [domain.strip() for domain in self.email_domain_restriction.split(",")]
    
    def _require_env(self, var_name: str):
        raise ValueError(f"Environment variable {var_name} is required in {self.environment} mode")


    class Config:
        env_file = ".env"
        extra = "ignore"  # 忽略额外的环境变量

settings = Settings()
