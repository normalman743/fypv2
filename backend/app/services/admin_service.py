from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.invite_code import InviteCode
from app.models.user import User
from app.schemas.invite_code import CreateInviteCodeRequest, UpdateInviteCodeRequest
from app.core.exceptions import NotFoundError, BadRequestError
from datetime import datetime
import secrets
import string
from typing import List, Optional, Dict, Any


class AdminService:
    def __init__(self, db: Session):
        self.db = db

    def generate_invite_code(self) -> str:
        """生成邀请码"""
        # 生成8位随机字符串，包含字母和数字
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(secrets.choice(alphabet) for _ in range(8))
            # 检查是否已存在
            if not self.db.query(InviteCode).filter(InviteCode.code == code).first():
                return code

    def create_invite_code(self, request: CreateInviteCodeRequest, created_by: int) -> InviteCode:
        """创建邀请码"""
        code = self.generate_invite_code()
        
        invite_code = InviteCode(
            code=code,
            description=request.description,
            expires_at=request.expires_at,
            is_used=False,
            created_by=created_by
        )
        
        self.db.add(invite_code)
        self.db.commit()
        self.db.refresh(invite_code)
        return invite_code

    def get_invite_codes(self, skip: int = 0, limit: int = 100) -> List[InviteCode]:
        """获取邀请码列表"""
        return self.db.query(InviteCode).offset(skip).limit(limit).all()

    def get_invite_code_by_id(self, invite_code_id: int) -> InviteCode:
        """根据ID获取邀请码"""
        invite_code = self.db.query(InviteCode).filter(InviteCode.id == invite_code_id).first()
        if not invite_code:
            raise NotFoundError("邀请码不存在", "INVITE_CODE_NOT_FOUND")
        return invite_code

    def update_invite_code(self, invite_code_id: int, request: UpdateInviteCodeRequest) -> InviteCode:
        """更新邀请码"""
        invite_code = self.get_invite_code_by_id(invite_code_id)
        
        if request.description is not None:
            invite_code.description = request.description
        if request.expires_at is not None:
            invite_code.expires_at = request.expires_at
        
        self.db.commit()
        self.db.refresh(invite_code)
        return invite_code

    def delete_invite_code(self, invite_code_id: int) -> bool:
        """删除邀请码"""
        invite_code = self.get_invite_code_by_id(invite_code_id)
        self.db.delete(invite_code)
        self.db.commit()
        return True

    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置"""
        # 这里可以扩展为从数据库或配置文件读取
        return {
            "max_file_size": 10485760,  # 10MB
            "allowed_file_types": ["pdf", "docx", "txt", "jpg", "png"],
            "ai_model": "gpt-4",
            "rag_enabled": True,
            "max_chat_history": 1000,
            "max_files_per_chat": 10
        }

    def update_system_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """更新系统配置"""
        # 这里可以扩展为保存到数据库或配置文件
        # 目前只是返回更新后的配置
        current_config = self.get_system_config()
        current_config.update(config)
        return current_config

    def get_audit_logs(self, 
                      user_id: Optional[int] = None,
                      action: Optional[str] = None,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      skip: int = 0,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """获取审计日志"""
        # 这里可以扩展为从数据库读取真实的审计日志
        # 目前返回模拟数据
        mock_logs = [
            {
                "id": 1,
                "user_id": 1,
                "username": "admin",
                "action": "login",
                "details": "用户登录",
                "ip_address": "127.0.0.1",
                "created_at": "2025-01-15T10:30:00Z"
            },
            {
                "id": 2,
                "user_id": 2,
                "username": "testuser",
                "action": "create_chat",
                "details": "创建聊天",
                "ip_address": "127.0.0.1",
                "created_at": "2025-01-15T11:00:00Z"
            },
            {
                "id": 3,
                "user_id": 1,
                "username": "admin",
                "action": "create_invite_code",
                "details": "创建邀请码",
                "ip_address": "127.0.0.1",
                "created_at": "2025-01-15T12:00:00Z"
            }
        ]
        
        # 应用过滤条件
        filtered_logs = mock_logs
        
        if user_id:
            filtered_logs = [log for log in filtered_logs if log["user_id"] == user_id]
        
        if action:
            filtered_logs = [log for log in filtered_logs if log["action"] == action]
        
        if start_date:
            try:
                # Handle different date formats
                if 'T' in start_date:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                else:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                
                filtered_logs = [log for log in filtered_logs 
                               if datetime.fromisoformat(log["created_at"].replace('Z', '+00:00')) >= start_dt]
            except ValueError:
                # If date parsing fails, return empty list
                return []
        
        if end_date:
            try:
                # Handle different date formats
                if 'T' in end_date:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                else:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                
                filtered_logs = [log for log in filtered_logs 
                               if datetime.fromisoformat(log["created_at"].replace('Z', '+00:00')) <= end_dt]
            except ValueError:
                # If date parsing fails, return empty list
                return []
        
        return filtered_logs[skip:skip + limit] 