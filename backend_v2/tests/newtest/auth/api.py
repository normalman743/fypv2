"""
Auth API Functions - 基于OpenAPI规范的简单API调用函数
不包含断言，纯粹的API调用封装
"""
import requests
from typing import Optional, Dict, Any

# 基础配置
BASE_URL = "http://localhost:8001"
PROXIES = {"http": None, "https": None}


def login(username: str, password: str) -> requests.Response:
    """
    POST /api/v1/auth/login
    用户登录
    """
    return requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username": username, "password": password},
        proxies=PROXIES
    )


def logout(token: str) -> requests.Response:
    """
    POST /api/v1/auth/logout  
    用户登出
    """
    return requests.post(
        f"{BASE_URL}/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
        proxies=PROXIES
    )


def get_me(token: str) -> requests.Response:
    """
    GET /api/v1/auth/me
    获取当前用户信息
    """
    return requests.get(
        f"{BASE_URL}/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        proxies=PROXIES
    )


def update_me(token: str, user_data: Dict[str, Any]) -> requests.Response:
    """
    PUT /api/v1/auth/me
    更新用户信息
    """
    return requests.put(
        f"{BASE_URL}/api/v1/auth/me",
        json=user_data,
        headers={"Authorization": f"Bearer {token}"},
        proxies=PROXIES
    )


def register(username: str, email: str, password: str, invite_code: str) -> requests.Response:
    """
    POST /api/v1/auth/register
    用户注册
    """
    return requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "invite_code": invite_code
        },
        proxies=PROXIES
    )


def verify_email(email: str, verification_code: str) -> requests.Response:
    """
    POST /api/v1/auth/verify-email
    邮箱验证
    """
    return requests.post(
        f"{BASE_URL}/api/v1/auth/verify-email",
        json={
            "email": email,
            "verification_code": verification_code
        },
        proxies=PROXIES
    )


def forgot_password(email: str) -> requests.Response:
    """
    POST /api/v1/auth/forgot-password
    忘记密码
    """
    return requests.post(
        f"{BASE_URL}/api/v1/auth/forgot-password",
        json={"email": email},
        proxies=PROXIES
    )


def reset_password(reset_token: str, new_password: str) -> requests.Response:
    """
    PUT /api/v1/auth/reset-password  
    重置密码
    """
    return requests.put(
        f"{BASE_URL}/api/v1/auth/reset-password",
        json={
            "reset_token": reset_token,
            "new_password": new_password
        },
        proxies=PROXIES
    )


def change_password(token: str, current_password: str, new_password: str) -> requests.Response:
    """
    PUT /api/v1/auth/change-password
    修改密码
    """
    return requests.put(
        f"{BASE_URL}/api/v1/auth/change-password",
        json={
            "current_password": current_password,
            "new_password": new_password
        },
        headers={"Authorization": f"Bearer {token}"},
        proxies=PROXIES
    )


def resend_verification(email: str) -> requests.Response:
    """
    POST /api/v1/auth/resend-verification
    重新发送验证码
    """
    return requests.post(
        f"{BASE_URL}/api/v1/auth/resend-verification",
        json={"email": email},
        proxies=PROXIES
    )


# 辅助函数
def get_token_from_login_response(response: requests.Response) -> Optional[str]:
    """从登录响应中提取token"""
    if response.status_code == 200:
        data = response.json()
        if data.get("success") and "data" in data:
            return data["data"].get("access_token")
    return None


def health_check() -> requests.Response:
    """健康检查 - 无需认证"""
    return requests.get(f"{BASE_URL}/health", proxies=PROXIES)