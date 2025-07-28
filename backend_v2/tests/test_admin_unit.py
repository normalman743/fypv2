"""
Admin模块单元测试 - 基于pytest最佳实践

测试AdminService的所有方法，覆盖业务逻辑、异常处理和边界条件。
使用真实数据库环境 + 事务回滚策略确保测试隔离。

重要说明：
- 发现AdminService代码中存在关系字段不一致：
  第111行使用了 `joinedload(InviteCode.used_by_user)`
  但模型定义是 `user = relationship("User", foreign_keys=[used_by])`
  应该使用 `InviteCode.user` 而不是 `InviteCode.used_by_user`
- 测试基于实际模型关系编写，避免运行时错误
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from unittest.mock import patch
import uuid

# 导入模型
from src.auth.models import User, InviteCode
from src.admin.models import AuditLog

# 导入服务和schemas
from src.admin.service import AdminService
from src.admin.schemas import CreateInviteCodeRequest, UpdateInviteCodeRequest, AuditLogQuery

# 导入异常
from src.shared.exceptions import BadRequestError, NotFoundError, ConflictError

# 导入配置
from src.shared.config import settings


class TestAdminServiceInviteCodeManagement:
    """邀请码管理功能测试"""
    
    @pytest.fixture
    def admin_service(self, db_session: Session) -> AdminService:
        """创建AdminService实例"""
        return AdminService(db_session)
    
    # ========== 创建邀请码测试 ==========
    
    def test_create_invite_code_success_basic(self, admin_service: AdminService, admin_user: User):
        """测试成功创建基本邀请码"""
        request = CreateInviteCodeRequest(
            description="pytest测试邀请码"
        )
        
        result = admin_service.create_invite_code(request, admin_user.id)
        
        # 验证返回结果
        assert "invite_code" in result
        assert "message" in result
        assert result["message"] == "邀请码创建成功"
        
        # 验证邀请码信息
        invite_code = result["invite_code"]
        assert invite_code["description"] == "pytest测试邀请码"
        assert invite_code["is_used"] is False
        assert invite_code["is_active"] is True
        assert invite_code["created_by"] == admin_user.id
        assert invite_code["created_by_username"] == admin_user.username
        assert invite_code["used_by"] is None
        assert invite_code["used_by_username"] is None
        assert invite_code["used_at"] is None
        assert invite_code["expires_at"] is None
        
        # 验证邀请码格式 (2位字母 + 6位数字)
        code = invite_code["code"]
        assert len(code) == 8
        assert code[:2].isupper()
        assert code[:2].isalpha()
        assert code[2:].isdigit()
    
    def test_create_invite_code_success_with_expiry(self, admin_service: AdminService, admin_user: User):
        """测试创建带过期时间的邀请码"""
        future_time = datetime.utcnow() + timedelta(days=7)
        request = CreateInviteCodeRequest(
            description="带过期时间的邀请码",
            expires_at=future_time
        )
        
        result = admin_service.create_invite_code(request, admin_user.id)
        
        invite_code = result["invite_code"]
        assert invite_code["expires_at"] is not None
        # 时间比较需要容忍一定误差
        expires_at = datetime.fromisoformat(invite_code["expires_at"].replace('Z', '+00:00'))
        time_diff = abs((expires_at - future_time).total_seconds())
        assert time_diff < 10  # 10秒内的误差可接受
    
    def test_create_invite_code_generates_audit_log(self, admin_service: AdminService, admin_user: User, db_session: Session):
        """测试创建邀请码会生成审计日志"""
        request = CreateInviteCodeRequest(description="审计测试")
        
        # 记录创建前的审计日志数量
        initial_count = db_session.query(AuditLog).count()
        
        result = admin_service.create_invite_code(request, admin_user.id)
        
        # 验证审计日志增加
        final_count = db_session.query(AuditLog).count()
        assert final_count == initial_count + 1
        
        # 验证审计日志内容
        audit_log = db_session.query(AuditLog).order_by(AuditLog.created_at.desc()).first()
        assert audit_log.user_id == admin_user.id
        assert audit_log.action == "CREATE_INVITE_CODE"
        assert audit_log.entity_type == "invite_code"
        assert audit_log.entity_id == result["invite_code"]["id"]
        assert audit_log.details is not None
        assert "code" in audit_log.details
        assert "description" in audit_log.details
    
    def test_create_invite_code_invalid_expire_time(self, admin_service: AdminService, admin_user: User):
        """测试过期时间早于当前时间的错误"""
        past_time = datetime.utcnow() - timedelta(hours=1)
        request = CreateInviteCodeRequest(
            description="过期时间测试",
            expires_at=past_time
        )
        
        with pytest.raises(BadRequestError) as exc_info:
            admin_service.create_invite_code(request, admin_user.id)
        
        assert exc_info.value.error_code == "INVALID_EXPIRE_TIME"
        assert "过期时间不能早于当前时间" in str(exc_info.value)
    
    def test_create_invite_code_unique_code_generation(self, admin_service: AdminService, admin_user: User):
        """测试邀请码唯一性生成"""
        codes = set()
        
        # 创建多个邀请码，验证唯一性
        for i in range(5):
            request = CreateInviteCodeRequest(description=f"唯一性测试{i}")
            result = admin_service.create_invite_code(request, admin_user.id)
            code = result["invite_code"]["code"]
            assert code not in codes
            codes.add(code)
    
    @patch('src.admin.service.AdminService._generate_unique_invite_code')
    def test_create_invite_code_conflict_error(self, mock_generate, admin_service: AdminService, admin_user: User, db_session: Session):
        """测试邀请码生成冲突的处理"""
        # 先创建一个邀请码
        existing_code = "CONFLICT1"
        invite_code = InviteCode(
            code=existing_code,
            description="已存在的邀请码",
            created_by=admin_user.id
        )
        db_session.add(invite_code)
        db_session.commit()
        
        # Mock生成器返回相同的码，触发IntegrityError
        mock_generate.return_value = existing_code
        
        request = CreateInviteCodeRequest(description="冲突测试")
        
        with pytest.raises(ConflictError) as exc_info:
            admin_service.create_invite_code(request, admin_user.id)
        
        assert exc_info.value.error_code == "INVITE_CODE_CONFLICT"
        assert "邀请码生成冲突" in str(exc_info.value)
    
    # ========== 查询邀请码测试 ==========
    
    def test_get_invite_codes_success_empty(self, admin_service: AdminService):
        """测试查询空的邀请码列表"""
        result = admin_service.get_invite_codes()
        
        assert "invite_codes" in result
        assert "total" in result
        assert "pagination" in result
        assert result["invite_codes"] == []
        assert result["total"] == 0
        assert result["pagination"]["skip"] == 0
        assert result["pagination"]["limit"] == 100
        assert result["pagination"]["has_more"] is False
    
    def test_get_invite_codes_success_with_data(self, admin_service: AdminService, db_session: Session, admin_user: User, regular_user: User):
        """测试查询有数据的邀请码列表"""
        # 创建测试数据：未使用和已使用的邀请码
        unused_code = InviteCode(
            code="UNUSED01",
            description="未使用邀请码",
            created_by=admin_user.id
        )
        used_code = InviteCode(
            code="USED0001",
            description="已使用邀请码",
            is_used=True,
            used_by=regular_user.id,
            used_at=datetime.utcnow(),
            created_by=admin_user.id
        )
        db_session.add_all([unused_code, used_code])
        db_session.commit()
        
        result = admin_service.get_invite_codes()
        
        assert result["total"] == 2
        assert len(result["invite_codes"]) == 2
        
        # 验证数据按创建时间倒序排列
        codes = result["invite_codes"]
        assert codes[0]["created_at"] >= codes[1]["created_at"]
        
        # 验证未使用邀请码
        unused = next(c for c in codes if c["code"] == "UNUSED01")
        assert unused["is_used"] is False
        assert unused["used_by"] is None
        assert unused["used_by_username"] is None
        assert unused["created_by_username"] == admin_user.username
        
        # 验证已使用邀请码
        used = next(c for c in codes if c["code"] == "USED0001")
        assert used["is_used"] is True
        assert used["used_by"] == regular_user.id
        assert used["used_by_username"] == regular_user.username
        assert used["created_by_username"] == admin_user.username
    
    def test_get_invite_codes_pagination(self, admin_service: AdminService, db_session: Session, admin_user: User):
        """测试邀请码分页功能"""
        # 创建5个邀请码
        for i in range(5):
            code = InviteCode(
                code=f"PAGE{i:04d}",
                description=f"分页测试{i}",
                created_by=admin_user.id
            )
            db_session.add(code)
        db_session.commit()
        
        # 测试第一页
        result = admin_service.get_invite_codes(skip=0, limit=3)
        assert result["total"] == 5
        assert len(result["invite_codes"]) == 3
        assert result["pagination"]["has_more"] is True
        
        # 测试第二页
        result = admin_service.get_invite_codes(skip=3, limit=3)
        assert result["total"] == 5
        assert len(result["invite_codes"]) == 2
        assert result["pagination"]["has_more"] is False
    
    def test_get_invite_code_success(self, admin_service: AdminService, valid_invite_code: InviteCode):
        """测试获取单个邀请码成功"""
        result = admin_service.get_invite_code(valid_invite_code.id)
        
        assert "invite_code" in result
        assert "message" in result
        assert result["message"] is None
        
        invite_code = result["invite_code"]
        assert invite_code["id"] == valid_invite_code.id
        assert invite_code["code"] == valid_invite_code.code
        assert invite_code["description"] == valid_invite_code.description
    
    def test_get_invite_code_not_found(self, admin_service: AdminService):
        """测试获取不存在的邀请码"""
        with pytest.raises(NotFoundError) as exc_info:
            admin_service.get_invite_code(99999)
        
        assert exc_info.value.error_code == "INVITE_CODE_NOT_FOUND"
        assert "邀请码 99999 不存在" in str(exc_info.value)
    
    # ========== 更新邀请码测试 ==========
    
    def test_update_invite_code_success(self, admin_service: AdminService, valid_invite_code: InviteCode, admin_user: User):
        """测试成功更新邀请码"""
        future_time = datetime.utcnow() + timedelta(days=30)
        request = UpdateInviteCodeRequest(
            description="更新后的描述",
            expires_at=future_time,
            is_active=False
        )
        
        result = admin_service.update_invite_code(valid_invite_code.id, request, admin_user.id)
        
        assert "invite_code" in result
        assert "message" in result
        assert result["message"] == "邀请码更新成功"
        
        updated_code = result["invite_code"]
        assert updated_code["description"] == "更新后的描述"
        assert updated_code["is_active"] is False
        assert updated_code["expires_at"] is not None
    
    def test_update_invite_code_not_found(self, admin_service: AdminService, admin_user: User):
        """测试更新不存在的邀请码"""
        request = UpdateInviteCodeRequest(description="不存在")
        
        with pytest.raises(NotFoundError) as exc_info:
            admin_service.update_invite_code(99999, request, admin_user.id)
        
        assert exc_info.value.error_code == "INVITE_CODE_NOT_FOUND"
    
    def test_update_invite_code_used_readonly_restriction(self, admin_service: AdminService, used_invite_code: InviteCode, admin_user: User):
        """测试已使用邀请码的更新限制"""
        future_time = datetime.utcnow() + timedelta(days=30)
        request = UpdateInviteCodeRequest(expires_at=future_time)
        
        with pytest.raises(BadRequestError) as exc_info:
            admin_service.update_invite_code(used_invite_code.id, request, admin_user.id)
        
        assert exc_info.value.error_code == "USED_INVITE_CODE_READONLY"
        assert "已使用的邀请码不能修改过期时间" in str(exc_info.value)
    
    def test_update_invite_code_invalid_expire_time(self, admin_service: AdminService, valid_invite_code: InviteCode, admin_user: User):
        """测试更新无效的过期时间"""
        past_time = datetime.utcnow() - timedelta(hours=1)
        request = UpdateInviteCodeRequest(expires_at=past_time)
        
        with pytest.raises(BadRequestError) as exc_info:
            admin_service.update_invite_code(valid_invite_code.id, request, admin_user.id)
        
        assert exc_info.value.error_code == "INVALID_EXPIRE_TIME"
    
    def test_update_invite_code_generates_audit_log(self, admin_service: AdminService, valid_invite_code: InviteCode, admin_user: User, db_session: Session):
        """测试更新邀请码生成审计日志"""
        initial_count = db_session.query(AuditLog).count()
        
        request = UpdateInviteCodeRequest(description="审计日志测试")
        admin_service.update_invite_code(valid_invite_code.id, request, admin_user.id)
        
        final_count = db_session.query(AuditLog).count()
        assert final_count == initial_count + 1
        
        audit_log = db_session.query(AuditLog).order_by(AuditLog.created_at.desc()).first()
        assert audit_log.action == "UPDATE_INVITE_CODE"
        assert audit_log.entity_id == valid_invite_code.id
        assert "old_data" in audit_log.details
        assert "new_data" in audit_log.details
    
    # ========== 删除邀请码测试 ==========
    
    def test_delete_invite_code_success(self, admin_service: AdminService, valid_invite_code: InviteCode, admin_user: User, db_session: Session):
        """测试成功删除未使用的邀请码"""
        code_value = valid_invite_code.code
        code_id = valid_invite_code.id
        
        result = admin_service.delete_invite_code(code_id, admin_user.id)
        
        assert "message" in result
        assert f"邀请码 {code_value} 删除成功" in result["message"]
        
        # 验证邀请码已从数据库删除
        deleted_code = db_session.query(InviteCode).filter(InviteCode.id == code_id).first()
        assert deleted_code is None
    
    def test_delete_invite_code_not_found(self, admin_service: AdminService, admin_user: User):
        """测试删除不存在的邀请码"""
        with pytest.raises(NotFoundError) as exc_info:
            admin_service.delete_invite_code(99999, admin_user.id)
        
        assert exc_info.value.error_code == "INVITE_CODE_NOT_FOUND"
    
    def test_delete_invite_code_already_used(self, admin_service: AdminService, used_invite_code: InviteCode, admin_user: User):
        """测试删除已使用的邀请码（应该失败）"""
        with pytest.raises(ConflictError) as exc_info:
            admin_service.delete_invite_code(used_invite_code.id, admin_user.id)
        
        assert exc_info.value.error_code == "INVITE_CODE_ALREADY_USED"
        assert "已被使用，无法删除" in str(exc_info.value)
    
    def test_delete_invite_code_generates_audit_log(self, admin_service: AdminService, valid_invite_code: InviteCode, admin_user: User, db_session: Session):
        """测试删除邀请码生成审计日志"""
        initial_count = db_session.query(AuditLog).count()
        
        admin_service.delete_invite_code(valid_invite_code.id, admin_user.id)
        
        final_count = db_session.query(AuditLog).count()
        assert final_count == initial_count + 1
        
        audit_log = db_session.query(AuditLog).order_by(AuditLog.created_at.desc()).first()
        assert audit_log.action == "DELETE_INVITE_CODE"
        assert audit_log.entity_id == valid_invite_code.id
        assert "code" in audit_log.details
        assert "description" in audit_log.details


class TestAdminServiceSystemConfig:
    """系统配置功能测试"""
    
    @pytest.fixture
    def admin_service(self, db_session: Session) -> AdminService:
        """创建AdminService实例"""
        return AdminService(db_session)
    
    def test_get_system_config_success(self, admin_service: AdminService, db_session: Session, admin_user: User, regular_user: User):
        """测试获取系统配置成功"""
        result = admin_service.get_system_config()
        
        assert "data" in result
        assert "message" in result
        assert result["message"] is None
        
        config = result["data"]
        
        # 验证应用信息
        assert "app_name" in config
        assert "app_version" in config
        assert "environment" in config
        
        # 验证功能开关
        assert "registration_enabled" in config
        assert "email_verification_enabled" in config
        
        # 验证系统统计
        assert "total_users" in config
        assert "total_files" in config
        assert "storage_used_mb" in config
        assert config["total_users"] >= 2  # 至少有admin_user和regular_user
        
        # 验证限制配置
        assert "max_file_size_mb" in config
        assert "max_upload_files_per_user" in config
        assert isinstance(config["max_file_size_mb"], int)
        assert isinstance(config["max_upload_files_per_user"], int)
    
    def test_get_system_config_user_count_accuracy(self, admin_service: AdminService, db_session: Session):
        """测试用户统计的准确性"""
        initial_count = db_session.query(User).count()
        
        # 创建额外用户
        test_user = User(
            username="config_test_user",
            email="config@test.com",
            password_hash="hash",
            role="user"
        )
        db_session.add(test_user)
        db_session.commit()
        
        result = admin_service.get_system_config()
        config = result["data"]
        
        assert config["total_users"] == initial_count + 1
    
    def test_get_system_config_no_sensitive_data(self, admin_service: AdminService):
        """测试系统配置不包含敏感信息"""
        result = admin_service.get_system_config()
        config = result["data"]
        
        # 确保不包含敏感配置
        sensitive_keys = [
            "secret_key", "database_url", "redis_url",
            "openai_api_key", "smtp_password", "admin_password"
        ]
        
        for key in sensitive_keys:
            assert key not in config


class TestAdminServiceAuditLog:
    """审计日志功能测试"""
    
    @pytest.fixture
    def admin_service(self, db_session: Session) -> AdminService:
        """创建AdminService实例"""
        return AdminService(db_session)
    
    @pytest.fixture
    def sample_audit_logs(self, db_session: Session, admin_user: User, regular_user: User):
        """创建测试用审计日志"""
        logs = []
        base_time = datetime.utcnow()
        
        # 创建不同类型的审计日志
        log_data = [
            {
                "user_id": admin_user.id,
                "action": "CREATE_INVITE_CODE",
                "entity_type": "invite_code",
                "entity_id": 1,
                "created_at": base_time - timedelta(hours=3)
            },
            {
                "user_id": regular_user.id,
                "action": "LOGIN",
                "entity_type": "user",
                "entity_id": regular_user.id,
                "created_at": base_time - timedelta(hours=2)
            },
            {
                "user_id": admin_user.id,
                "action": "UPDATE_INVITE_CODE",
                "entity_type": "invite_code",
                "entity_id": 1,
                "created_at": base_time - timedelta(hours=1)
            },
            {
                "user_id": None,  # 系统操作
                "action": "SYSTEM_BACKUP",
                "entity_type": "system",
                "entity_id": None,
                "created_at": base_time
            }
        ]
        
        for data in log_data:
            log = AuditLog(
                user_id=data["user_id"],
                action=data["action"],
                entity_type=data["entity_type"],
                entity_id=data["entity_id"],
                details={"test": "data"},
                ip_address="127.0.0.1",
                user_agent="pytest",
                created_at=data["created_at"]
            )
            logs.append(log)
            db_session.add(log)
        
        db_session.commit()
        return logs
    
    def test_get_audit_logs_success_no_filters(self, admin_service: AdminService, sample_audit_logs):
        """测试获取所有审计日志"""
        result = admin_service.get_audit_logs()
        
        assert "logs" in result
        assert "total" in result
        assert "pagination" in result
        
        assert result["total"] == 4
        assert len(result["logs"]) == 4
        
        # 验证按时间倒序排列
        logs = result["logs"]
        for i in range(len(logs) - 1):
            assert logs[i]["created_at"] >= logs[i + 1]["created_at"]
    
    def test_get_audit_logs_filter_by_user(self, admin_service: AdminService, sample_audit_logs, admin_user: User):
        """测试按用户ID过滤审计日志"""
        result = admin_service.get_audit_logs(user_id=admin_user.id)
        
        assert result["total"] == 2  # admin_user有2条日志
        for log in result["logs"]:
            assert log["user_id"] == admin_user.id
            assert log["username"] == admin_user.username
    
    def test_get_audit_logs_filter_by_action(self, admin_service: AdminService, sample_audit_logs):
        """测试按操作类型过滤"""
        result = admin_service.get_audit_logs(action="CREATE_INVITE_CODE")
        
        assert result["total"] == 1
        assert result["logs"][0]["action"] == "CREATE_INVITE_CODE"
    
    def test_get_audit_logs_filter_by_entity_type(self, admin_service: AdminService, sample_audit_logs):
        """测试按实体类型过滤"""
        result = admin_service.get_audit_logs(entity_type="invite_code")
        
        assert result["total"] == 2
        for log in result["logs"]:
            assert log["entity_type"] == "invite_code"
    
    def test_get_audit_logs_filter_by_date_range(self, admin_service: AdminService, sample_audit_logs):
        """测试按时间范围过滤"""
        start_date = datetime.utcnow() - timedelta(hours=2, minutes=30)
        end_date = datetime.utcnow() - timedelta(hours=0, minutes=30)
        
        result = admin_service.get_audit_logs(
            start_date=start_date,
            end_date=end_date
        )
        
        # 应该返回2条记录（LOGIN和UPDATE_INVITE_CODE）
        assert result["total"] == 2
        
        for log in result["logs"]:
            log_time = log["created_at"]
            if isinstance(log_time, str):
                log_time = datetime.fromisoformat(log_time.replace('Z', '+00:00'))
            assert start_date <= log_time <= end_date
    
    def test_get_audit_logs_invalid_date_range(self, admin_service: AdminService):
        """测试无效的时间范围"""
        start_date = datetime.utcnow()
        end_date = datetime.utcnow() - timedelta(hours=1)  # 结束时间早于开始时间
        
        with pytest.raises(BadRequestError) as exc_info:
            admin_service.get_audit_logs(start_date=start_date, end_date=end_date)
        
        assert exc_info.value.error_code == "INVALID_DATE_RANGE"
        assert "开始时间不能晚于结束时间" in str(exc_info.value)
    
    def test_get_audit_logs_date_range_too_large(self, admin_service: AdminService):
        """测试时间范围过大"""
        start_date = datetime.utcnow() - timedelta(days=400)
        end_date = datetime.utcnow()
        
        with pytest.raises(BadRequestError) as exc_info:
            admin_service.get_audit_logs(start_date=start_date, end_date=end_date)
        
        assert exc_info.value.error_code == "DATE_RANGE_TOO_LARGE"
        assert "查询时间范围不能超过365天" in str(exc_info.value)
    
    def test_get_audit_logs_pagination(self, admin_service: AdminService, sample_audit_logs):
        """测试审计日志分页"""
        # 第一页
        result = admin_service.get_audit_logs(skip=0, limit=2)
        assert result["total"] == 4
        assert len(result["logs"]) == 2
        assert result["pagination"]["has_more"] is True
        
        # 第二页
        result = admin_service.get_audit_logs(skip=2, limit=2)
        assert result["total"] == 4
        assert len(result["logs"]) == 2
        assert result["pagination"]["has_more"] is False
    
    def test_get_audit_logs_with_null_user(self, admin_service: AdminService, sample_audit_logs):
        """测试处理用户为空的审计日志"""
        result = admin_service.get_audit_logs()
        
        # 查找系统操作日志
        system_log = next(log for log in result["logs"] if log["action"] == "SYSTEM_BACKUP")
        assert system_log["user_id"] is None
        assert system_log["username"] is None
    
    def test_create_audit_log_success(self, admin_service: AdminService, admin_user: User, db_session: Session):
        """测试创建审计日志成功"""
        details = {"test_key": "test_value", "number": 123}
        
        result = admin_service.create_audit_log(
            user_id=admin_user.id,
            action="TEST_ACTION",
            entity_type="test_entity",
            entity_id=456,
            details=details,
            ip_address="192.168.1.1",
            user_agent="pytest-test-agent"
        )
        
        assert isinstance(result, AuditLog)
        assert result.user_id == admin_user.id
        assert result.action == "TEST_ACTION"
        assert result.entity_type == "test_entity"
        assert result.entity_id == 456
        assert result.details == details
        assert result.ip_address == "192.168.1.1"
        assert result.user_agent == "pytest-test-agent"
        
        # 验证数据库中确实创建了记录
        db_log = db_session.query(AuditLog).filter(AuditLog.id == result.id).first()
        assert db_log is not None
        assert db_log.action == "TEST_ACTION"
    
    def test_create_audit_log_minimal_data(self, admin_service: AdminService):
        """测试只使用最少参数创建审计日志"""
        result = admin_service.create_audit_log(
            user_id=None,
            action="MINIMAL_TEST",
            entity_type="minimal"
        )
        
        assert isinstance(result, AuditLog)
        assert result.user_id is None
        assert result.action == "MINIMAL_TEST"
        assert result.entity_type == "minimal"
        assert result.entity_id is None
        assert result.details is None
        assert result.ip_address is None
        assert result.user_agent is None


class TestAdminServicePrivateMethods:
    """私有辅助方法测试"""
    
    @pytest.fixture
    def admin_service(self, db_session: Session) -> AdminService:
        """创建AdminService实例"""
        return AdminService(db_session)
    
    def test_generate_unique_invite_code_format(self, admin_service: AdminService):
        """测试邀请码生成格式"""
        code = admin_service._generate_unique_invite_code()
        
        # 标准格式：2位字母 + 6位数字
        assert len(code) == 8
        assert code[:2].isupper()
        assert code[:2].isalpha()
        assert code[2:].isdigit()
    
    def test_generate_unique_invite_code_uniqueness(self, admin_service: AdminService):
        """测试邀请码生成唯一性"""
        codes = set()
        
        for _ in range(10):
            code = admin_service._generate_unique_invite_code()
            assert code not in codes
            codes.add(code)
    
    def test_get_invite_code_with_user_info_success(self, admin_service: AdminService, db_session: Session, admin_user: User, regular_user: User):
        """测试获取包含用户信息的邀请码"""
        # 创建已使用的邀请码
        invite_code = InviteCode(
            code="USERINFO1",
            description="用户信息测试",
            is_used=True,
            used_by=regular_user.id,
            used_at=datetime.utcnow(),
            created_by=admin_user.id
        )
        db_session.add(invite_code)
        db_session.commit()
        db_session.refresh(invite_code)
        
        result = admin_service._get_invite_code_with_user_info(invite_code.id)
        
        assert result is not None
        assert result["id"] == invite_code.id
        assert result["code"] == "USERINFO1"
        assert result["description"] == "用户信息测试"
        assert result["is_used"] is True
        assert result["used_by"] == regular_user.id
        assert result["used_by_username"] == regular_user.username
        assert result["created_by"] == admin_user.id
        assert result["created_by_username"] == admin_user.username
    
    def test_get_invite_code_with_user_info_not_found(self, admin_service: AdminService):
        """测试获取不存在的邀请码用户信息"""
        result = admin_service._get_invite_code_with_user_info(99999)
        assert result is None
    
    def test_get_invite_code_with_user_info_unused_code(self, admin_service: AdminService, db_session: Session, admin_user: User):
        """测试获取未使用邀请码的用户信息"""
        invite_code = InviteCode(
            code="UNUSED02",
            description="未使用测试",
            created_by=admin_user.id
        )
        db_session.add(invite_code)
        db_session.commit()
        db_session.refresh(invite_code)
        
        result = admin_service._get_invite_code_with_user_info(invite_code.id)
        
        assert result is not None
        assert result["is_used"] is False
        assert result["used_by"] is None
        assert result["used_by_username"] is None
        assert result["used_at"] is None
        assert result["created_by_username"] == admin_user.username


class TestAdminServiceExceptionCoverage:
    """异常覆盖测试 - 确保所有声明的异常都有对应测试"""
    
    def test_method_exceptions_coverage(self):
        """验证METHOD_EXCEPTIONS声明的完整性"""
        expected_methods = {
            'create_invite_code', 'get_invite_codes', 'get_invite_code',
            'update_invite_code', 'delete_invite_code', 'get_system_config',
            'get_audit_logs', 'create_audit_log'
        }
        
        actual_methods = set(AdminService.METHOD_EXCEPTIONS.keys())
        assert actual_methods == expected_methods
    
    def test_create_invite_code_exceptions(self):
        """验证create_invite_code方法的异常声明"""
        exceptions = AdminService.METHOD_EXCEPTIONS['create_invite_code']
        assert BadRequestError in exceptions
        assert ConflictError in exceptions
        assert len(exceptions) == 2
    
    def test_update_invite_code_exceptions(self):
        """验证update_invite_code方法的异常声明"""
        exceptions = AdminService.METHOD_EXCEPTIONS['update_invite_code']
        assert NotFoundError in exceptions
        assert BadRequestError in exceptions
        assert len(exceptions) == 2
    
    def test_delete_invite_code_exceptions(self):
        """验证delete_invite_code方法的异常声明"""
        exceptions = AdminService.METHOD_EXCEPTIONS['delete_invite_code']
        assert NotFoundError in exceptions
        assert ConflictError in exceptions
        assert len(exceptions) == 2
    
    def test_get_audit_logs_exceptions(self):
        """验证get_audit_logs方法的异常声明"""
        exceptions = AdminService.METHOD_EXCEPTIONS['get_audit_logs']
        assert BadRequestError in exceptions
        assert len(exceptions) == 1
    
    def test_no_exception_methods(self):
        """验证声明无异常的方法"""
        no_exception_methods = [
            'get_invite_codes', 'get_system_config', 'create_audit_log'
        ]
        
        for method in no_exception_methods:
            exceptions = AdminService.METHOD_EXCEPTIONS[method]
            assert len(exceptions) == 0


class TestAdminServiceIntegration:
    """集成测试 - 测试方法间的交互"""
    
    @pytest.fixture
    def admin_service(self, db_session: Session) -> AdminService:
        """创建AdminService实例"""
        return AdminService(db_session)
    
    def test_invite_code_lifecycle(self, admin_service: AdminService, admin_user: User, regular_user: User, db_session: Session):
        """测试邀请码完整生命周期"""
        # 1. 创建邀请码
        create_request = CreateInviteCodeRequest(
            description="生命周期测试",
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        create_result = admin_service.create_invite_code(create_request, admin_user.id)
        invite_code_id = create_result["invite_code"]["id"]
        
        # 2. 查询单个邀请码
        get_result = admin_service.get_invite_code(invite_code_id)
        assert get_result["invite_code"]["description"] == "生命周期测试"
        
        # 3. 更新邀请码
        update_request = UpdateInviteCodeRequest(
            description="更新后的生命周期测试"
        )
        
        update_result = admin_service.update_invite_code(invite_code_id, update_request, admin_user.id)
        assert update_result["invite_code"]["description"] == "更新后的生命周期测试"
        
        # 4. 在列表中查看邀请码
        list_result = admin_service.get_invite_codes()
        found_code = next(
            (code for code in list_result["invite_codes"] if code["id"] == invite_code_id),
            None
        )
        assert found_code is not None
        assert found_code["description"] == "更新后的生命周期测试"
        
        # 5. 删除邀请码
        delete_result = admin_service.delete_invite_code(invite_code_id, admin_user.id)
        assert "删除成功" in delete_result["message"]
        
        # 6. 验证删除后无法查询
        with pytest.raises(NotFoundError):
            admin_service.get_invite_code(invite_code_id)
    
    def test_audit_log_generation_throughout_operations(self, admin_service: AdminService, admin_user: User, db_session: Session):
        """测试操作过程中审计日志的生成"""
        initial_count = db_session.query(AuditLog).count()
        
        # 执行一系列操作
        create_request = CreateInviteCodeRequest(description="审计测试")
        create_result = admin_service.create_invite_code(create_request, admin_user.id)
        invite_code_id = create_result["invite_code"]["id"]
        
        update_request = UpdateInviteCodeRequest(description="审计测试更新")
        admin_service.update_invite_code(invite_code_id, update_request, admin_user.id)
        
        admin_service.delete_invite_code(invite_code_id, admin_user.id)
        
        # 验证审计日志增加了3条
        final_count = db_session.query(AuditLog).count()
        assert final_count == initial_count + 3
        
        # 验证日志内容
        recent_logs = (
            db_session.query(AuditLog)
            .filter(AuditLog.user_id == admin_user.id)
            .order_by(AuditLog.created_at.desc())
            .limit(3)
            .all()
        )
        
        actions = [log.action for log in recent_logs]
        assert "DELETE_INVITE_CODE" in actions
        assert "UPDATE_INVITE_CODE" in actions
        assert "CREATE_INVITE_CODE" in actions