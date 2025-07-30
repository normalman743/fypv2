from api import login,logout,register,get_me,update_me,health_check
import requests
from typing import Dict, Any, Optional
# first test case for email verification is not enabled

def get_token(response: requests.Response) -> Optional[str]:
    """
    从登录响应中获取用户的 JWT Token
    """
    if response.status_code == 200:
        return response.json().get("data", {}).get("access_token")
    return None
# user:testuser password:testpassword

def get_user_token() -> Optional[str]:
    """
    从登录响应中获取用户的 JWT Token
    """
    response = login("testuser", "user123456")
    token = get_token(response)
    if token:
        return token
    return None

def get_admin_token() -> Optional[str]:
    """
    从登录响应中获取管理员的 JWT Token
    """
    response = login("testadmin", "admin123456")
    token = get_token(response)
    if token:
        return token
    return None

if __name__ == "__main__":
    print("Testing user login...")
    try:
        health_response = health_check()
        print(f"Health check response: {health_response.status_code}")
    except requests.RequestException as e:
        print(f"Health check failed: {e}")
        exit(1)
    
    try:
        user_token = get_user_token()
        if user_token:
            print(f"User token: {user_token}")

            user_info_response = get_me(user_token)
            
            user_info = user_info_response.json()
            print(f"User info: {user_info}")
            
            update_response = update_me(user_token, update_info)
            
            update_response = update_me(user_token, {"username": "testuser"})
            
            

            print("Testing user logout...")
            logout_response = logout(user_token)
            print(f"Logout response: {logout_response.status_code}")
        else:
            print("User login failed.")
    except requests.RequestException as e:
        print(f"An error occurred during user operations: {e}")
        exit(1)

    try:
        print("Testing admin login...")
        admin_token = get_admin_token()
        if admin_token:
            print(f"Admin token: {admin_token}")
            print("Testing admin info retrieval...")
            admin_info_response = get_me(admin_token)
            print(f"Admin info response: {admin_info_response.json()}")
            
            print("Testing admin info update...")
            update_response = update_me(admin_token, {"username": "updatedadmin"})
            print(f"Update response: {update_response.json()}")
            
            print("Testing admin logout...")
            logout_response = logout(admin_token)
            print(f"Logout response: {logout_response.status_code}")
        else:
            print("Admin login failed.")
    except requests.RequestException as e:
        print(f"An error occurred during admin operations: {e}")
        exit(1)