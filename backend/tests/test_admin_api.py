"""
管理员 API 测试

测试策略：
1. 使用默认admin用户（不重复创建）
2. 测试主要功能路径和错误处理
3. 重点关注业务逻辑正确性
4. 适度的覆盖率，不过度测试
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch

from app.models.user import User
from app.models.invite_code import InviteCode
from app.models.audit_log import AuditLog


class TestAdminInviteCodes:
    """邀请码管理测试"""
    
    def test_create_invite_code_success(self, client: TestClient, admin_headers: dict):
        """测试创建邀请码 - 成功路径"""
        response = client.post(
            "/api/v1/invite-codes",
            json={
                "description": "pytest测试邀请码",
                "expires_at": "2025-12-31T23:59:59Z"
            },
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "invite_code" in data["data"]
        assert data["data"]["invite_code"]["code"]  # 应该有生成的邀请码
    
    def test_create_invite_code_no_permission(self, client: TestClient, regular_headers: dict):
        """测试非管理员无法创建邀请码"""
        response = client.post(
            "/api/v1/invite-codes",
            json={"description": "test"},
            headers=regular_headers
        )
        assert response.status_code == 403  # Forbidden
    
    def test_get_invite_codes_list(self, client: TestClient, admin_headers: dict):
        """测试获取邀请码列表"""
        # 先创建一个邀请码
        client.post(
            "/api/v1/invite-codes",
            json={"description": "test list"},
            headers=admin_headers
        )
        
        # 获取列表
        response = client.get("/api/v1/invite-codes", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "invite_codes" in data["data"]
        assert len(data["data"]["invite_codes"]) >= 1
    
    def test_get_invite_codes_pagination(self, client: TestClient, admin_headers: dict):
        """测试邀请码分页"""
        response = client.get(
            "/api/v1/invite-codes?skip=0&limit=5",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestAdminSystemConfig:
    """系统配置测试"""
    
    def test_get_system_config_success(self, client: TestClient, admin_headers: dict):
        """测试获取系统配置"""
        response = client.get("/api/v1/system/config", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 验证关键配置字段存在
        config = data["data"]["config"]
        required_fields = [
            "app_name", "environment", "registration_enabled",
            "max_file_size", "max_file_size_mb", "total_users"
        ]
        for field in required_fields:
            assert field in config
    
    def test_get_system_config_no_sensitive_data(self, client: TestClient, admin_headers: dict):
        """测试系统配置不包含敏感信息"""
        response = client.get("/api/v1/system/config", headers=admin_headers)
        config = response.json()["data"]["config"]
        
        # 确保不包含敏感字段
        sensitive_fields = ["secret_key", "database_url", "openai_api_key"]
        for field in sensitive_fields:
            assert field not in config
    
    def test_get_system_config_no_permission(self, client: TestClient, regular_headers: dict):
        """测试普通用户无法访问系统配置"""
        response = client.get("/api/v1/system/config", headers=regular_headers)
        assert response.status_code == 403


class TestAdminAuditLogs:
    """审计日志测试"""
    
    @pytest.fixture
    def sample_audit_log(self, db_session: Session, default_admin_user: User):
        """创建示例审计日志"""
        log = AuditLog(
            user_id=default_admin_user.id,
            action="test_action",
            entity_type="test_entity",
            entity_id=1,
            details={"test": "data"},
            ip_address="127.0.0.1"
        )
        db_session.add(log)
        db_session.commit()
        return log
    
    def test_get_audit_logs_success(self, client: TestClient, admin_headers: dict, sample_audit_log):
        """测试获取审计日志"""
        response = client.get("/api/v1/audit-logs", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "logs" in data["data"]
        assert "total" in data["data"]
        assert "pagination" in data["data"]
    
    def test_get_audit_logs_filter_by_user(self, client: TestClient, admin_headers: dict, sample_audit_log):
        """测试按用户过滤审计日志"""
        user_id = sample_audit_log.user_id
        response = client.get(
            f"/api/v1/audit-logs?user_id={user_id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        logs = data["data"]["logs"]
        if logs:  # 如果有日志，验证过滤是否正确
            assert all(log["user_id"] == user_id for log in logs)
    
    def test_get_audit_logs_invalid_date(self, client: TestClient, admin_headers: dict):
        """测试无效日期格式"""
        response = client.get(
            "/api/v1/audit-logs?start_date=invalid-date",
            headers=admin_headers
        )
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False


class TestAdminFileManagement:
    """文件管理测试"""
    
    @patch('app.api.v1.admin.UnifiedFileService')
    def test_upload_global_file_success(self, mock_service_class, client: TestClient, 
                                      admin_headers: dict, sample_file_upload_data: dict):
        """测试上传全局文件"""
        # Mock服务返回
        mock_service = mock_service_class.return_value
        mock_service.upload_file.return_value = type('MockFile', (), {
            'id': 1,
            'original_name': 'test.pdf',
            'file_type': 'pdf',
            'scope': 'global',
            'visibility': 'public',
            'is_processed': False,
            'processing_status': 'pending',
            'created_at': '2025-01-27T10:00:00Z',
            'file_size': 1024,
            'description': '测试文件',
            'tags': ['test']
        })()
        
        response = client.post(
            "/api/v1/global-files/upload",
            files={"file": sample_file_upload_data["file"]},
            data={
                "description": sample_file_upload_data["description"],
                "tags": sample_file_upload_data["tags"],
                "visibility": sample_file_upload_data["visibility"]
            },
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "file" in data["data"]
    
    def test_upload_global_file_no_permission(self, client: TestClient, regular_headers: dict):
        """测试普通用户无法上传全局文件"""
        response = client.post(
            "/api/v1/global-files/upload",
            files={"file": ("test.txt", b"test", "text/plain")},
            headers=regular_headers
        )
        assert response.status_code == 403


class TestAdminAPIEdgeCases:
    """边界情况和错误处理测试"""
    
    def test_missing_auth_token(self, client: TestClient):
        """测试缺少认证token"""
        response = client.get("/api/v1/system/config")
        assert response.status_code == 401
    
    def test_invalid_auth_token(self, client: TestClient):
        """测试无效认证token"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v1/system/config", headers=headers)
        assert response.status_code == 401
    
    def test_malformed_json(self, client: TestClient, admin_headers: dict):
        """测试格式错误的JSON"""
        response = client.post(
            "/api/v1/invite-codes",
            data="invalid-json",
            headers={**admin_headers, "Content-Type": "application/json"}
        )
        assert response.status_code == 422  # FastAPI 自动处理JSON解析错误


