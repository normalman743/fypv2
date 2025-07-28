"""Admin模块依赖注入"""
from typing import Annotated
from fastapi import Depends

from src.shared.dependencies import get_current_user
from src.shared.exceptions import ForbiddenError
from src.shared.types import UserProtocol


def get_admin_user(current_user: UserProtocol = Depends(get_current_user)) -> UserProtocol:
    """获取管理员用户，验证管理员权限
    
    Args:
        current_user: 当前登录用户
        
    Returns:
        UserProtocol: 管理员用户对象
        
    Raises:
        ForbiddenError: 当用户不是管理员时抛出
    """
    if current_user.role != "admin":
        raise ForbiddenError("需要管理员权限", error_code="ADMIN_REQUIRED")
    return current_user


# 类型别名，用于路由参数注解
AdminDep = Annotated[UserProtocol, Depends(get_admin_user)]