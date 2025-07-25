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
    """数据库配置类"""
    host: str = "39.108.113.103"
    database: str = "campus_llm_db"
    user: str = os.getenv("DB_USER", "campus_user")
    password: str = os.getenv("DB_PASSWORD", "CampusLLM123!")
    port: int = 3306

@dataclass
class TestConfig:
    """测试配置类"""
    # 默认测试用户
    default_users = {
        "admin": {
            "username": "admin",
            "email": "admin@test.com",
            "password": "admin123456",
            "role": "admin"
        },
        "user": {
            "username": "user",
            "email": "user@test.com", 
            "password": "user123456",
            "role": "user"
        },
        "ad-xiong": {
            "username": "ad-xiong",
            "email": "ad-xiong@icu.584743.xyz",
            "password": "xiong123",
            "role": "admin"
        },
        "ad-qi": {
            "username": "ad-qi",
            "email": "ad-qi@icu.584743.xyz",
            "password": "qi123",
            "role": "admin"
        },
        "ad-shen": {
            "username": "ad-shen",
            "email": "ad-shen@icu.584743.xyz",
            "password": "shen123",
            "role": "admin"
        },
        "ad-chen": {
            "username": "ad-chen",
            "email": "ad-chen@icu.584743.xyz",
            "password": "chen123",
            "role": "admin"
        }
    }
    
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