# ========== 集成测试 ==========

class TestAdminWorkflow:
    """管理员工作流程集成测试"""
    
    def test_complete_invite_code_workflow(self, client: TestClient, admin_headers: dict):
        """测试完整的邀请码管理流程"""
        # 1. 创建邀请码
        create_response = client.post(
            "/api/v1/invite-codes",
            json={"description": "workflow test"},
            headers=admin_headers
        )
        assert create_response.status_code == 200
        invite_code_id = create_response.json()["data"]["invite_code"]["id"]
        
        # 2. 获取邀请码列表
        list_response = client.get("/api/v1/invite-codes", headers=admin_headers)
        assert list_response.status_code == 200
        
        # 3. 更新邀请码
        update_response = client.put(
            f"/api/v1/invite-codes/{invite_code_id}",
            json={"description": "updated description"},
            headers=admin_headers
        )
        assert update_response.status_code == 200
        
        # 4. 删除邀请码
        delete_response = client.delete(
            f"/api/v1/invite-codes/{invite_code_id}",
            headers=admin_headers
        )
        assert delete_response.status_code == 200


# ========== 辅助方法 ==========

def assert_admin_api_error_format(response, expected_status: int):
    """验证管理员API错误响应格式"""
    assert response.status_code == expected_status
    data = response.json()
    if expected_status >= 400:
        assert data["success"] is False
        if "error" in data:
            assert "code" in data["error"]
            assert "message" in data["error"]