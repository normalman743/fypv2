from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.schemas.common import BaseResponse

# 系统配置相关模型
class SystemConfigItem(BaseModel):
    """单个系统配置项模型 - 映射 system_config 表"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    config_key: str
    config_value: str
    description: Optional[str] = None
    is_public: bool = False
    updated_by: Optional[int] = None
    updated_at: datetime

class SystemConfigData(BaseModel):
    """批量配置数据模型"""
    config: Dict[str, Any]

class SystemConfigResponse(BaseResponse):
    success: bool = True
    data: Dict[str, Any]  # 直接使用Dict而不是包装

# 审计日志相关模型
class AuditLogItem(BaseModel):
    """审计日志模型 - 映射 audit_logs 表"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime

class AuditLogsData(BaseModel):
    logs: List[AuditLogItem]

class AuditLogsResponse(BaseResponse):
    success: bool = True
    data: Dict[str, Any]  # 直接使用Dict而不是包装