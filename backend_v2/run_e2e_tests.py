#!/usr/bin/env python3
"""
Campus LLM System v2 - End-to-End测试运行脚本
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path


def run_command(cmd, cwd=None):
    """运行命令并返回结果"""
    print(f"🔧 执行命令: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr


def check_dependencies():
    """检查依赖"""
    print("📋 检查依赖...")
    
    required_packages = ['pytest', 'requests', 'faker']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行以下命令安装依赖:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 所有依赖已满足")
    return True


def check_api_server(api_url):
    """检查API服务器状态"""
    print(f"🔍 检查API服务器状态: {api_url}")
    
    try:
        import requests
        response = requests.get(f"{api_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ API服务器运行正常")
            return True
        else:
            print(f"❌ API服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到API服务器: {e}")
        print("\n💡 请确保API服务器正在运行:")
        print("   cd backend_v2")
        print("   source v2env/bin/activate")
        print("   uvicorn src.main:app --reload --port 8001")
        return False


def main():
    parser = argparse.ArgumentParser(description="Campus LLM System v2 - E2E测试运行器")
    
    # 测试选项
    parser.add_argument("--smoke-only", action="store_true", 
                       help="只运行冒烟测试")
    parser.add_argument("--module", choices=["auth", "admin", "course", "storage", "chat", "ai"],
                       help="只运行指定模块的测试")
    parser.add_argument("--api-url", default="http://localhost:8001",
                       help="API服务器地址 (默认: http://localhost:8001)")
    parser.add_argument("--debug", action="store_true",
                       help="启用调试模式")
    parser.add_argument("--no-cleanup", action="store_true",
                       help="测试后不清理数据")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="详细输出")
    parser.add_argument("--parallel", "-n", type=int, metavar="N",
                       help="并行运行测试 (需要安装pytest-xdist)")
    
    # pytest选项
    parser.add_argument("--html", metavar="FILE",
                       help="生成HTML测试报告 (需要安装pytest-html)")
    parser.add_argument("--junitxml", metavar="FILE", 
                       help="生成JUnit XML测试报告")
    parser.add_argument("--cov", action="store_true",
                       help="生成覆盖率报告 (需要安装pytest-cov)")
    
    # 其他选项
    parser.add_argument("--no-check", action="store_true",
                       help="跳过依赖和服务器检查")
    parser.add_argument("--dry-run", action="store_true",
                       help="显示将要执行的命令但不实际运行")
    
    args = parser.parse_args()
    
    # 获取项目根目录
    project_root = Path(__file__).parent
    e2e_tests_dir = project_root / "tests" / "e2e"
    
    print("🎯 Campus LLM System v2 - End-to-End测试")
    print("=" * 50)
    
    # 检查依赖和服务器
    if not args.no_check:
        if not check_dependencies():
            return 1
        
        if not check_api_server(args.api_url):
            return 1
    
    # 构建pytest命令
    cmd = ["python", "-m", "pytest", str(e2e_tests_dir)]
    
    # 添加测试选择选项
    if args.smoke_only:
        cmd.extend(["--smoke-only", "-m", "smoke"])
    
    if args.module:
        cmd.extend(["-m", args.module])
    
    # 添加API配置
    cmd.extend(["--api-url", args.api_url])
    
    # 添加调试选项
    if args.debug:
        cmd.append("--e2e-debug")
    
    if args.no_cleanup:
        cmd.append("--no-cleanup")
    
    # 添加输出选项
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # 添加并行运行选项
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    # 添加报告选项
    if args.html:
        cmd.extend(["--html", args.html, "--self-contained-html"])
    
    if args.junitxml:
        cmd.extend(["--junitxml", args.junitxml])
    
    if args.cov:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
    
    # 显示将要执行的命令
    print(f"🚀 准备执行测试命令:")
    print(f"   {' '.join(cmd)}")
    print()
    
    if args.dry_run:
        print("🏃 干运行模式，不实际执行测试")
        return 0
    
    # 设置环境变量
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    
    # 执行测试
    print("🧪 开始执行E2E测试...")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, cwd=project_root, env=env)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        return 130
    except Exception as e:
        print(f"\n❌ 执行测试时发生错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())