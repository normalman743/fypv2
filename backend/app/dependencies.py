import time
import logging
import threading
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, make_transient_to_detached
from sqlalchemy import inspect as sa_inspect
from app.models.database import get_db
from app.models.user import User
from app.core.security import verify_token
from app.core.config import settings
from app.core.exceptions import ForbiddenError, UnauthorizedError, InsufficientPermissionsError

# HTTP Bearer authentication
security = HTTPBearer(auto_error=False)

# ==================== Auth User Cache ====================
# 缓存已认证用户，避免每次请求都查 DB（远程 MySQL RTT ~450ms）
_user_cache: dict = {}  # {user_id: (column_state_dict, timestamp)}
_USER_CACHE_TTL = 30    # 缓存有效期（秒）
_cache_lock = threading.Lock()


def _cache_set(user: User):
    """将用户的列属性存入缓存"""
    state = {}
    for attr in sa_inspect(type(user)).mapper.column_attrs:
        state[attr.key] = getattr(user, attr.key)
    with _cache_lock:
        _user_cache[user.id] = (state, time.time())


def _cache_get(user_id: int) -> dict | None:
    """取缓存，过期返回 None"""
    with _cache_lock:
        entry = _user_cache.get(user_id)
    if entry and time.time() - entry[1] < _USER_CACHE_TTL:
        return entry[0]
    return None


def invalidate_user_cache(user_id: int):
    """写操作（余额变更等）后调用，使缓存失效"""
    with _cache_lock:
        _user_cache.pop(user_id, None)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current user（带 30s TTL 缓存）"""
    t_start = time.perf_counter()
    if credentials is None:
        raise UnauthorizedError("Authentication credentials required")
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise UnauthorizedError("Invalid authentication credentials")
    
    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid authentication credentials")
    user_id = int(user_id)

    # 1) 尝试从缓存读取
    cached_state = _cache_get(user_id)
    if cached_state:
        if not cached_state.get('is_active', False):
            raise UnauthorizedError("User not found or deactivated")
        # 重建 detached User 并 merge 进当前 session（不产生 DB 查询）
        # 使用正常构造函数，确保 SQLAlchemy instrumentation 正确初始化
        user = User(**cached_state)
        make_transient_to_detached(user)
        user = db.merge(user, load=False)
        t_done = time.perf_counter()
        logging.info(f"⏱️ [Auth] Cache hit user_id={user_id}: {(t_done - t_start) * 1000:.1f}ms")
        return user

    # 2) 缓存未命中 → 查 DB
    t_query = time.perf_counter()
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    t_done = time.perf_counter()
    logging.info(f"⏱️ [Auth] Query user: {(t_done - t_query) * 1000:.1f}ms | Total auth: {(t_done - t_start) * 1000:.1f}ms")
    
    if user is None:
        raise UnauthorizedError("User not found or deactivated")
    
    # 存入缓存
    _cache_set(user)
    
    return user


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current admin user"""
    if current_user.role != "admin":
        raise InsufficientPermissionsError("Insufficient permissions")
    return current_user

# Alias for require_admin
require_admin = get_current_admin_user
