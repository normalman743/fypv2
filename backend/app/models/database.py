import time
import logging
from sqlalchemy import create_engine, text
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
        pool_pre_ping=False,   # 关闭：每次取连接前都会额外一次跟数据库的RTT往返
        pool_recycle=1800,     # 30分钟回收连接（防止MySQL超时断开）
        pool_size=10,          # 预热连接数
        max_overflow=20,       # 高并发时最大剩余
        pool_timeout=30,       # 等待连接超时（秒）
        echo=settings.debug
    )


def warmup_pool():
    """预热连接池：在应用启动时建立初始pool_size个连接，避免第一个请求抑刻"""
    import logging
    conns = []
    try:
        for _ in range(engine.pool.size()):
            conns.append(engine.connect())
        logging.info(f"连接池预热完成，{len(conns)}个连接就绪")
    except Exception as e:
        logging.warning(f"连接池预热失败（不影响服务启动）: {e}")
    finally:
        for conn in conns:
            conn.close()

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

def test_db_latency():
    """测试一次数据库往返延迟 (SELECT 1)"""
    try:
        conn = engine.connect()
        t0 = time.perf_counter()
        conn.execute(text("SELECT 1"))
        rtt = (time.perf_counter() - t0) * 1000
        conn.close()
        logging.info(f"⏱️ [DB] SELECT 1 RTT: {rtt:.1f}ms")
        return rtt
    except Exception as e:
        logging.error(f"⏱️ [DB] Latency test failed: {e}")
        return -1


def get_db():
    """获取数据库会话"""
    t0 = time.perf_counter()
    db = SessionLocal()
    t1 = time.perf_counter()
    logging.info(f"⏱️ [DB] Session created in {(t1 - t0) * 1000:.1f}ms")
    try:
        yield db
    finally:
        t2 = time.perf_counter()
        db.close()
        t3 = time.perf_counter()
        logging.info(f"⏱️ [DB] Session closed in {(t3 - t2) * 1000:.1f}ms")
