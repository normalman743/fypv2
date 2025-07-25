#!/usr/bin/env python3
"""
发送测试邮件到 support@icu.584743.xyz
用于测试邮箱配置和邮件发送功能
"""

import resend
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv("/Users/mannormal/Downloads/fyp/backend/.env")

def send_test_email():
    """发送测试邮件"""
    try:
        # 设置 Resend API
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            print("❌ RESEND_API_KEY 未设置")
            return False
        
        resend.api_key = api_key
        print(f"✅ Resend API 已配置")
        
        # 邮件内容
        html_content = """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h2 style="color: #333; margin-top: 0; text-align: center;">📧 邮件系统测试</h2>
            </div>
            
            <div style="background-color: white; padding: 20px; border: 1px solid #dee2e6; border-radius: 8px;">
                <h3 style="color: #495057;">Hi 👋</h3>
                <p>这是一封来自校园LLM系统的测试邮件。</p>
                
                <div style="background-color: #d1ecf1; padding: 15px; border-radius: 5px; border-left: 4px solid #bee5eb; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #0c5460;">测试信息：</h4>
                    <ul style="margin-bottom: 0; color: #0c5460;">
                        <li>发送时间：${new Date().toLocaleString('zh-CN', {timeZone: 'Asia/Shanghai'})}</li>
                        <li>发件人：Campus LLM System</li>
                        <li>测试目的：验证邮件发送功能</li>
                        <li>邮件格式：HTML + 中文支持</li>
                    </ul>
                </div>
                
                <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; border-left: 4px solid #c3e6cb; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #155724;">✅ 测试项目：</h4>
                    <ul style="margin-bottom: 0; color: #155724;">
                        <li>✅ Resend API 连接</li>
                        <li>✅ 域名验证 (icu.584743.xyz)</li>
                        <li>✅ HTML 邮件格式</li>
                        <li>✅ 中文字符支持</li>
                        <li>✅ 邮件投递</li>
                    </ul>
                </div>
                
                <p>如果您收到这封邮件，说明邮件系统工作正常！🎉</p>
            </div>
            
            <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
            
            <div style="text-align: center; color: #6c757d; font-size: 12px;">
                <p>此邮件由校园LLM系统自动发送，请勿回复。</p>
                <p>如有问题，请联系 <a href="mailto:support@icu.584743.xyz" style="color: #6c757d;">support@icu.584743.xyz</a></p>
            </div>
        </div>
        """
        
        # 发送邮件
        from_email = f"Campus LLM <{os.getenv('EMAIL_ADDRESS', 'no-reply@icu.584743.xyz')}>"
        to_email = "support@icu.584743.xyz"
        
        print(f"📧 准备发送测试邮件...")
        print(f"   发件人: {from_email}")
        print(f"   收件人: {to_email}")
        
        response = resend.Emails.send({
            "from": from_email,
            "to": [to_email],
            "subject": "📧 校园LLM系统 - 邮件功能测试",
            "html": html_content
        })
        
        print(f"✅ 测试邮件发送成功！")
        print(f"   邮件ID: {response.get('id', 'N/A')}")
        print(f"   响应: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ 发送测试邮件失败:")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误详情: {str(e)}")
        return False

def main():
    """主函数"""
    print("📧 校园LLM系统 - 邮件功能测试")
    print("=" * 50)
    print("🎯 目标: support@icu.584743.xyz")
    print()
    
    if send_test_email():
        print("\n🎉 测试完成！请检查 support@icu.584743.xyz 邮箱")
    else:
        print("\n❌ 测试失败，请检查配置")

if __name__ == "__main__":
    main()