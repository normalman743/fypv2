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
    
    # 数据库配置 - 默认使用SQLite
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    test_database_url: str = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")
    
    # JWT配置
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24小时
    
    # 邀请码配置
    default_invite_code: str = "INVITE2025"
    
    # 文件上传配置
    upload_dir: str = os.getenv("UPLOAD_DIR", "./storage/uploads")
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions_str: str = os.getenv("ALLOWED_EXTENSIONS", "pdf,doc,docx,txt,md")
    
    # AI 和 RAG 配置
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"
    
    @property
    def allowed_extensions(self) -> List[str]:
        """将逗号分隔的字符串转换为列表"""
        return [ext.strip() for ext in self.allowed_extensions_str.split(",")]
    
    class Config:
        env_file = ".env"

settings = Settings()
