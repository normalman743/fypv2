from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Campus LLM System"
    API_V1_STR: str = "/api/v1"

    # Database settings
    MYSQL_SERVER: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DB: str
    DATABASE_URL: Optional[str] = None

    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # File storage settings
    UPLOAD_FOLDER: str = "uploads"

    # ChromaDB settings
    CHROMA_DB_PATH: str = "chroma_db"

    # Admin invite code
    ADMIN_INVITE_CODE: Optional[str] = None

    # LLM settings (example, can be expanded)
    OPENAI_API_KEY: Optional[str] = None
    # Add other LLM related settings as needed

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_SERVER}/{self.MYSQL_DB}"

settings = Settings()
