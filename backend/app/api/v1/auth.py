from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.user import User
from app.models.invite_code import InviteCode
from app.schemas.user import UserRegister, UserLogin, UserResponse, UserUpdate
from app.schemas.common import SuccessResponse, ErrorResponse
from app.core.security import get_password_hash, verify_password, create_access_token, get_current_user, security
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/register", response_model=SuccessResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                error={"code": "USERNAME_EXISTS", "message": "用户名已存在"}
            ).model_dump()
        )
    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                error={"code": "EMAIL_EXISTS", "message": "邮箱已存在"}
            ).model_dump()
        )
    # 检查邀请码
    invite_code = db.query(InviteCode).filter(
        InviteCode.code == user_data.invite_code,
        InviteCode.is_used == False,
        InviteCode.expires_at > datetime.now()
    ).first()
    if not invite_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                error={"code": "INVALID_INVITE_CODE", "message": "邀请码无效或已过期"}
            ).model_dump()
        )
    # 创建用户
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        role="user"
    )
    db.add(user)
    # 标记邀请码为已使用
    invite_code.is_used = True
    db.commit()
    db.refresh(user)
    return SuccessResponse(
        success=True,
        data={"user": UserResponse.model_validate(user)}
    )

@router.post("/login", response_model=SuccessResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.username == user_data.username).first()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                error={"code": "INVALID_CREDENTIALS", "message": "用户名或密码错误"}
            ).model_dump()
        )
    
    # 生成访问令牌
    access_token = create_access_token(data={"sub": user.id})
    
    return SuccessResponse(
        success=True,
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse.model_validate(user)
        }
    )

@router.get("/me", response_model=SuccessResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return SuccessResponse(
        success=True,
        data=UserResponse.model_validate(current_user)
    )

@router.put("/me", response_model=SuccessResponse)
async def update_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    # 检查用户名是否已被其他用户使用
    if user_data.username and user_data.username != current_user.username:
        existing_user = db.query(User).filter(User.username == user_data.username, User.id != current_user.id).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error={"code": "USERNAME_EXISTS", "message": "用户名已存在"}
                ).model_dump()
            )
    # 更新用户信息
    if user_data.username:
        current_user.username = user_data.username
    if user_data.email:
        current_user.email = user_data.email
    if user_data.preferred_language:
        current_user.preferred_language = user_data.preferred_language
    if user_data.preferred_theme:
        current_user.preferred_theme = user_data.preferred_theme
    db.commit()
    db.refresh(current_user)
    return SuccessResponse(
        success=True,
        data=UserResponse.model_validate(current_user)
    )

@router.post("/logout", response_model=SuccessResponse)
async def logout(current_user: User = Depends(get_current_user)):
    """用户登出"""
    return SuccessResponse(
        success=True,
        data={"message": "已成功登出"}
    )
