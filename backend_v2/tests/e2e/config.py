"""
E2E测试配置
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class TestConfig:
    """测试配置类"""
    
    # API服务配置
    base_url: str = "http://localhost:8001"
    timeout: int = 30
    debug: bool = False
    
    # 测试数据配置
    test_data_dir: str = "tests/e2e/test_data"
    test_files_dir: str = "tests/e2e/test_files"
    
    # 测试用户配置
    admin_username: str = "testadmin"
    admin_email: str = "test@icu.584743.xyz"
    admin_password: str = "admin123456"
    
    test_user_prefix: str = "testuser"
    test_email_domain: str = "test.com"
    test_password: str = "TestPass123!"
    
    # 测试数据库配置（如果需要）
    test_db_url: Optional[str] = None
    
    # 清理配置
    cleanup_after_test: bool = True
    keep_test_data: bool = False
    
    @classmethod
    def from_env(cls) -> 'TestConfig':
        """从环境变量创建配置"""
        return cls(
            base_url=os.getenv('TEST_BASE_URL', 'http://localhost:8001'),
            timeout=int(os.getenv('TEST_TIMEOUT', '30')),
            debug=os.getenv('TEST_DEBUG', 'false').lower() == 'true',
            
            test_data_dir=os.getenv('TEST_DATA_DIR', 'tests/e2e/test_data'),
            test_files_dir=os.getenv('TEST_FILES_DIR', 'tests/e2e/test_files'),
            
            admin_username=os.getenv('TEST_ADMIN_USERNAME', 'testadmin'),
            admin_email=os.getenv('TEST_ADMIN_EMAIL', 'admin@test.com'),
            admin_password=os.getenv('TEST_ADMIN_PASSWORD', 'admin123456'),
            
            test_user_prefix=os.getenv('TEST_USER_PREFIX', 'testuser'),
            test_email_domain=os.getenv('TEST_EMAIL_DOMAIN', 'test.com'),
            test_password=os.getenv('TEST_PASSWORD', 'TestPass123!'),
            
            test_db_url=os.getenv('TEST_DATABASE_URL'),
            
            cleanup_after_test=os.getenv('TEST_CLEANUP', 'true').lower() == 'true',
            keep_test_data=os.getenv('TEST_KEEP_DATA', 'false').lower() == 'true',
        )


# 全局配置实例
config = TestConfig.from_env()