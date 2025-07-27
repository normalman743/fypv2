import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional
import resend
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.email_verification import EmailVerification
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

class EmailConfig:
      VERIFICATION_CODE_LENGTH = 6
      MAX_ATTEMPTS = 5
      RATE_LIMIT_MINUTES = 1

class EmailService:
    def __init__(self):
        if settings.resend_api_key:
            resend.api_key = settings.resend_api_key
        else:
            raise ValueError("Resend API key is not configured. Please set it in the settings.")
    
    def generate_verification_code(self) -> str:
        """生成6位数验证码"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    def can_send_verification(self, db: Session, email: str) -> bool:
        """检查是否可以发送验证码（防止频繁发送）"""
        # 检查最近1分钟内是否已发送过
        one_minute_ago = datetime.now(timezone.utc) - timedelta(minutes=1)
        recent_verification = db.query(EmailVerification).filter(
            EmailVerification.email == email,
            EmailVerification.created_at > one_minute_ago
        ).first()
        
        return recent_verification is None
    
    def send_verification_email(self, db: Session, user: User) -> bool:
        """发送验证邮件"""
        try:
            # 检查是否可以发送
            if not self.can_send_verification(db, user.email):
                logger.warning(f"Too frequent verification requests for {user.email}")
                return False
            
            # 生成验证码
            code = self.generate_verification_code()
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.verification_code_expire_minutes)
            
            # 保存验证码到数据库
            verification = EmailVerification(
                user_id=user.id,
                email=user.email,
                verification_code=code,
                expires_at=expires_at
            )
            db.add(verification)
            db.commit()
            
            # 发送邮件
            if settings.resend_api_key:
                try:
                    resend.Emails.send({
                        "from": settings.email_from_address,
                        "to": user.email,
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
                                    <h2 style="color: #333; font-size: 24px; margin: 0; font-weight: 600;">你好，{user.username}！</h2>
                                    <p style="color: #666; font-size: 16px; margin: 10px 0; line-height: 1.6;">我是你的专属AI学习助手 <strong style="color: #667eea;">Star</strong>✨</p>
                                </div>
                                
                                <div style="background: #f8f9ff; padding: 25px; border-radius: 12px; text-align: center; margin: 30px 0;">
                                    <p style="color: #555; font-size: 16px; margin: 0 0 15px;">欢迎来到ICU智能学习平台！请使用以下验证码完成注册：</p>
                                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-size: 42px; font-weight: bold; letter-spacing: 8px; padding: 20px; border-radius: 10px; margin: 20px 0; font-family: 'Courier New', monospace;">
                                        {code}
                                    </div>
                                    <p style="color: #888; font-size: 14px; margin: 15px 0 0;">验证码有效期：<strong>{settings.verification_code_expire_minutes}分钟</strong></p>
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
                    })
                    logger.info(f"Verification email sent to {user.email}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to send email via Resend: {e}")
                    # 如果邮件发送失败，删除验证码记录
                    db.delete(verification)
                    db.commit()
                    return False
            else:
                # 如果没有配置Resend，仅在开发环境下记录验证码
                logger.info(f"Development mode - Verification code for {user.email}: {code}")
                return True
                
        except Exception as e:
            logger.error(f"Error in send_verification_email: {e}")
            db.rollback()
            return False
    
    def verify_code(self, db: Session, email: str, code: str) -> Optional[User]:
        """验证邮箱验证码"""
        # 查找有效的验证码记录
        verification = db.query(EmailVerification).filter(
            EmailVerification.email == email,
            EmailVerification.verification_code == code,
            EmailVerification.expires_at > datetime.now(timezone.utc),
            EmailVerification.verified_at.is_(None)
        ).first()
        
        if not verification:
            # 增加尝试次数（即使验证码不存在）
            latest_verification = db.query(EmailVerification).filter(
                EmailVerification.email == email,
                EmailVerification.verified_at.is_(None)
            ).order_by(EmailVerification.created_at.desc()).first()
            
            if latest_verification:
                latest_verification.attempts += 1
                db.commit()
                
                # 如果尝试次数过多，返回None
                if latest_verification.attempts >= 5:
                    logger.warning(f"Too many attempts for {email}")
            
            return None
        
        # 标记为已验证
        verification.verified_at = datetime.now(timezone.utc)
        verification.attempts += 1
        
        # 获取用户
        user = db.query(User).filter(User.id == verification.user_id).first()
        
        db.commit()
        logger.info(f"Email verified successfully for {email}")
        
        return user
    
    def resend_verification(self, db: Session, email: str) -> bool:
        """重新发送验证码"""
        # 查找用户
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return False
        
        # 作废之前的验证码
        db.query(EmailVerification).filter(
            EmailVerification.email == email,
            EmailVerification.verified_at.is_(None)
        ).delete()
        db.commit()
        
        # 发送新验证码
        return self.send_verification_email(db, user)

# 创建全局实例
email_service = EmailService()