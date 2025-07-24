#!/usr/bin/env python3
"""
测试 CORS 配置脚本
验证 CORS 设置是否正确处理了 credentials + origins 的组合
"""
import os
import sys
sys.path.append('.')

from app.core.config import settings

def test_cors_config():
    print("=== CORS 配置测试 ===")
    print(f"原始 CORS_ORIGINS 环境变量: {os.getenv('CORS_ORIGINS', '未设置')}")
    print(f"配置中的 cors_origins: {settings.cors_origins}")
    print(f"配置中的 cors_allow_credentials: {settings.cors_allow_credentials}")
    print()
    
    print("=== CORS Origins 列表 ===")
    print(f"cors_origins_list: {settings.cors_origins_list}")
    print(f"cors_origins_for_credentials: {settings.cors_origins_for_credentials}")
    print()
    
    print("=== 实际 FastAPI 中间件将使用的配置 ===")
    cors_origins = settings.cors_origins_for_credentials if settings.cors_allow_credentials else settings.cors_origins_list
    print(f"allow_origins: {cors_origins}")
    print(f"allow_credentials: {settings.cors_allow_credentials}")
    print()
    
    print("=== 配置验证 ===")
    if settings.cors_allow_credentials and "*" in cors_origins:
        print("❌ 错误: 启用了 credentials 但仍使用通配符 '*' 作为 origin")
        print("   这会导致浏览器 CORS 错误: 'Disallowed CORS origin'")
        return False
    elif settings.cors_allow_credentials:
        print("✅ 正确: 启用了 credentials 且使用了具体的 origins")
        print(f"   允许的源: {cors_origins}")
        return True
    else:
        print("✅ 正确: 禁用了 credentials，可以使用通配符")
        return True

if __name__ == "__main__":
    test_cors_config()