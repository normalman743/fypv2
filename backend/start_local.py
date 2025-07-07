#!/usr/bin/env python3
"""
本地开发环境启动脚本
"""
import os
import sys
import subprocess
from pathlib import Path

def setup_local_env():
    """设置本地环境"""
    print("🔧 设置本地开发环境...")
    
    # 确保必要的目录存在
    directories = [
        "logs",
        "storage/uploads", 
        "data/chroma"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 创建目录: {directory}")
    
    # 复制本地环境配置
    if not os.path.exists(".env"):
        if os.path.exists(".env.local"):
            import shutil
            shutil.copy(".env.local", ".env")
            print("📄 使用本地环境配置 (.env.local → .env)")
        else:
            print("⚠️ 未找到 .env.local 文件")
    
    print("✅ 环境设置完成")

def init_database():
    """初始化数据库"""
    print("🗄️ 初始化本地数据库...")
    
    try:
        result = subprocess.run([
            sys.executable, "scripts/init_local_db.py", "init"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 数据库初始化成功")
            print(result.stdout)
        else:
            print("❌ 数据库初始化失败")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 数据库初始化错误: {e}")
        return False
    
    return True

def start_server():
    """启动开发服务器"""
    print("🚀 启动本地开发服务器...")
    
    try:
        # 使用uvicorn启动服务器
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "127.0.0.1", 
            "--port", "8000",
            "--log-level", "debug"
        ])
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")

def main():
    """主函数"""
    print("🎯 校园LLM系统 - 本地开发环境")
    print("=" * 50)
    
    # 1. 设置环境
    setup_local_env()
    
    # 2. 初始化数据库
    if not init_database():
        print("❌ 数据库初始化失败，无法启动服务器")
        return
    
    print("\n📊 本地环境信息:")
    print("🌐 API地址: http://127.0.0.1:8000")
    print("📚 API文档: http://127.0.0.1:8000/docs")
    print("🔧 管理员: admin / admin123")
    print("👤 测试用户: testuser / test123")
    print("🎫 邀请码: LOCAL2025, TEST2025, DEV2025")
    
    print("\n" + "=" * 50)
    
    # 3. 启动服务器
    start_server()

if __name__ == "__main__":
    main()