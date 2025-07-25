#!/usr/bin/env python3
"""
🚨 SECURITY WARNING: This file has been secured to prevent credential exposure.
Admin account management should now use secure credential management.

发送管理员账号信息邮件 - 安全版本
使用环境变量配置管理员账号信息，不再在源代码中存储明文密码
"""

import resend
import os
import secrets
import string
from dotenv import load_dotenv
from typing import List, Dict

# 加载环境变量
load_dotenv("/Users/mannormal/Downloads/fyp/backend/.env")

# 🔒 SECURITY IMPROVEMENT: Remove hardcoded credentials
# Admin accounts now must be configured via environment variables or secure credential store
def get_admin_accounts_from_env() -> List[Dict[str, str]]:
    """
    从环境变量或安全配置中获取管理员账号信息
    Environment variables format:
    ADMIN_ACCOUNT_1_USERNAME=admin
    ADMIN_ACCOUNT_1_EMAIL=admin@example.com
    ADMIN_ACCOUNT_1_PASSWORD=secure_password_here
    """
    admin_accounts = []
    
    # Check for environment-based admin accounts
    for i in range(1, 6):  # Support up to 5 admin accounts
        username = os.getenv(f"ADMIN_ACCOUNT_{i}_USERNAME")
        email = os.getenv(f"ADMIN_ACCOUNT_{i}_EMAIL") 
        password = os.getenv(f"ADMIN_ACCOUNT_{i}_PASSWORD")
        
        if username and email and password:
            admin_accounts.append({
                "username": username,
                "email": email,
                "password": password
            })
    
    if not admin_accounts:
        print("⚠️  WARNING: No admin accounts configured via environment variables.")
        print("   Please set ADMIN_ACCOUNT_*_USERNAME, ADMIN_ACCOUNT_*_EMAIL, and ADMIN_ACCOUNT_*_PASSWORD")
        print("   environment variables for secure admin account management.")
        return []
    
    return admin_accounts

def generate_secure_password(length: int = 16) -> str:
    """生成安全的随机密码"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def setup_resend():
    """设置Resend API"""
    api_key = os.getenv("RESEND_API_KEY")
    print(f"🔍 检查环境变量...")
    print(f"   RESEND_API_KEY: {'已设置' if api_key else '未设置'}")
    print(f"   EMAIL_ADDRESS: {os.getenv('EMAIL_ADDRESS', '未设置')}")
    
    if not api_key:
        raise ValueError("RESEND_API_KEY not found in environment variables")
    
    resend.api_key = api_key
    print(f"✅ Resend API已配置")
    print(f"   API Key 前缀: {api_key[:10]}...") # 只显示前几位

def create_email_content(admin_info):
    """生成邮件内容"""
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="color: #333; margin-top: 0;">校园LLM系统 - 管理员账号信息</h2>
        </div>
        
        <div style="background-color: white; padding: 20px; border: 1px solid #dee2e6; border-radius: 8px;">
            <h3 style="color: #495057;">您的管理员账号已创建</h3>
            <p>您好，您的校园LLM系统管理员账号已经准备就绪。</p>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h4 style="margin-top: 0; color: #495057;">登录信息：</h4>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #495057;">用户名：</td>
                        <td style="padding: 8px 0; font-family: monospace; background-color: #e9ecef; padding: 4px 8px; border-radius: 3px;">
                            {admin_info['username']}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #495057;">邮箱：</td>
                        <td style="padding: 8px 0; font-family: monospace; background-color: #e9ecef; padding: 4px 8px; border-radius: 3px;">
                            {admin_info['email']}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #495057;">密码：</td>
                        <td style="padding: 8px 0; font-family: monospace; background-color: #fff3cd; padding: 4px 8px; border-radius: 3px; border: 1px solid #ffeaa7;">
                            {admin_info['password']}
                        </td>
                    </tr>
                </table>
            </div>
            
            <div style="background-color: #d1ecf1; padding: 15px; border-radius: 5px; border-left: 4px solid #bee5eb;">
                <h4 style="margin-top: 0; color: #0c5460;">系统地址：</h4>
                <p style="margin-bottom: 8px;">
                    <strong>前端（开发中）：</strong>
                    <a href="https://icu.584743.xyz" style="color: #0c5460; text-decoration: none;">
                        https://icu.584743.xyz
                    </a>
                </p>
                <p style="margin-bottom: 0;">
                    <strong>后端API文档：</strong>
                    <a href="https://api.icu.584743.xyz/docs" style="color: #0c5460; text-decoration: none;">
                        https://api.icu.584743.xyz/docs
                    </a>
                </p>
            </div>
            
            <div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; border-left: 4px solid #f5c6cb; margin-top: 20px;">
                <h4 style="margin-top: 0; color: #721c24;">安全提醒：</h4>
                <ul style="margin-bottom: 0; color: #721c24;">
                    <li>请妥善保管您的登录凭据</li>
                    <li>建议首次登录后修改密码</li>
                    <li>不要在公共场所或不安全的网络环境下登录</li>
                </ul>
            </div>
        </div>
        
        <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
        
        <div style="text-align: center; color: #6c757d; font-size: 12px;">
            <p>此邮件由校园LLM系统自动发送，请勿回复。</p>
            <p>如有问题，请联系 <a href="mailto:support@icu.584743.xyz" style="color: #6c757d;">support@icu.584743.xyz</a></p>
        </div>
    </div>
    """
    
    return html_content

