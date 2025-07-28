"""Auth模块的FastAPI路由定义"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .schemas import (
    UserRegister, UserLogin, UserUpdate, PasswordChangeRequest,
    ForgotPasswordRequest, ResetPasswordRequest, EmailVerificationRequest,
    ResendVerificationRequest, LoginResponse, RegisterResponse, 
    UserProfileResponse, MessageResponse, UserResponse
)
from .service import AuthService
from .models import User
from src.shared.dependencies import DbDep, UserDep
from src.shared.schemas import ErrorResponse

# 创建路由器
router = APIRouter(prefix="/auth", tags=["认证/Authentication"])


# ===== 现有API接口（保持兼容） =====

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
async def register(user_data: UserRegister, db: DbDep):
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
        401: {"model": ErrorResponse, "description": "Unauthorized - 用户名或密码错误"},
        400: {"model": ErrorResponse, "description": "Bad Request - 账户被锁定"}
    },
    summary="用户登录"
)
async def login(user_data: UserLogin, db: DbDep):
    """用户登录"""
    service = AuthService(db)
    result = service.login(user_data)
    
    return LoginResponse(
        success=True,
        data={
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"],
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
async def get_me(current_user: UserDep):
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
        409: {"model": ErrorResponse, "description": "Conflict - 用户名已存在"}
    },
    summary="更新用户信息"
)
async def update_me(
    user_data: UserUpdate,
    current_user: UserDep,
    db: DbDep
):
    """更新当前用户信息"""
    service = AuthService(db)
    updated_user = service.update_user(current_user["id"], user_data)
    
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
async def logout(current_user: UserDep):
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
async def verify_email(
    request: EmailVerificationRequest,
    db: DbDep
):
    """验证邮箱"""
    service = AuthService(db)
    user = service.verify_email(request.email, request.code)
    
    return UserProfileResponse(
        success=True,
        data=UserResponse.model_validate(user)
    )


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request - 重发失败或功能未启用"}
    },
    summary="重发验证码"
)
async def resend_verification(
    request: ResendVerificationRequest,
    db: DbDep
):
    """重新发送验证码"""
    service = AuthService(db)
    success = service.resend_verification(request.email)
    
    return MessageResponse(
        success=True,
        data={"message": f"验证码已发送至 {request.email}"}
    )


# ===== 新增API接口 =====

@router.put(
    "/change-password",
    response_model=MessageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request - 请求参数错误"},
        401: {"model": ErrorResponse, "description": "Unauthorized - 当前密码错误或未认证"}
    },
    summary="修改密码"
)
async def change_password(
    request: PasswordChangeRequest,
    current_user: UserDep,
    db: DbDep
):
    """修改密码"""
    service = AuthService(db)
    result = service.change_password(current_user["id"], request)
    
    return MessageResponse(
        success=True,
        data=result
    )


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request - 请求过于频繁"}
    },
    summary="忘记密码"
)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: DbDep
):
    """忘记密码 - 发送重置邮件"""
    service = AuthService(db)
    result = service.forgot_password(request)
    
    return MessageResponse(
        success=True,
        data=result
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request - 重置令牌无效或已过期"},
        401: {"model": ErrorResponse, "description": "Unauthorized - 令牌验证失败"}
    },
    summary="重置密码"
)
async def reset_password(
    request: ResetPasswordRequest,
    db: DbDep
):
    """重置密码"""
    service = AuthService(db)
    result = service.reset_password(request)
    
    return MessageResponse(
        success=True,
        data=result
    )