"""共享邮件服务"""
import secrets
import string
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from .config import settings
from .exceptions import BaseServiceException
from .error_codes import ErrorCodes
from .logging import get_logger


class EmailServiceException(BaseServiceException):
    """邮件服务异常"""
    pass


class EmailTemplate:
    """邮件模板"""
    
    @staticmethod
    def verification_email(username: str, code: str, expire_minutes: int) -> Dict[str, str]:
        """验证邮件模板"""
        return {
            "subject": "🌟 欢迎加入ICU智能学习助手！",
            "html": f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; border-radius: 15px;">
                <div style="background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #667eea; font-size: 28px; margin: 0; font-weight: 700;">🏫 ICU智能学习助手</h1>
                        <div style="width: 50px; height: 3px; background: linear-gradient(90deg, #667eea, #764ba2); margin: 15px auto;"></div>
                    </div>
                    
                    <div style="text-align: center; margin-bottom: 30px;">
                        <div style="background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); width: 80px; height: 80px; border-radius: 50%; margin: 0 auto 15px; display: flex; align-items: center; justify-content: center; font-size: 40px;">⭐</div>
                        <h2 style="color: #333; font-size: 24px; margin: 0; font-weight: 600;">你好，{username}！</h2>
                        <p style="color: #666; font-size: 16px; margin: 10px 0; line-height: 1.6;">我是你的专属AI学习助手 <strong style="color: #667eea;">Star</strong>✨</p>
                    </div>
                    
                    <div style="background: #f8f9ff; padding: 25px; border-radius: 12px; text-align: center; margin: 30px 0;">
                        <p style="color: #555; font-size: 16px; margin: 0 0 15px;">欢迎来到ICU智能学习平台！请使用以下验证码完成注册：</p>
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-size: 42px; font-weight: bold; letter-spacing: 8px; padding: 20px; border-radius: 10px; margin: 20px 0; font-family: 'Courier New', monospace;">
                            {code}
                        </div>
                        <p style="color: #888; font-size: 14px; margin: 15px 0 0;">验证码有效期：<strong>{expire_minutes}分钟</strong></p>
                    </div>
                    
                    <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 25px 0; border-radius: 5px;">
                        <p style="color: #856404; margin: 0; font-size: 14px;">🔒 为了您的账户安全，请不要将验证码分享给他人</p>
                    </div>
                    
                    <div style="text-align: center; margin-top: 35px;">
                        <p style="color: #666; font-size: 14px; margin: 0; line-height: 1.5;">
                            即将开启你的智能学习之旅！🚀<br>
                            如果您没有申请注册，请忽略此邮件
                        </p>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <div style="text-align: center;">
                        <p style="color: #999; font-size: 12px; margin: 0;">
                            💌 此邮件由ICU智能学习助手系统自动发送<br>
                            <span style="color: #667eea;">Star助手</span> 期待与你一起学习成长
                        </p>
                    </div>
                </div>
            </div>
            """
        }
    
    @staticmethod
    def password_reset_email(username: str, reset_token: str) -> Dict[str, str]:
        """密码重置邮件模板"""
        return {
            "subject": "🔐 ICU智能学习助手 - 密码重置",
            "html": f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; border-radius: 15px;">
                <div style="background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #667eea; font-size: 28px; margin: 0; font-weight: 700;">🏫 ICU智能学习助手</h1>
                        <div style="width: 50px; height: 3px; background: linear-gradient(90deg, #667eea, #764ba2); margin: 15px auto;"></div>
                    </div>
                    
                    <div style="text-align: center; margin-bottom: 30px;">
                        <div style="background: linear-gradient(135deg, #ffa726 0%, #ffcc02 100%); width: 80px; height: 80px; border-radius: 50%; margin: 0 auto 15px; display: flex; align-items: center; justify-content: center; font-size: 40px;">🔐</div>
                        <h2 style="color: #333; font-size: 24px; margin: 0; font-weight: 600;">密码重置请求</h2>
                        <p style="color: #666; font-size: 16px; margin: 10px 0; line-height: 1.6;">你好，{username}！我们收到了你的密码重置请求</p>
                    </div>
                    
                    <div style="background: #f8f9ff; padding: 25px; border-radius: 12px; text-align: center; margin: 30px 0;">
                        <p style="color: #555; font-size: 16px; margin: 0 0 15px;">请使用以下重置令牌来重置你的密码：</p>
                        <div style="background: #f8f9fa; border: 2px dashed #dee2e6; padding: 15px; border-radius: 8px; margin: 20px 0; font-family: 'Courier New', monospace; font-size: 14px; word-break: break-all;">
                            {reset_token}
                        </div>
                        <p style="color: #888; font-size: 14px; margin: 15px 0 0;">重置令牌有效期：<strong>1小时</strong></p>
                    </div>
                    
                    <div style="background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 25px 0; border-radius: 5px;">
                        <p style="color: #721c24; margin: 0; font-size: 14px;">⚠️ 如果你没有申请密码重置，请忽略此邮件并确保账户安全</p>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <div style="text-align: center;">
                        <p style="color: #999; font-size: 12px; margin: 0;">
                            💌 此邮件由ICU智能学习助手系统自动发送<br>
                            如有疑问，请联系系统管理员
                        </p>
                    </div>
                </div>
            </div>
            """
        }


