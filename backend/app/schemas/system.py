from pydantic import BaseModel
from typing import Dict, Any, List
from app.schemas.common import BaseResponse

# 系统配置相关模型
class SystemConfigData(BaseModel):
    config: Dict[str, Any]

class SystemConfigResponse(BaseResponse):
    success: bool = True
    data: Dict[str, Any]  # 直接使用Dict而不是包装

# 审计日志相关模型
class AuditLogItem(BaseModel):
    id: int
    user_id: int
    action: str
    entity_type: str
    entity_id: int
    details: Dict[str, Any]
    ip_address: str
    created_at: str

class AuditLogsData(BaseModel):
    logs: List[AuditLogItem]

class AuditLogsResponse(BaseResponse):
    success: bool = True
    data: Dict[str, Any]  # 直接使用Dict而不是包装