import logging
import sys
from .config import settings


def setup_logging() -> None:
    """设置应用日志配置"""
    
    # 设置日志级别
    log_level = logging.DEBUG if settings.debug else logging.INFO
    
    # 配置根日志器
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # 如果是生产环境，可以添加文件日志
    if not settings.debug:
        file_handler = logging.FileHandler("app.log", encoding='utf-8')
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logging.getLogger().addHandler(file_handler)
    
    # 减少第三方库的日志级别
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Debug: {settings.debug}")


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器"""
    return logging.getLogger(name)