from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from typing import List
import secrets


class Settings(BaseSettings):
    # 应用基本配置
    app_name: str = Field("Campus LLM System v2", env="APP_NAME")
    app_version: str = Field("2.0.0", env="APP_VERSION")
    app_description: str = Field("A modular RAG-based intelligent campus assistant", env="APP_DESCRIPTION")
    debug: bool = Field(False, env="DEBUG")
    environment: str = Field("development", env="ENVIRONMENT")
    
    # 服务器配置
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8001, env="PORT")  # 使用 8001 避免与 v1 冲突
    workers: int = Field(4, env="WORKERS")
    
    # CORS 配置
    cors_origins: str = Field("http://localhost:3000,http://localhost:3001", env="CORS_ORIGINS")
    
    # 数据库配置
    database_url: str = Field("mysql+pymysql://root:password@localhost:3306/campus_llm", env="DATABASE_URL")
    
    # JWT 配置
    secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        env="SECRET_KEY",
        min_length=32,
        description="JWT密钥，生产环境必须设置"
    )
    algorithm: str = Field("HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(1440, env="ACCESS_TOKEN_EXPIRE_MINUTES")  # 24小时
    
    # Auth 安全配置
    enable_registration: bool = Field(True, env="ENABLE_REGISTRATION")
    enable_email_verification: bool = Field(True, env="ENABLE_EMAIL_VERIFICATION")
    max_login_attempts: int = Field(5, env="MAX_LOGIN_ATTEMPTS")
    account_lock_duration_hours: int = Field(1, env="ACCOUNT_LOCK_DURATION_HOURS")
    
    # 邮箱配置
    allowed_email_domains: str = Field(
        "example.com,test.com",
        env="ALLOWED_EMAIL_DOMAINS"
    )
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f"环境必须是 {allowed} 之一")
        return v
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        # 获取 environment 字段值
        environment = info.data.get('environment') if info.data else 'development'
        if environment == 'production' and v == "your-secret-key-change-in-production":
            raise ValueError("生产环境必须设置安全的 SECRET_KEY")
        return v
    
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith(('mysql+pymysql://', 'postgresql://', 'sqlite:///')):
            raise ValueError("不支持的数据库URL格式")
        return v
    
    @property
    def cors_origins_list(self) -> List[str]:
        """安全的 CORS 配置"""
        if self.environment == "production" and "*" in self.cors_origins:
            raise ValueError("生产环境不能使用 CORS_ORIGINS='*'")
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def allowed_email_domains_list(self) -> List[str]:
        """获取允许的邮箱域名列表"""
        if not self.allowed_email_domains:
            return []
        return [domain.strip() for domain in self.allowed_email_domains.split(",") if domain.strip()]
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


# 全局配置实例
settings = Settings()