def send_all_admin_emails():
    """批量发送所有管理员邮件 - 安全版本"""
    try:
        # 🔒 SECURITY IMPROVEMENT: Get admin accounts from secure configuration
        admin_accounts = get_admin_accounts_from_env()
        
        if not admin_accounts:
            print("❌ 无法获取管理员账号信息，邮件发送中止")
            return False
        
        # 准备批量发送参数
        from_email = f"Campus LLM <{os.getenv('EMAIL_ADDRESS', 'no-reply@icu.584743.xyz')}>"
        
        params: List[resend.Emails.SendParams] = []
        
        for admin in admin_accounts:
            email_content = create_email_content(admin)
            
            email_param = {
                "from": from_email,
                "to": [admin["email"]],
                "subject": "校园LLM系统 - 管理员账号信息",
                "html": email_content
            }
            params.append(email_param)
            print(f"✅ 准备发送给 {admin['username']} ({admin['email']})")
        
        print(f"\n🚀 正在批量发送 {len(params)} 封邮件...")
        
        # 批量发送
        response = resend.Batch.send(params)
        
        print(f"✅ 批量发送完成!")
        print(f"📧 发送结果:")
        
        if hasattr(response, 'data') and response.data:
            for i, result in enumerate(response.data):
                admin = admin_accounts[i]
                if hasattr(result, 'id'):
                    print(f"   ✅ {admin['username']}: 邮件ID = {result.id}")
                else:
                    print(f"   ❌ {admin['username']}: 发送失败")
        else:
            print(f"   响应内容: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ 批量发送邮件失败:")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误详情: {str(e)}")
        
        # 尝试获取更多错误信息
        if hasattr(e, 'response'):
            print(f"   HTTP响应: {e.response}")
        if hasattr(e, 'status_code'):
            print(f"   状态码: {e.status_code}")
        
        return False

def main():
    """主函数 - 安全版本"""
    print("📧 校园LLM系统 - 管理员账号信息邮件发送器 (安全版本)")
    print("=" * 70)
    print("🔒 SECURITY: 已移除硬编码凭据，现使用环境变量配置")
    print("=" * 70)
    
    try:
        # 🔒 SECURITY IMPROVEMENT: Get admin accounts from secure configuration
        admin_accounts = get_admin_accounts_from_env()
        
        if not admin_accounts:
            print("\n❌ 错误：未找到管理员账号配置")
            print("请设置以下环境变量：")
            print("  ADMIN_ACCOUNT_1_USERNAME=your_username")
            print("  ADMIN_ACCOUNT_1_EMAIL=your_email")
            print("  ADMIN_ACCOUNT_1_PASSWORD=your_secure_password")
            print("  (以此类推，支持最多5个管理员账号)")
            return
        
        # 设置Resend API
        setup_resend()
        
        # 显示要发送的账号（不显示密码）
        print(f"\n准备向以下 {len(admin_accounts)} 个管理员发送账号信息：")
        for admin in admin_accounts:
            print(f"  - {admin['username']} ({admin['email']})")
        
        print(f"\n🚀 开始批量发送邮件...")
        
        # 批量发送邮件
        success = send_all_admin_emails()
        
        # 总结
        print(f"\n" + "=" * 70)
        if success:
            print("🎉 邮件批量发送完成！")
            print("🔒 提醒：建议管理员首次登录后立即修改密码")
        else:
            print("❌ 邮件发送失败")
            
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")

if __name__ == "__main__":
    main()