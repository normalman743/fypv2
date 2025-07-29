from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import Optional, Annotated, Dict, Any
import logging

from .database import get_db
from .config import settings
from .exceptions import UnauthorizedServiceException, AccessDeniedServiceException
from .types import UserProtocol

logger = logging.getLogger(__name__)

# JWT Bearer token scheme
security = HTTPBearer()

# 重新导出数据库依赖
get_db = get_db


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """
    从 JWT token 中提取当前用户 ID
    这个函数会在 auth 模块完成后更新
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise UnauthorizedServiceException("无效的认证令牌", "INVALID_TOKEN")
        return user_id
    except JWTError:
        raise UnauthorizedServiceException("无效的认证令牌", "INVALID_TOKEN")


def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
) -> UserProtocol:
    """
    获取当前用户对象
    """
    from src.auth.models import User
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise UnauthorizedServiceException("用户不存在", "USER_NOT_FOUND")
    return user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[UserProtocol]:
    """
    可选的用户认证（允许匿名访问）
    用于某些公开 API 或需要区分认证/匿名用户的场景
    """
    if credentials is None:
        return None
    
    try:
        user_id = get_current_user_id(credentials)
        from src.auth.models import User
        user = db.query(User).filter(User.id == user_id).first()
        return user  # 如果用户不存在返回None，不抛出异常
    except (UnauthorizedServiceException, Exception):
        return None


def require_admin(
    current_user: UserProtocol = Depends(get_current_user)
) -> UserProtocol:
    """
    要求管理员权限
    """
    if current_user.role != "admin":
        raise AccessDeniedServiceException("需要管理员权限")
    return current_user


# 现代化的类型注解依赖（FastAPI 2024 推荐）
UserDep = Annotated[UserProtocol, Depends(get_current_user)]
OptionalUserDep = Annotated[Optional[UserProtocol], Depends(get_optional_current_user)]
AdminUserDep = Annotated[UserProtocol, Depends(require_admin)]
DbDep = Annotated[Session, Depends(get_db)]