from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.schemas.user import (
    UserRegister, UserLogin, UserResponse, UserUpdate, 
    EmailVerificationRequest, ResendVerificationRequest,
    LoginResponse, RegisterResponse, UserProfileResponse, MessageResponse
)
from app.schemas.common import ErrorResponse
from app.core.security import get_current_user
from app.services.auth_service import AuthService
from app.core.exceptions import BadRequestError
from app.models.user import User
from app.core.api_decorator import service_api

router = APIRouter(prefix="/auth", tags=["认证/Authentication"])

@router.post(
    "/register",
    response_model=RegisterResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request - 请求参数错误"},
        403: {"model": ErrorResponse, "description": "Forbidden - 注册功能已关闭"},
        409: {"model": ErrorResponse, "description": "Conflict - 用户名或邮箱已存在"}
    },
    summary="用户注册"
)
@service_api(AuthService, 'register')
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    service = AuthService(db)
    result = service.register(user_data)
    
    return RegisterResponse(
        success=True,
        data={
            "user": UserResponse.model_validate(result["user"]),
            "message": result["message"]
        }
    )

@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - 用户名或密码错误"}
    },
    summary="用户登录"
)
@service_api(AuthService, 'login')
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    service = AuthService(db)
    result = service.login(user_data)
    
    return LoginResponse(
        success=True,
        data={
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "user": UserResponse.model_validate(result["user"])
        }
    )

@router.get(
    "/me",
    response_model=UserProfileResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - 未认证"}
    },
    summary="获取当前用户信息"
)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserProfileResponse(
        success=True,
        data=UserResponse.model_validate(current_user)
    )

@router.put(
    "/me",
    response_model=UserProfileResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request - 请求参数错误"},
        401: {"model": ErrorResponse, "description": "Unauthorized - 未认证"},
        403: {"model": ErrorResponse, "description": "Forbidden - 无权限"},
        409: {"model": ErrorResponse, "description": "Conflict - 用户名或邮箱已存在"}
    },
    summary="更新用户信息"
)
@service_api(AuthService, 'update_user')
async def update_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    service = AuthService(db)
    updated_user = service.update_user(current_user.id, user_data)
    
    return UserProfileResponse(
        success=True,
        data=UserResponse.model_validate(updated_user)
    )

@router.post(
    "/logout",
    response_model=MessageResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - 未认证"}
    },
    summary="用户登出"
)
async def logout(current_user: User = Depends(get_current_user)):
    """用户登出"""
    return MessageResponse(
        success=True,
        data={"message": "已成功登出"}
    )

@router.post(
    "/verify-email",
    response_model=UserProfileResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request - 验证码无效或已过期"}
    },
    summary="验证邮箱"
)
@service_api(AuthService, 'verify_email')
async def verify_email(
    request: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """验证邮箱"""
    service = AuthService(db)
    user = service.verify_email(request.email, request.code)
    
    return UserProfileResponse(
        success=True,
        data={
            "message": "邮箱验证成功",
            "user": UserResponse.model_validate(user)
        }
    )

@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request - 重发失败或功能未启用"}
    },
    summary="重发验证码"
)
@service_api(AuthService, 'resend_verification')
async def resend_verification(
    request: ResendVerificationRequest,
    db: Session = Depends(get_db)
):
    """重新发送验证码"""
    service = AuthService(db)
    success = service.resend_verification(request.email)
    
    if not success:
        raise BadRequestError("重新发送验证码失败，请稍后再试", "RESEND_FAILED")
    
    return MessageResponse(
        success=True,
        data={"message": f"验证码已发送至 {request.email}"}
    )
