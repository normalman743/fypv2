from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 创建数据库引擎
if settings.database_url.startswith("sqlite"):
    # SQLite配置
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
        echo=settings.debug
    )
else:
    # MySQL配置
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,  # 检测失效连接
        pool_recycle=300,    # 5分钟回收连接
        pool_size=20,        # 连接池大小
        max_overflow=10,     # 最大溢出连接数
        pool_timeout=30,     # 等待连接超时（秒）
        echo=settings.debug
    )

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
