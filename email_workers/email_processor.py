#!/usr/bin/env python3
"""
邮件处理系统
处理邮件转发和自动回复功能
"""

import re
import resend
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv
import json

# 加载环境变量
load_dotenv("/Users/mannormal/Downloads/fyp/backend/.env")

class EmailProcessor:
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        if self.api_key:
            resend.api_key = self.api_key
        
        # 管理员邮箱映射
        self.admin_emails = {
            "admin": "admin@icu.584743.xyz",
            "ad-xiong": "ad-xiong@icu.584743.xyz", 
            "ad-qi": "ad-qi@icu.584743.xyz",
            "ad-shen": "ad-shen@icu.584743.xyz",
            "ad-chen": "ad-chen@icu.584743.xyz"
        }
        
        # 反向映射：邮箱到用户名
        self.email_to_user = {v: k for k, v in self.admin_emails.items()}
    
    def parse_target_user(self, subject: str, content: str) -> Optional[str]:
        """
        从邮件主题或内容中解析目标用户
        支持格式：
        1. [USER:admin] 在主题中
        2. @admin 在内容中  
        3. 发送给admin 在内容中
        """
        # 检查主题中的 [USER:username] 格式
        subject_match = re.search(r'\[USER:(\w+)\]', subject, re.IGNORECASE)
        if subject_match:
            username = subject_match.group(1).lower()
            if username in self.admin_emails:
                return username
        
        # 检查内容中的 @username 格式
        at_matches = re.findall(r'@(\w+)', content, re.IGNORECASE)
        for match in at_matches:
            username = match.lower()
            if username in self.admin_emails:
                return username
        
        # 检查内容中的"发送给 username"格式
        send_to_matches = re.findall(r'发送给\s*(\w+)', content, re.IGNORECASE)
        for match in send_to_matches:
            username = match.lower()
            if username in self.admin_emails:
                return username
        
        return None
    
    def create_forwarded_email_content(self, original_email: Dict) -> str:
        """创建转发邮件的HTML内容"""
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="color: #333; margin: 0;">📧 转发邮件 - 校园LLM系统</h3>
            </div>
            
            <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffeaa7; margin-bottom: 20px;">
                <h4 style="margin-top: 0; color: #856404;">📨 原始邮件信息</h4>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 5px 10px; font-weight: bold; color: #495057; width: 80px;">发件人:</td>
                        <td style="padding: 5px 10px;">{original_email.get('from', 'Unknown')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px 10px; font-weight: bold; color: #495057;">主题:</td>
                        <td style="padding: 5px 10px;">{original_email.get('subject', 'No Subject')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px 10px; font-weight: bold; color: #495057;">时间:</td>
                        <td style="padding: 5px 10px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                </table>
            </div>
            
            <div style="background-color: white; padding: 20px; border: 1px solid #dee2e6; border-radius: 8px;">
                <h4 style="color: #495057; margin-top: 0;">📄 邮件内容：</h4>
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 3px solid #007bff;">
                    {original_email.get('content', '无内容')}
                </div>
            </div>
            
            <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
            
            <div style="text-align: center; color: #6c757d; font-size: 12px;">
                <p>此邮件由校园LLM系统自动转发</p>
                <p>如需回复，请直接回复此邮件或联系 <a href="mailto:support@icu.584743.xyz">support@icu.584743.xyz</a></p>
            </div>
        </div>
        """
    
    def create_auto_reply_content(self, original_email: Dict) -> str:
        """创建自动回复邮件的HTML内容"""
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #d4edda; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h2 style="color: #155724; margin-top: 0;">✅ 我们已收到您的邮件</h2>
            </div>
            
            <div style="background-color: white; padding: 20px; border: 1px solid #dee2e6; border-radius: 8px;">
                <p>亲爱的用户，</p>
                <p>感谢您联系校园LLM系统支持团队！</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #495057;">📋 您的请求信息：</h4>
                    <ul style="margin-bottom: 0; color: #495057;">
                        <li><strong>工单编号：</strong> #{datetime.now().strftime('%Y%m%d%H%M%S')}</li>
                        <li><strong>收到时间：</strong> {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</li>
                        <li><strong>邮件主题：</strong> {original_email.get('subject', '无主题')}</li>
                    </ul>
                </div>
                
                <div style="background-color: #d1ecf1; padding: 15px; border-radius: 5px; border-left: 4px solid #bee5eb;">
                    <h4 style="margin-top: 0; color: #0c5460;">⏰ 处理时间说明：</h4>
                    <ul style="margin-bottom: 0; color: #0c5460;">
                        <li>一般咨询：1-2个工作日内回复</li>
                        <li>技术问题：2-3个工作日内回复</li>
                        <li>紧急问题：24小时内回复</li>
                    </ul>
                </div>
                
                <p>我们的技术团队正在处理您的请求，会尽快为您提供解决方案。</p>
                <p>如有紧急问题，请直接回复此邮件并在主题中标注 <strong>[紧急]</strong>。</p>
            </div>
            
            <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
            
            <div style="text-align: center; color: #6c757d; font-size: 12px;">
                <p>此邮件由校园LLM系统自动发送，请勿直接回复。</p>
                <p>如需联系，请发送邮件至 <a href="mailto:support@icu.584743.xyz" style="color: #6c757d;">support@icu.584743.xyz</a></p>
            </div>
        </div>
        """
    
    def process_incoming_email(self, email_data: Dict) -> Dict:
        """
        处理收到的邮件
        email_data 格式：
        {
            "from": "user@example.com",
            "to": "l:cuhk.fyp.llm@outlook.com", 
            "subject": "[USER:admin] 系统问题",
            "content": "邮件内容...",
            "html": "HTML内容..."
        }
        """
        result = {
            "forwarded": False,
            "auto_replied": False,
            "target_user": None,
            "errors": []
        }
        
        try:
            # 1. 解析目标用户
            target_user = self.parse_target_user(
                email_data.get('subject', ''),
                email_data.get('content', '')
            )
            
            result["target_user"] = target_user
            
            # 2. 转发邮件到指定用户或support
            if target_user and target_user in self.admin_emails:
                # 转发给特定管理员
                target_email = self.admin_emails[target_user]
                forward_subject = f"[转发] {email_data.get('subject', '无主题')}"
            else:
                # 转发给通用support
                target_email = "support@icu.584743.xyz"
                forward_subject = f"[用户咨询] {email_data.get('subject', '无主题')}"
            
            # 发送转发邮件
            forward_content = self.create_forwarded_email_content(email_data)
            
            forward_response = resend.Emails.send({
                "from": f"Campus LLM <no-reply@icu.584743.xyz>",
                "to": [target_email],
                "subject": forward_subject,
                "html": forward_content
            })
            
            result["forwarded"] = True
            result["forward_id"] = forward_response.get('id')
            
            # 3. 发送自动回复给原发件人
            reply_content = self.create_auto_reply_content(email_data)
            
            reply_response = resend.Emails.send({
                "from": f"Campus LLM Support <support@icu.584743.xyz>",
                "to": [email_data.get('from')],
                "subject": f"Re: {email_data.get('subject', '您的咨询')} - 已收到",
                "html": reply_content
            })
            
            result["auto_replied"] = True
            result["reply_id"] = reply_response.get('id')
            
        except Exception as e:
            result["errors"].append(str(e))
        
        return result

def main():
    """测试函数"""
    processor = EmailProcessor()
    
    # 模拟收到的邮件
    test_email = {
        "from": "student@example.com",
        "to": "l:cuhk.fyp.llm@outlook.com",
        "subject": "[USER:admin] 系统登录问题",
        "content": "我无法登录系统，用户名是test123，请帮忙查看一下。",
        "html": "<p>我无法登录系统，用户名是test123，请帮忙查看一下。</p>"
    }
    
    print("📧 邮件处理系统测试")
    print("=" * 50)
    print(f"处理邮件: {test_email['subject']}")
    print(f"发件人: {test_email['from']}")
    
    result = processor.process_incoming_email(test_email)
    
    print(f"\n📊 处理结果:")
    print(f"  目标用户: {result.get('target_user', '未指定')}")
    print(f"  转发状态: {'✅' if result.get('forwarded') else '❌'}")
    print(f"  自动回复: {'✅' if result.get('auto_replied') else '❌'}")
    
    if result.get('errors'):
        print(f"  错误: {result['errors']}")

if __name__ == "__main__":
    main()