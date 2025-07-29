"""Auth模块的FastAPI路由定义 - 基于FastAPI 2024最佳实践"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .schemas import (
    UserRegister, UserLogin, UserUpdate, PasswordChangeRequest,
    ForgotPasswordRequest, ResetPasswordRequest, EmailVerificationRequest,
    ResendVerificationRequest, LoginResponse, RegisterResponse, 
    UserProfileResponse, MessageResponse, UserResponse, RegisterData, LoginData
)
from .service import AuthService
from .models import User
from src.shared.dependencies import DbDep, UserDep
from src.shared.schemas import ErrorResponse
from src.shared.api_decorator import create_service_route_config, service_api_handler

# 创建路由器
router = APIRouter(prefix="/auth")


# ===== 现有API接口（保持兼容） =====

@router.post("/register", **create_service_route_config(
    AuthService, 'register', RegisterResponse, 
    success_status=201,
    summary="用户注册",
    description="使用邀请码注册新用户账户，注册成功后会发送验证邮件到用户邮箱进行验证",
    operation_id="register_user"
))
@service_api_handler(AuthService, 'register')
async def register(user_data: UserRegister, db: DbDep):
    """用户注册"""
    service = AuthService(db)
    result = service.register(user_data)
    
    return RegisterResponse(
        success=True,
        data=RegisterData(user=UserResponse.model_validate(result["user"])),
        message=result["message"]
    )


@router.post("/login", **create_service_route_config(
    AuthService, 'login', LoginResponse,
    summary="用户登录",
    description="使用用户名或邮箱登录系统，成功后返回JWT访问令牌",
    operation_id="login_user"
))
@service_api_handler(AuthService, 'login')
async def login(user_data: UserLogin, db: DbDep):
    """用户登录"""
    service = AuthService(db)
    result = service.login(user_data)
    
    return LoginResponse(
        success=True,
        data=LoginData(
            access_token=result["access_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
            user=UserResponse.model_validate(result["user"])
        )
    )


@router.get("/me", **create_service_route_config(
    AuthService, 'get_user_profile', UserProfileResponse,
    summary="获取当前用户信息",
    description="获取当前认证用户的详细信息",
    operation_id="get_current_user_profile"
))
@service_api_handler(AuthService, 'get_user_profile')
async def get_me(current_user: UserDep, db: DbDep):
    """获取当前用户信息"""
    service = AuthService(db)
    result = service.get_user_profile(current_user.id)
    
    return UserProfileResponse(
        success=True,
        data=UserResponse.model_validate(result["user"]),
        message=result.get("message")
    )


@router.put("/me", **create_service_route_config(
    AuthService, 'update_user', UserProfileResponse,
    summary="更新用户信息",
    description="更新当前认证用户的个人信息",
    operation_id="update_current_user"
))
@service_api_handler(AuthService, 'update_user')
async def update_me(
    user_data: UserUpdate,
    current_user: UserDep,
    db: DbDep
):
    """更新当前用户信息"""
    service = AuthService(db)
    result = service.update_user(current_user.id, user_data)
    
    return UserProfileResponse(
        success=True,
        data=UserResponse.model_validate(result["user"]),
        message=result.get("message")
    )


@router.post("/logout", **create_service_route_config(
    AuthService, 'logout', MessageResponse,
    summary="用户登出",
    description="用户登出系统，客户端应清除访问令牌",
    operation_id="logout_user"
))
@service_api_handler(AuthService, 'logout')
async def logout(current_user: UserDep, db: DbDep):
    """用户登出"""
    service = AuthService(db)
    result = service.logout(current_user.id)
    
    return MessageResponse(
        success=True,
        data=result,
        message=result.get("message")
    )


@router.post("/verify-email", **create_service_route_config(
    AuthService, 'verify_email', UserProfileResponse,
    summary="验证邮箱",
    description="使用验证码验证用户邮箱地址",
    operation_id="verify_user_email",
    include_in_schema=False  # 不在自动生成的文档中显示
))
@service_api_handler(AuthService, 'verify_email')
async def verify_email(
    request: EmailVerificationRequest,
    db: DbDep
):
    """验证邮箱"""
    service = AuthService(db)
    result = service.verify_email(request.email, request.code)
    
    return UserProfileResponse(
        success=True,
        data=UserResponse.model_validate(result["user"]),
        message=result.get("message")
    )


@router.post("/resend-verification", **create_service_route_config(
    AuthService, 'resend_verification', MessageResponse,
    summary="重发验证码",
    description="重新发送邮箱验证码",
    operation_id="resend_verification_code",
    include_in_schema=False  # 不在自动生成的文档中显示
))
@service_api_handler(AuthService, 'resend_verification')
async def resend_verification(
    request: ResendVerificationRequest,
    db: DbDep
):
    """重新发送验证码"""
    service = AuthService(db)
    result = service.resend_verification(request.email)
    
    return MessageResponse(
        success=True,
        data=result,
        message=result.get("message")
    )


# ===== 新增API接口 =====

@router.put("/change-password", **create_service_route_config(
    AuthService, 'change_password', MessageResponse,
    summary="修改密码",
    description="修改当前用户密码，需要提供当前密码验证",
    operation_id="change_user_password",
    include_in_schema=False  # 不在自动生成的文档中显示
))
@service_api_handler(AuthService, 'change_password')
async def change_password(
    request: PasswordChangeRequest,
    current_user: UserDep,
    db: DbDep
):
    """修改密码"""
    service = AuthService(db)
    result = service.change_password(current_user.id, request)
    
    return MessageResponse(
        success=True,
        data=result,
        message=result.get("message")
    )


@router.post("/forgot-password", **create_service_route_config(
    AuthService, 'forgot_password', MessageResponse,
    summary="忘记密码",
    description="发送密码重置邮件到用户注册邮箱",
    operation_id="forgot_password",
    include_in_schema=False  # 不在自动生成的文档中显示
))
@service_api_handler(AuthService, 'forgot_password')
async def forgot_password(
    request: ForgotPasswordRequest,
    db: DbDep
):
    """忘记密码 - 发送重置邮件"""
    service = AuthService(db)
    result = service.forgot_password(request)
    
    return MessageResponse(
        success=True,
        data=result,
        message=result.get("message")
    )


@router.post("/reset-password", **create_service_route_config(
    AuthService, 'reset_password', MessageResponse,
    summary="重置密码",
    description="使用重置令牌重置用户密码",
    operation_id="reset_password",
    include_in_schema=False  # 不在自动生成的文档中显示
))
@service_api_handler(AuthService, 'reset_password')
async def reset_password(
    request: ResetPasswordRequest,
    db: DbDep
):
    """重置密码"""
    service = AuthService(db)
    result = service.reset_password(request)
    
    return MessageResponse(
        success=True,
        data=result,
        message=result.get("message")
    )