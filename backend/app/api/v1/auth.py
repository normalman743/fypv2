from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.user import User
from app.models.invite_code import InviteCode
from app.schemas.user import UserRegister, UserLogin, UserResponse, UserUpdate, EmailVerificationRequest, ResendVerificationRequest
from app.schemas.common import SuccessResponse, ErrorResponse
from app.core.security import get_password_hash, verify_password, create_access_token, get_current_user, security
from app.core.config import settings
from app.services.email_service import email_service
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/register", response_model=SuccessResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查是否启用注册
    if not settings.registration_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse(
                success=False,
                error={"code": "REGISTRATION_DISABLED", "message": "注册功能已关闭"}
            ).model_dump()
        )
    
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
    
    # 检查邮箱域名限制
    if settings.registration_email_verification and settings.allowed_email_domains_list:

        email_domain = user_data.email.split('@')[-1] if '@' in user_data.email else ""
        email_domain_valid = any(
            email_domain == domain or email_domain.endswith(f".{domain}")
            for domain in settings.allowed_email_domains_list
        )
        if not email_domain_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error={
                        "code": "INVALID_EMAIL_DOMAIN",
                        "message": f"邮箱域名必须是: {', '.join(settings.allowed_email_domains_list)}"
                    }
                ).model_dump()
            )
    
    # 检查邀请码（如果启用）
    print(f"User invite code: {user_data.invite_code}")
    print(f"Invite code list: {settings.registration_invite_code_verification}")
    invite_code_obj = None
    if settings.registration_invite_code_verification:
        print(f"Checking invite code: {user_data.invite_code}")
        # 使用行级锁防止多个用户同时使用同一邀请码
        invite_code_obj = db.query(InviteCode).filter(
            InviteCode.code == user_data.invite_code,
            InviteCode.is_used == False,
            InviteCode.expires_at > datetime.now()
        ).with_for_update().first()
        print(f"Invite code query result: {invite_code_obj}")
        if not invite_code_obj:
            print("Invite code is invalid or expired.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error={"code": "INVALID_INVITE_CODE", "message": "邀请码无效或已过期"}
                ).model_dump()
            )
        else:
            print(f"Invite code {user_data.invite_code} is valid and not used.")
            # 立即标记为已使用以防止其他并发请求使用
            invite_code_obj.is_used = True
            invite_code_obj.used_at = datetime.now()
    # 创建用户
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        role="user"
    )
    db.add(user)
    
    # 设置邀请码使用者（如果启用）
    if settings.registration_invite_code_verification and invite_code_obj:
        invite_code_obj.used_by = user.id  # This will be set after user creation
    
    db.commit()
    db.refresh(user)
    
    # 更新邀请码使用者ID
    if settings.registration_invite_code_verification and invite_code_obj:
        invite_code_obj.used_by = user.id
        db.commit()
    db.refresh(user)
    
    # 发送验证邮件（如果启用）
    if settings.registration_email_verification:
        email_sent = email_service.send_verification_email(db, user)
        if not email_sent:
            # 邮件发送失败，但用户已创建，记录日志
            import logging
            logging.warning(f"Failed to send verification email to {user.email}")
    
    return SuccessResponse(
        success=True,
        data={
            "user": UserResponse.model_validate(user),
            "email_verification_required": settings.registration_email_verification
        }
    )

@router.post("/login", response_model=SuccessResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    # 支持用户名或邮箱登录
    user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.username)
    ).first()
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                error={"code": "INVALID_CREDENTIALS", "message": "用户名/邮箱或密码错误"}
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
    
    # 检查邮箱是否已被其他用户使用
    if user_data.email and user_data.email != current_user.email:
        # 如果启用邮箱验证，禁止修改邮箱

        if settings.registration_email_verification:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error={"code": "EMAIL_CHANGE_NOT_ALLOWED", "message": "启用邮箱验证后不允许修改邮箱"}
                ).model_dump()
            )
        
        existing_user = db.query(User).filter(User.email == user_data.email, User.id != current_user.id).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error={"code": "EMAIL_EXISTS", "message": "邮箱已存在"}
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
    if user_data.last_opened_semester_id:
        current_user.last_opened_semester_id = user_data.last_opened_semester_id
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

@router.post("/verify-email", response_model=SuccessResponse)
async def verify_email(
    request: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """验证邮箱"""
    # 验证邮箱和验证码
    user = email_service.verify_code(db, request.email, request.code)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                error={"code": "INVALID_VERIFICATION_CODE", "message": "验证码无效或已过期"}
            ).model_dump()
        )
    
    return SuccessResponse(
        success=True,
        data={
            "message": "邮箱验证成功",
            "user": UserResponse.model_validate(user)
        }
    )

@router.post("/resend-verification", response_model=SuccessResponse)
async def resend_verification(
    request: ResendVerificationRequest,
    db: Session = Depends(get_db)
):
    """重新发送验证码"""
    # 检查是否启用邮箱验证
    if not settings.registration_email_verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                error={"code": "EMAIL_VERIFICATION_DISABLED", "message": "邮箱验证功能未启用"}
            ).model_dump()
        )
    
    # 重新发送验证码
    success = email_service.resend_verification(db, request.email)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                error={"code": "RESEND_FAILED", "message": "重新发送验证码失败，请稍后再试"}
            ).model_dump()
        )
    
    return SuccessResponse(
        success=True,
        data={"message": f"验证码已发送至 {request.email}"}
    )
