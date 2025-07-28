from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import Optional, Annotated, Dict, Any, TYPE_CHECKING
import logging

from .database import get_db
from .config import settings
from .exceptions import UnauthorizedError, ForbiddenError

# 避免循环导入，使用 TYPE_CHECKING
if TYPE_CHECKING:
    from src.auth.models import User

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
            raise UnauthorizedError("无效的认证令牌")
        return user_id
    except JWTError:
        raise UnauthorizedError("无效的认证令牌")


def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
) -> "User":
    """
    获取当前用户对象
    """
    from src.auth.models import User
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise UnauthorizedError("用户不存在")
    return user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional["User"]:
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
    except (UnauthorizedError, Exception):
        return None


def require_admin(
    current_user: "User" = Depends(get_current_user)
) -> "User":
    """
    要求管理员权限
    """
    if current_user.role != "admin":
        raise ForbiddenError("需要管理员权限")
    return current_user


# 现代化的类型注解依赖（FastAPI 2024 推荐）
UserDep = Annotated["User", Depends(get_current_user)]
OptionalUserDep = Annotated[Optional["User"], Depends(get_optional_current_user)]
AdminUserDep = Annotated["User", Depends(require_admin)]
DbDep = Annotated[Session, Depends(get_db)]