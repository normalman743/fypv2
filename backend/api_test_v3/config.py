# -*- coding: utf-8 -*-
"""
API测试工具配置文件
V3.0 模块化版本
"""

import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class APIConfig:
    """API配置类"""
    base_url: str = "http://localhost:8000"
    timeout: int = 30
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

@dataclass
class DatabaseConfig:
    """数据库配置类 - 安全版本"""
    host: str = os.getenv("DB_HOST", "localhost")
    database: str = "campus_llm_db"
    user: str = os.getenv("DB_USER", "root")
    # 🔒 SECURITY IMPROVEMENT: Remove hardcoded database password
    password: str = os.getenv("DB_PASSWORD", "")  # Must be set via environment variable
    port: int = 3306
    
    def __post_init__(self):
        if not self.password:
            raise ValueError("DB_PASSWORD environment variable must be set for security. "
                           "Please set DB_PASSWORD=your_secure_database_password in your environment.")

@dataclass
class TestConfig:
    """测试配置类 - 安全版本"""
    # 🔒 SECURITY IMPROVEMENT: Remove hardcoded passwords from test configuration
    # Test users now use environment variables or generated secure passwords
    
    def get_secure_test_users(self) -> Dict[str, Dict[str, str]]:
        """获取安全的测试用户配置"""
        import secrets
        import string
        
        def generate_secure_password(length: int = 12) -> str:
            """生成安全的测试密码"""
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            return ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # Check for environment variables first, generate secure passwords as fallback
        return {
            "admin": {
                "username": "admin",
                "email": "admin@icu.584743.xyz",
                "password": os.getenv("TEST_ADMIN_PASSWORD", generate_secure_password()),
                "role": "admin"
            },
            "user": {
                "username": "user", 
                "email": "user@icu.584743.xyz",
                "password": os.getenv("TEST_USER_PASSWORD", generate_secure_password()),
                "role": "user"
            },
            "ad-xiong": {
                "username": "ad-xiong",
                "email": "ad-xiong@icu.584743.xyz",
                "password": os.getenv("TEST_XIONG_PASSWORD", generate_secure_password()),
                "role": "admin"
            },
            "ad-qi": {
                "username": "ad-qi",
                "email": "ad-qi@icu.584743.xyz", 
                "password": os.getenv("TEST_QI_PASSWORD", generate_secure_password()),
                "role": "admin"
            },
            "ad-shen": {
                "username": "ad-shen",
                "email": "ad-shen@icu.584743.xyz",
                "password": os.getenv("TEST_SHEN_PASSWORD", generate_secure_password()),
                "role": "admin"
            },
            "ad-chen": {
                "username": "ad-chen", 
                "email": "ad-chen@icu.584743.xyz",
                "password": os.getenv("TEST_CHEN_PASSWORD", generate_secure_password()),
                "role": "admin"
            }
        }
    
    # Legacy compatibility property (use get_secure_test_users() instead)
    @property
    def default_users(self) -> Dict[str, Dict[str, str]]:
        """⚠️ DEPRECATED: Use get_secure_test_users() for secure password handling"""
        return self.get_secure_test_users()
    
    # 默认邀请码
    default_invite_codes = [
        {
            "code": "ADMIN2024",
            "description": "管理员邀请码",
            "is_active": True
        },
        {
            "code": "USER2024", 
            "description": "普通用户邀请码",
            "is_active": True
        },
        {
            "code": "TEST2024",
            "description": "测试邀请码",
            "is_active": True
        },
        {
            "code": "INVITE2025",
            "description": "默认邀请码",
            "is_active": True
        },
        {
            "code": "TEST2025",
            "description": "测试邀请码2025",
            "is_active": True
        },
        {
            "code": "TEST2026",
            "description": "测试邀请码2026",
            "is_active": True
        }
    ]

# 全局配置实例
api_config = APIConfig()
db_config = DatabaseConfig()
test_config = TestConfig()

# 路径配置
BACKEND_DIR = "/Users/mannormal/Downloads/fyp/backend"
STORAGE_DIR = f"{BACKEND_DIR}/storage"
CHROMA_DIR = f"{BACKEND_DIR}/data/chroma"