"""
Admin模块API集成测试 - 完整HTTP请求流程测试

基于真实环境测试策略，测试完整的Admin API端点行为
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from src.auth.models import User, InviteCode
from src.admin.models import AuditLog
from .conftest import assert_success_response, assert_error_response


class TestInviteCodeManagementAPI:
    """邀请码管理API测试"""
    
    def test_create_invite_code_success(self, client: TestClient, admin_headers: dict):
        """测试创建邀请码 - 成功路径"""
        response = client.post("/api/v1/admin/invite-codes", 
                             headers=admin_headers,
                             json={
                                 "description": "测试邀请码",
                                 "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat()
                             })
        
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content}")
        assert_success_response(response, ["invite_code"], expected_status=201)
        
        data = response.json()["data"]
        assert data["invite_code"]["description"] == "测试邀请码"
        assert data["invite_code"]["is_used"] is False
        assert data["invite_code"]["is_active"] is True
        assert len(data["invite_code"]["code"]) >= 8  # 邀请码长度验证
        assert data["invite_code"]["created_by_username"] == "admin_test"
        
        # 验证状态码 201
        assert response.status_code == 201
    
    def test_create_invite_code_no_description(self, client: TestClient, admin_headers: dict):
        """测试创建邀请码 - 无描述"""
        response = client.post("/api/v1/admin/invite-codes", 
                             headers=admin_headers,
                             json={})
        
        assert_success_response(response, ["invite_code"], expected_status=201)
        
        data = response.json()["data"]
        assert data["invite_code"]["description"] is None
        assert data["invite_code"]["expires_at"] is None  # 永不过期
    
    def test_create_invite_code_invalid_expire_time(self, client: TestClient, admin_headers: dict):
        """测试创建邀请码 - 过期时间早于当前时间"""
        response = client.post("/api/v1/admin/invite-codes",
                             headers=admin_headers, 
                             json={
                                 "description": "测试邀请码",
                                 "expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat()
                             })
        
        assert_error_response(response, 400, "INVALID_EXPIRE_TIME")
    
    def test_create_invite_code_unauthorized(self, client: TestClient, user_headers: dict):
        """测试创建邀请码 - 非管理员权限"""
        response = client.post("/api/v1/admin/invite-codes",
                             headers=user_headers,
                             json={"description": "测试邀请码"})
        
        assert_error_response(response, 403, "ADMIN_REQUIRED")
    
    def test_create_invite_code_no_auth(self, client: TestClient):
        """测试创建邀请码 - 未认证"""
        response = client.post("/api/v1/admin/invite-codes",
                             json={"description": "测试邀请码"})
        
        assert_error_response(response, 403, "HTTP_403")

    def test_get_invite_codes_list(self, client: TestClient, admin_headers: dict, db_session: Session, admin_user: User):
        """测试获取邀请码列表"""
        # 创建测试数据
        test_codes = []
        for i in range(3):
            invite_code = InviteCode(
                code=f"TEST{i:03d}ABCD",
                description=f"测试邀请码 {i+1}",
                created_by=admin_user.id
            )
            db_session.add(invite_code)
            test_codes.append(invite_code)
        db_session.commit()
        
        response = client.get("/api/v1/admin/invite-codes", headers=admin_headers)
        
        assert_success_response(response, ["invite_codes", "total", "pagination"])
        
        data = response.json()["data"]
        assert len(data["invite_codes"]) >= 3  # 至少包含我们创建的3个
        assert data["total"] >= 3
        assert data["pagination"]["skip"] == 0
        assert data["pagination"]["limit"] == 100
        
        # 验证数据结构
        invite_code = data["invite_codes"][0]
        expected_fields = ["id", "code", "description", "is_used", "used_by", 
                          "used_by_username", "used_at", "expires_at", "is_active",
                          "created_by", "created_by_username", "created_at"]
        for field in expected_fields:
            assert field in invite_code
    
    def test_get_invite_codes_pagination(self, client: TestClient, admin_headers: dict):
        """测试邀请码列表分页"""
        response = client.get("/api/v1/admin/invite-codes?skip=0&limit=5", 
                             headers=admin_headers)
        
        assert_success_response(response, ["invite_codes", "total", "pagination"])
        
        data = response.json()["data"]
        assert len(data["invite_codes"]) <= 5
        assert data["pagination"]["skip"] == 0
        assert data["pagination"]["limit"] == 5
    
    def test_get_invite_code_detail_success(self, client: TestClient, admin_headers: dict, 
                                          db_session: Session, admin_user: User):
        """测试获取邀请码详情 - 成功路径"""
        # 创建测试邀请码
        invite_code = InviteCode(
            code="DETAILTEST001",
            description="详情测试邀请码",
            created_by=admin_user.id
        )
        db_session.add(invite_code)
        db_session.commit()
        db_session.refresh(invite_code)
        
        response = client.get(f"/api/v1/admin/invite-codes/{invite_code.id}", 
                             headers=admin_headers)
        
        assert_success_response(response, ["invite_code"], expected_status=200)
        
        data = response.json()["data"]
        assert data["invite_code"]["id"] == invite_code.id
        assert data["invite_code"]["code"] == "DETAILTEST001"
        assert data["invite_code"]["description"] == "详情测试邀请码"
    
    def test_get_invite_code_detail_not_found(self, client: TestClient, admin_headers: dict):
        """测试获取邀请码详情 - 不存在"""
        response = client.get("/api/v1/admin/invite-codes/99999", headers=admin_headers)
        
        assert_error_response(response, 404, "INVITE_CODE_NOT_FOUND")
    
    def test_update_invite_code_success(self, client: TestClient, admin_headers: dict,
                                      db_session: Session, admin_user: User):
        """测试更新邀请码 - 成功路径"""
        # 创建测试邀请码
        invite_code = InviteCode(
            code="UPDATE001",
            description="原始描述",
            created_by=admin_user.id
        )
        db_session.add(invite_code)
        db_session.commit()
        db_session.refresh(invite_code)
        
        response = client.put(f"/api/v1/admin/invite-codes/{invite_code.id}",
                             headers=admin_headers,
                             json={
                                 "description": "更新后的描述",
                                 "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat()
                             })
        
        assert_success_response(response, ["invite_code"], expected_status=200)
        
        data = response.json()["data"]
        assert data["invite_code"]["description"] == "更新后的描述"
        assert data["invite_code"]["expires_at"] is not None
    
    def test_update_invite_code_used_restriction(self, client: TestClient, admin_headers: dict,
                                               used_invite_code: InviteCode):
        """测试更新已使用邀请码的限制"""
        response = client.put(f"/api/v1/admin/invite-codes/{used_invite_code.id}",
                             headers=admin_headers,
                             json={
                                 "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat()
                             })
        
        assert_error_response(response, 400, "USED_INVITE_CODE_READONLY")
    
    def test_update_invite_code_not_found(self, client: TestClient, admin_headers: dict):
        """测试更新不存在的邀请码"""
        response = client.put("/api/v1/admin/invite-codes/99999",
                             headers=admin_headers,
                             json={"description": "新描述"})
        
        assert_error_response(response, 404, "INVITE_CODE_NOT_FOUND")
    
    def test_delete_invite_code_success(self, client: TestClient, admin_headers: dict,
                                      db_session: Session, admin_user: User):
        """测试删除邀请码 - 成功路径"""
        # 创建测试邀请码
        invite_code = InviteCode(
            code="DELETE001",
            description="待删除邀请码",
            created_by=admin_user.id
        )
        db_session.add(invite_code)
        db_session.commit()
        db_session.refresh(invite_code)
        
        response = client.delete(f"/api/v1/admin/invite-codes/{invite_code.id}",
                               headers=admin_headers)
        
        assert_success_response(response, ["message"])
        
        data = response.json()["data"]
        assert "DELETE001" in data["message"]
        assert "删除成功" in data["message"]
    
    def test_delete_invite_code_used(self, client: TestClient, admin_headers: dict,
                                   used_invite_code: InviteCode):
        """测试删除已使用的邀请码"""
        response = client.delete(f"/api/v1/admin/invite-codes/{used_invite_code.id}",
                               headers=admin_headers)
        
        assert_error_response(response, 409, "INVITE_CODE_ALREADY_USED")
    
    def test_delete_invite_code_not_found(self, client: TestClient, admin_headers: dict):
        """测试删除不存在的邀请码"""
        response = client.delete("/api/v1/admin/invite-codes/99999", headers=admin_headers)
        
        assert_error_response(response, 404, "INVITE_CODE_NOT_FOUND")


class TestSystemConfigAPI:
    """系统配置API测试"""
    
    def test_get_system_config_success(self, client: TestClient, admin_headers: dict):
        """测试获取系统配置 - 成功路径"""
        response = client.get("/api/v1/admin/system/config", headers=admin_headers)
        
        assert_success_response(response, ["app_name", "app_version", "environment",
                                         "registration_enabled", "email_verification_enabled",
                                         "total_users", "total_files", "storage_used_mb",
                                         "max_file_size_mb", "max_upload_files_per_user"])
        
        data = response.json()["data"]
        assert isinstance(data["total_users"], int)
        assert data["total_users"] >= 0
        assert isinstance(data["total_files"], int)
        assert isinstance(data["storage_used_mb"], (int, float))
        assert isinstance(data["registration_enabled"], bool)
    
    def test_get_system_config_unauthorized(self, client: TestClient, user_headers: dict):
        """测试获取系统配置 - 非管理员权限"""
        response = client.get("/api/v1/admin/system/config", headers=user_headers)
        
        assert_error_response(response, 403, "ADMIN_REQUIRED")


class TestAuditLogAPI:
    """审计日志API测试"""
    
    def test_get_audit_logs_success(self, client: TestClient, admin_headers: dict,
                                  db_session: Session, admin_user: User):
        """测试获取审计日志 - 成功路径"""
        # 创建测试审计日志
        test_log = AuditLog(
            user_id=admin_user.id,
            action="TEST_ACTION",
            entity_type="test_entity",
            entity_id=1,
            details={"test": "data"},
            ip_address="127.0.0.1"
        )
        db_session.add(test_log)
        db_session.commit()
        
        response = client.get("/api/v1/admin/audit-logs", headers=admin_headers)
        
        assert_success_response(response, ["logs", "total", "pagination"])
        
        data = response.json()["data"]
        assert len(data["logs"]) >= 1
        assert data["total"] >= 1
        
        # 验证日志数据结构
        log = data["logs"][0]
        expected_fields = ["id", "user_id", "username", "action", "entity_type", 
                          "entity_id", "details", "ip_address", "user_agent", "created_at"]
        for field in expected_fields:
            assert field in log
    
    def test_get_audit_logs_with_filters(self, client: TestClient, admin_headers: dict,
                                       db_session: Session, admin_user: User):
        """测试审计日志过滤查询"""
        # 创建测试数据
        test_log1 = AuditLog(
            user_id=admin_user.id,
            action="CREATE_INVITE_CODE",
            entity_type="invite_code",
            entity_id=1,
        )
        test_log2 = AuditLog(
            user_id=admin_user.id,
            action="DELETE_INVITE_CODE", 
            entity_type="invite_code",
            entity_id=2,
        )
        db_session.add_all([test_log1, test_log2])
        db_session.commit()
        
        # 测试按action过滤
        response = client.get(f"/api/v1/admin/audit-logs?action=CREATE_INVITE_CODE&user_id={admin_user.id}",
                             headers=admin_headers)
        
        assert_success_response(response, ["logs", "total", "pagination"])
        
        data = response.json()["data"]
        if data["logs"]:  # 如果有数据
            for log in data["logs"]:
                if log["action"] == "CREATE_INVITE_CODE":
                    assert log["user_id"] == admin_user.id
    
    def test_get_audit_logs_pagination(self, client: TestClient, admin_headers: dict):
        """测试审计日志分页"""
        response = client.get("/api/v1/admin/audit-logs?skip=0&limit=10", 
                             headers=admin_headers)
        
        assert_success_response(response, ["logs", "total", "pagination"])
        
        data = response.json()["data"]
        assert len(data["logs"]) <= 10
        assert data["pagination"]["skip"] == 0
        assert data["pagination"]["limit"] == 10
    
    def test_get_audit_logs_invalid_date_range(self, client: TestClient, admin_headers: dict):
        """测试审计日志无效日期范围"""
        end_date = datetime.utcnow()
        start_date = end_date + timedelta(days=1)  # 开始时间晚于结束时间
        
        response = client.get(
            f"/api/v1/admin/audit-logs?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}",
            headers=admin_headers
        )
        
        assert_error_response(response, 400, "INVALID_DATE_RANGE")
    
    def test_get_audit_logs_date_range_too_large(self, client: TestClient, admin_headers: dict):
        """测试审计日志日期范围过大"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=400)  # 超过365天限制
        
        response = client.get(
            f"/api/v1/admin/audit-logs?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}",
            headers=admin_headers
        )
        
        assert_error_response(response, 400, "DATE_RANGE_TOO_LARGE")
    
    def test_get_audit_logs_unauthorized(self, client: TestClient, user_headers: dict):
        """测试获取审计日志 - 非管理员权限"""
        response = client.get("/api/v1/admin/audit-logs", headers=user_headers)
        
        assert_error_response(response, 403, "ADMIN_REQUIRED")


