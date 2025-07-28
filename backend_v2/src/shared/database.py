from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from typing import Generator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# 现代化的 Base 类（SQLAlchemy 2.0+ 推荐）
class Base(DeclarativeBase):
    pass

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # 连接池预检查
    pool_recycle=300,    # 连接回收时间（秒）
    echo=settings.debug  # 开发模式下显示 SQL
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def setup_database() -> None:
    """验证数据库连接"""
    try:
        # 只验证连接，表结构由 Alembic 管理
        with engine.connect() as conn:
            logger.info("Database connection successful")
            
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise