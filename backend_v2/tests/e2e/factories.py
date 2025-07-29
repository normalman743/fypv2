"""
测试数据工厂
用于生成各种测试数据
"""
import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from faker import Faker

fake = Faker('zh_CN')


class TestDataFactory:
    """测试数据工厂类"""
    
    @staticmethod
    def random_string(length: int = 8) -> str:
        """生成随机字符串"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    @staticmethod
    def random_email(domain: str = "test.com") -> str:
        """生成随机邮箱"""
        username = TestDataFactory.random_string(8).lower()
        return f"{username}@{domain}"
    
    @staticmethod
    def random_username(prefix: str = "testuser") -> str:
        """生成随机用户名"""
        return f"{prefix}_{TestDataFactory.random_string(6).lower()}"
    
    @staticmethod
    def random_phone() -> str:
        """生成随机手机号"""
        return f"1{random.randint(3, 9)}{random.randint(0, 9):08d}"
    
    @staticmethod
    def future_datetime(days: int = 30) -> str:
        """生成未来日期时间"""
        future_date = datetime.utcnow() + timedelta(days=days)
        return future_date.strftime("%Y-%m-%dT%H:%M:%S")
    
    @staticmethod
    def past_datetime(days: int = 30) -> str:
        """生成过去日期时间"""
        past_date = datetime.utcnow() - timedelta(days=days)
        return past_date.strftime("%Y-%m-%dT%H:%M:%S")


class UserDataFactory:
    """用户数据工厂"""
    
    @classmethod
    def create_user_data(cls, **overrides) -> Dict[str, Any]:
        """创建用户注册数据"""
        data = {
            "username": TestDataFactory.random_username(),
            "email": TestDataFactory.random_email(),
            "password": "TestPass123!",
            "real_name": fake.name(),
            "phone": TestDataFactory.random_phone()
        }
        data.update(overrides)
        return data
    
    @classmethod
    def create_admin_data(cls, **overrides) -> Dict[str, Any]:
        """创建管理员数据"""
        data = cls.create_user_data()
        data.update({
            "username": f"admin_{TestDataFactory.random_string(4)}",
            "email": f"admin_{TestDataFactory.random_string(4)}@test.com",
            "real_name": "测试管理员"
        })
        data.update(overrides)
        return data
    
    @classmethod
    def create_login_data(cls, username: str, password: str = "TestPass123!") -> Dict[str, Any]:
        """创建登录数据"""
        return {
            "identifier": username,
            "password": password
        }


class AdminDataFactory:
    """管理员数据工厂"""
    
    @classmethod
    def create_invite_code_data(cls, **overrides) -> Dict[str, Any]:
        """创建邀请码数据"""
        data = {
            "description": f"测试邀请码 - {TestDataFactory.random_string(6)}",
            "expires_at": TestDataFactory.future_datetime(7)  # 7天后过期
        }
        data.update(overrides)
        return data


class CourseDataFactory:
    """课程相关数据工厂"""
    
    @classmethod
    def create_semester_data(cls, **overrides) -> Dict[str, Any]:
        """创建学期数据"""
        year = datetime.now().year
        season = random.choice(['春', '夏', '秋', '冬'])
        
        data = {
            "name": f"{year}年{season}季学期",
            "code": f"{year}{season[0]}",
            "start_date": "2024-02-01",
            "end_date": "2024-06-30",
            "description": f"{year}年{season}季学期测试数据"
        }
        data.update(overrides)
        return data
    
    @classmethod
    def create_course_data(cls, semester_id: int, **overrides) -> Dict[str, Any]:
        """创建课程数据"""
        subjects = ['Python编程', 'Java基础', '数据结构', '算法设计', '数据库原理', '计算机网络']
        subject = random.choice(subjects)
        code_num = random.randint(100, 999)
        
        data = {
            "name": subject,
            "code": f"CS{code_num}",
            "semester_id": semester_id,
            "description": f"{subject}课程测试数据",
            "credits": random.randint(2, 4)
        }
        data.update(overrides)
        return data


class StorageDataFactory:
    """存储相关数据工厂"""
    
    @classmethod
    def create_folder_data(cls, **overrides) -> Dict[str, Any]:
        """创建文件夹数据"""
        folder_types = ["outline", "tutorial", "lecture", "exam", "assignment", "others"]
        folder_names = ["课件", "作业", "考试资料", "参考资料", "实验指导", "其他"]
        
        folder_type = random.choice(folder_types)
        folder_name = random.choice(folder_names)
        
        data = {
            "name": f"{folder_name}_{TestDataFactory.random_string(4)}",
            "folder_type": folder_type
        }
        data.update(overrides)
        return data


class ChatDataFactory:
    """聊天相关数据工厂"""
    
    @classmethod
    def create_chat_data(cls, course_id: Optional[int] = None, **overrides) -> Dict[str, Any]:
        """创建聊天数据"""
        chat_types = ["general", "course", "qa"]
        ai_models = ["gpt-3.5-turbo", "gpt-4"]
        context_modes = ["default", "focused", "creative"]
        
        titles = ["Python学习助手", "算法问题讨论", "数据库查询帮助", "编程疑难解答"]
        
        data = {
            "title": random.choice(titles),
            "chat_type": random.choice(chat_types),
            "ai_model": random.choice(ai_models),
            "rag_enabled": True,
            "context_mode": random.choice(context_modes)
        }
        
        if course_id:
            data["course_id"] = course_id
            data["chat_type"] = "course"
        
        data.update(overrides)
        return data
    
    @classmethod
    def create_message_data(cls, **overrides) -> Dict[str, Any]:
        """创建消息数据"""
        questions = [
            "什么是Python?",
            "如何实现快速排序?",
            "数据库索引的作用是什么?",
            "解释面向对象编程的概念",
            "什么是递归算法?"
        ]
        
        data = {
            "content": random.choice(questions)
        }
        data.update(overrides)
        return data


class AIDataFactory:
    """AI相关数据工厂"""
    
    @classmethod
    def create_ai_chat_data(cls, **overrides) -> Dict[str, Any]:
        """创建AI对话数据"""
        messages = [
            "解释Python中的装饰器概念",
            "如何优化SQL查询性能?",
            "什么是机器学习?",
            "解释RESTful API设计原则",
            "如何处理并发编程?"
        ]
        
        data = {
            "message": random.choice(messages),
            "ai_model": "gpt-3.5-turbo",
            "chat_type": "general",
            "rag_enabled": True,
            "context_mode": "default"
        }
        data.update(overrides)
        return data


# 便利函数
def create_test_user(**overrides) -> Dict[str, Any]:
    """创建测试用户数据"""
    return UserDataFactory.create_user_data(**overrides)


def create_test_admin(**overrides) -> Dict[str, Any]:
    """创建测试管理员数据"""
    return UserDataFactory.create_admin_data(**overrides)


def create_test_semester(**overrides) -> Dict[str, Any]:
    """创建测试学期数据"""
    return CourseDataFactory.create_semester_data(**overrides)


def create_test_course(semester_id: int, **overrides) -> Dict[str, Any]:
    """创建测试课程数据"""
    return CourseDataFactory.create_course_data(semester_id, **overrides)


def create_test_invite_code(**overrides) -> Dict[str, Any]:
    """创建测试邀请码数据"""
    return AdminDataFactory.create_invite_code_data(**overrides)