class EmailService:
    """统一的邮件服务"""
    
    METHOD_EXCEPTIONS = {
        "send_verification_email": [EmailServiceException],
        "send_password_reset_email": [EmailServiceException],
        "send_notification_email": [EmailServiceException],
        "generate_verification_code": [],
        "can_send_email": [EmailServiceException],
    }
    
    def __init__(self):
        self.resend_client = None
        self.logger = get_logger(self.__class__.__name__)
        
        # 初始化Resend客户端
        if settings.resend_api_key and settings.resend_api_key != "test-key":
            try:
                import resend
                resend.api_key = settings.resend_api_key
                self.resend_client = resend
                self.logger.info("Resend email client initialized successfully")
            except ImportError:
                self.logger.warning("Resend library not installed, using development mode")
            except Exception as e:
                self.logger.warning(f"Resend client initialization failed: {e}")
    
    def generate_verification_code(self, length: int = 6) -> str:
        """生成验证码"""
        if length == 6:
            # 6位数字验证码
            return ''.join(secrets.choice(string.digits) for _ in range(6))
        else:
            # 字母数字组合验证码
            return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))
    
    def can_send_email(self, db: Session, email: str, email_type: str = "verification", 
                      rate_limit_minutes: int = 1) -> bool:
        """检查是否可以发送邮件（防止频繁发送）"""
        try:
            from src.auth.models import EmailVerification
            
            # 检查最近N分钟内是否已发送过相同类型的邮件
            time_ago = datetime.now(timezone.utc) - timedelta(minutes=rate_limit_minutes)
            
            if email_type == "verification":
                recent_email = db.query(EmailVerification).filter(
                    EmailVerification.email == email,
                    EmailVerification.created_at > time_ago
                ).first()
                return recent_email is None
            
            # 其他类型的邮件可以添加更多检查
            return True
            
        except Exception as e:
            raise EmailServiceException(f"检查邮件发送频率失败: {str(e)}", ErrorCodes.RATE_CHECK_ERROR)
    
    def send_verification_email(self, email: str, username: str, verification_code: str) -> bool:
        """发送验证邮件"""
        try:
            template = EmailTemplate.verification_email(
                username, 
                verification_code, 
                settings.verification_code_expire_minutes
            )
            
            return self._send_email(
                to_email=email,
                subject=template["subject"],
                html_content=template["html"]
            )
            
        except Exception as e:
            raise EmailServiceException(f"发送验证邮件失败: {str(e)}", ErrorCodes.SEND_ERROR)
    
    def send_password_reset_email(self, email: str, username: str, reset_token: str) -> bool:
        """发送密码重置邮件"""
        try:
            template = EmailTemplate.password_reset_email(username, reset_token)
            
            return self._send_email(
                to_email=email,
                subject=template["subject"],
                html_content=template["html"]
            )
            
        except Exception as e:
            raise EmailServiceException(f"发送密码重置邮件失败: {str(e)}", ErrorCodes.SEND_ERROR)
    
    def send_notification_email(self, email: str, subject: str, content: str, 
                              is_html: bool = False) -> bool:
        """发送通知邮件"""
        try:
            if is_html:
                return self._send_email(to_email=email, subject=subject, html_content=content)
            else:
                return self._send_email(to_email=email, subject=subject, text_content=content)
                
        except Exception as e:
            raise EmailServiceException(f"发送通知邮件失败: {str(e)}", ErrorCodes.SEND_ERROR)
    
    async def _send_email_async(self, to_email: str, subject: str, 
                               html_content: str = None, text_content: str = None) -> bool:
        """异步发送邮件的通用方法"""
        if self.resend_client and settings.email_from_address:
            try:
                email_data = {
                    "from": settings.email_from_address,
                    "to": to_email,
                    "subject": subject
                }
                
                if html_content:
                    email_data["html"] = html_content
                if text_content:
                    email_data["text"] = text_content
                
                # 在线程池中运行同步的邮件发送
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.resend_client.Emails.send(email_data)
                )
                self.logger.info(f"Email sent successfully to {to_email}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to send email via Resend: {e}")
                return False
        else:
            # 开发模式：打印邮件内容
            self.logger.info(f"Development Mode - Email Details: To: {to_email}, Subject: {subject}, Content: {text_content or 'HTML content (see logs)'}")
            if html_content:
                self.logger.debug(f"HTML Content: {html_content[:200]}...")
            return True
    
    def _send_email(self, to_email: str, subject: str, 
                   html_content: str = None, text_content: str = None) -> bool:
        """发送邮件的同步版本（兼容旧代码）"""
        # 在新的事件循环中运行异步方法
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        
        if loop is None:
            # 没有运行中的事件循环，直接运行
            return asyncio.run(self._send_email_async(to_email, subject, html_content, text_content))
        else:
            # 有运行中的事件循环，在线程池中运行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, 
                    self._send_email_async(to_email, subject, html_content, text_content)
                )
                return future.result()


# 全局邮件服务实例
_email_service = None

def get_email_service() -> EmailService:
    """获取邮件服务实例"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service