class TestAdminPermissionSecurity:
    """管理员权限安全测试"""
    
    def test_all_admin_endpoints_require_admin_role(self, client: TestClient, user_headers: dict):
        """测试所有管理员端点都需要管理员权限"""
        admin_endpoints = [
            ("POST", "/api/v1/admin/invite-codes", {"description": "test"}),
            ("GET", "/api/v1/admin/invite-codes", None),
            ("GET", "/api/v1/admin/invite-codes/1", None),
            ("PUT", "/api/v1/admin/invite-codes/1", {"description": "test"}),
            ("DELETE", "/api/v1/admin/invite-codes/1", None),
            ("GET", "/api/v1/admin/system/config", None),
            ("GET", "/api/v1/admin/audit-logs", None),
        ]
        
        for method, endpoint, payload in admin_endpoints:
            if method == "POST":
                response = client.post(endpoint, headers=user_headers, json=payload)
            elif method == "PUT":
                response = client.put(endpoint, headers=user_headers, json=payload)
            elif method == "DELETE":
                response = client.delete(endpoint, headers=user_headers)
            else:  # GET
                response = client.get(endpoint, headers=user_headers)
            
            assert_error_response(response, 403, "ADMIN_REQUIRED"), f"Failed for {method} {endpoint}"
    
    def test_all_admin_endpoints_require_authentication(self, client: TestClient):
        """测试所有管理员端点都需要认证"""
        admin_endpoints = [
            ("POST", "/api/v1/admin/invite-codes", {"description": "test"}),
            ("GET", "/api/v1/admin/invite-codes", None),
            ("GET", "/api/v1/admin/invite-codes/1", None),
            ("PUT", "/api/v1/admin/invite-codes/1", {"description": "test"}),
            ("DELETE", "/api/v1/admin/invite-codes/1", None),
            ("GET", "/api/v1/admin/system/config", None), 
            ("GET", "/api/v1/admin/audit-logs", None),
        ]
        
        for method, endpoint, payload in admin_endpoints:
            if method == "POST":
                response = client.post(endpoint, json=payload)
            elif method == "PUT":
                response = client.put(endpoint, json=payload)
            elif method == "DELETE":
                response = client.delete(endpoint)
            else:  # GET
                response = client.get(endpoint)
            
            assert_error_response(response, 403, "HTTP_403"), f"Failed for {method} {endpoint}"