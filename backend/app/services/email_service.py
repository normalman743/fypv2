import secrets
import string
from datetime import datetime, timedelta
from typing import Optional
import resend
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.email_verification import EmailVerification
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        if settings.resend_api_key:
            resend.api_key = settings.resend_api_key
        else:
            logger.warning("Resend API key not configured")
    
    def generate_verification_code(self) -> str:
        """生成6位数验证码"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    def can_send_verification(self, db: Session, email: str) -> bool:
        """检查是否可以发送验证码（防止频繁发送）"""
        # 检查最近1分钟内是否已发送过
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
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
            expires_at = datetime.utcnow() + timedelta(minutes=settings.verification_code_expire_minutes)
            
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
                        "subject": "校园LLM系统 - 邮箱验证码",
                        "html": f"""
                        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                            <h2>邮箱验证</h2>
                            <p>您好 {user.username}，</p>
                            <p>您的验证码是：</p>
                            <h1 style="color: #333; text-align: center; font-size: 36px; letter-spacing: 5px;">
                                {code}
                            </h1>
                            <p>验证码将在 {settings.verification_code_expire_minutes} 分钟内有效。</p>
                            <p>如果您没有请求此验证码，请忽略此邮件。</p>
                            <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                            <p style="color: #666; font-size: 12px;">
                                此邮件由校园LLM系统自动发送，请勿回复。
                            </p>
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
            EmailVerification.expires_at > datetime.utcnow(),
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
        verification.verified_at = datetime.utcnow()
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