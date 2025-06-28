from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.user import User
from app.core.security import verify_token
from app.core.config import settings
from app.core.exceptions import ForbiddenError, UnauthorizedError

# HTTP Bearer authentication
security = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current user"""
    if credentials is None:
        raise UnauthorizedError("Authentication credentials required")
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise UnauthorizedError("Invalid authentication credentials")
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid authentication credentials")
    
    user = db.query(User).filter(User.id == user_id, User.is_active == True, User.is_deleted == False).first()
    if user is None:
        raise UnauthorizedError("User not found or deactivated")
    
    return user

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current admin user"""
    if current_user.role != "admin":
        raise ForbiddenError("Insufficient permissions")
    return current_user

# Alias for require_admin
require_admin = get_current_admin_user
