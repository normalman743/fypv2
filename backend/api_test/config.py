"""
API测试配置文件
"""

# API基础配置
BASE_URL = "http://127.0.0.1:8000"
API_VERSION = "v1"
API_BASE = f"{BASE_URL}/api/{API_VERSION}"


# 测试用户配置
TEST_USER = {
    "username": "api_test_user_1751867530",
    "email": "api_test@example.com",
    "password": "testpass123",
    "invite_code": "DEMO2025"  # 需要先确保这个邀请码存在
}

# 管理员配置
ADMIN_USER = {
    "username": "admin",
    "password": "admin123"
}

# 测试数据
TEST_SEMESTER = {
    "name": "2025测试学期",
    "code": "TEST2025",
    "start_date": "2025-01-01T00:00:00",
    "end_date": "2025-06-30T00:00:00"
}

TEST_COURSE = {
    "name": "API测试课程",
    "code": "API001",
    "description": "用于API测试的课程"
}

TEST_FOLDER = {
    "name": "测试文件夹",
    "folder_type": "lecture"
}

# HTTP请求配置
TIMEOUT = 30
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}