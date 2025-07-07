#!/usr/bin/env python3
"""
本地数据库初始化脚本
为本地开发环境创建数据库和基础数据
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.semester import Semester
from app.models.course import Course
from app.models.folder import Folder
from app.models.chat import Chat
from app.models.message import Message
from app.models.invite_code import InviteCode
from app.core.security import get_password_hash
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import string

def generate_invite_code(length=8):
    """生成随机邀请码"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def init_local_database():
    """初始化本地数据库"""
    print("🚀 初始化本地数据库...")
    
    # 创建所有表
    print("📋 创建数据库表...")
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    try:
        # 检查是否已有数据
        if db.query(User).first():
            print("ℹ️ 数据库已有数据，跳过初始化")
            return True
        
        print("📝 创建基础数据...")
        
        # 1. 创建管理员用户
        print("👑 创建管理员用户...")
        admin_user = User(
            username="admin",
            email="admin@localhost.com",
            password_hash=get_password_hash("admin123"),
            role="admin",
            balance=1000.00,
            total_spent=0.00,
            preferred_language="zh_CN",
            preferred_theme="light",
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"✅ 管理员用户创建成功: {admin_user.username}")
        
        # 2. 创建邀请码
        print("🎫 创建邀请码...")
        invite_codes_data = [
            {"code": "LOCAL2025", "description": "本地开发邀请码", "days": 365},
            {"code": "TEST2025", "description": "测试邀请码", "days": 365},
            {"code": "DEV2025", "description": "开发者邀请码", "days": 365},
        ]
        
        now = datetime.now()
        for code_data in invite_codes_data:
            invite_code = InviteCode(
                code=code_data["code"],
                description=code_data["description"],
                is_used=False,
                expires_at=now + timedelta(days=code_data["days"]),
                is_active=True,
                created_by=admin_user.id
            )
            db.add(invite_code)
        
        db.commit()
        print(f"✅ 创建了 {len(invite_codes_data)} 个邀请码")
        
        # 3. 创建测试用户
        print("👥 创建测试用户...")
        # 使用第一个邀请码
        first_code = db.query(InviteCode).filter(InviteCode.code == "LOCAL2025").first()
        
        test_user = User(
            username="testuser",
            email="test@localhost.com",
            password_hash=get_password_hash("test123"),
            role="user",
            balance=100.00,
            total_spent=0.00,
            preferred_language="zh_CN",
            preferred_theme="light",
            is_active=True
        )
        db.add(test_user)
        
        # 标记邀请码为已使用
        first_code.is_used = True
        first_code.used_by = test_user.id
        first_code.used_at = now
        
        db.commit()
        db.refresh(test_user)
        print(f"✅ 测试用户创建成功: {test_user.username}")
        
        # 4. 创建学期
        print("📅 创建学期...")
        semesters_data = [
            {
                "name": "2025年春季学期",
                "code": "2025SPRING",
                "start_date": datetime(2025, 2, 15),
                "end_date": datetime(2025, 6, 30)
            },
            {
                "name": "2025年秋季学期", 
                "code": "2025FALL",
                "start_date": datetime(2025, 9, 1),
                "end_date": datetime(2026, 1, 15)
            }
        ]
        
        semesters = []
        for sem_data in semesters_data:
            semester = Semester(
                name=sem_data["name"],
                code=sem_data["code"],
                start_date=sem_data["start_date"],
                end_date=sem_data["end_date"],
                is_active=True
            )
            db.add(semester)
            semesters.append(semester)
        
        db.commit()
        print(f"✅ 创建了 {len(semesters)} 个学期")
        
        # 5. 创建课程
        print("📚 创建课程...")
        courses_data = [
            {"name": "Python编程基础", "code": "CS101", "description": "学习Python编程语言基础"},
            {"name": "数据结构与算法", "code": "CS102", "description": "学习基本数据结构和算法"},
            {"name": "Web开发实践", "code": "CS103", "description": "学习Web应用程序开发"},
        ]
        
        courses = []
        for course_data in courses_data:
            course = Course(
                name=course_data["name"],
                code=course_data["code"],
                description=course_data["description"],
                semester_id=semesters[0].id,  # 使用第一个学期
                user_id=test_user.id
            )
            db.add(course)
            courses.append(course)
        
        db.commit()
        print(f"✅ 创建了 {len(courses)} 个课程")
        
        # 6. 为每个课程创建文件夹
        print("📁 创建文件夹...")
        folder_types = ["lecture", "tutorial", "exam", "assignment", "outline", "others"]
        folders = []
        
        for course in courses:
            for i, folder_type in enumerate(folder_types):
                folder = Folder(
                    name=f"{folder_type.title()}",
                    folder_type=folder_type,
                    course_id=course.id,
                    is_default=(i == 0)  # 第一个文件夹设为默认
                )
                db.add(folder)
                folders.append(folder)
        
        db.commit()
        print(f"✅ 创建了 {len(folders)} 个文件夹")
        
        # 7. 创建示例聊天
        print("💬 创建示例聊天...")
        chats = []
        
        # 通用聊天
        general_chat = Chat(
            title="AI学习助手",
            chat_type="general",
            user_id=test_user.id,
            custom_prompt="你是一个友好的AI学习助手，帮助学生解答学习问题。",
            rag_enabled=True,
            max_context_length=4000
        )
        db.add(general_chat)
        chats.append(general_chat)
        
        # 课程聊天
        for course in courses[:2]:  # 为前两个课程创建聊天
            course_chat = Chat(
                title=f"{course.name} - 课程助教",
                chat_type="course",
                course_id=course.id,
                user_id=test_user.id,
                custom_prompt=f"你是{course.name}的专业助教，帮助学生理解课程内容。",
                rag_enabled=True,
                max_context_length=6000
            )
            db.add(course_chat)
            chats.append(course_chat)
        
        db.commit()
        print(f"✅ 创建了 {len(chats)} 个聊天")
        
        # 8. 创建示例消息
        print("📝 创建示例消息...")
        messages = []
        
        # 为第一个聊天创建示例对话
        sample_messages = [
            {"role": "user", "content": "你好，我想学习Python编程，有什么建议吗？"},
            {"role": "assistant", "content": "你好！很高兴你想学习Python编程。Python是一门非常适合初学者的编程语言，语法简洁易懂。我建议你从以下几个方面开始：\n\n1. 学习基本语法：变量、数据类型、条件语句、循环\n2. 练习编写小程序：计算器、猜数字游戏等\n3. 学习函数和模块的使用\n4. 了解面向对象编程\n\n有什么具体问题可以随时问我！", "model": "gpt-3.5-turbo", "tokens": 180, "cost": 0.00036, "time": 1500}
        ]
        
        for msg_data in sample_messages:
            message = Message(
                chat_id=chats[0].id,
                content=msg_data["content"],
                role=msg_data["role"],
                model_name=msg_data.get("model"),
                tokens_used=msg_data.get("tokens"),
                cost=msg_data.get("cost"),
                response_time_ms=msg_data.get("time")
            )
            db.add(message)
            messages.append(message)
        
        db.commit()
        print(f"✅ 创建了 {len(messages)} 条示例消息")
        
        print("\n🎉 本地数据库初始化完成！")
        print("\n📋 本地开发数据摘要:")
        print(f"👑 管理员: admin (密码: admin123)")
        print(f"👤 测试用户: testuser (密码: test123)")
        print(f"🎫 邀请码: LOCAL2025, TEST2025, DEV2025")
        print(f"📅 学期: {len(semesters)} 个")
        print(f"📚 课程: {len(courses)} 个")
        print(f"📁 文件夹: {len(folders)} 个")
        print(f"💬 聊天: {len(chats)} 个")
        print(f"📝 消息: {len(messages)} 条")
        
        return True
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

def check_local_database():
    """检查本地数据库状态"""
    print("🔍 检查本地数据库状态...")
    
    db: Session = SessionLocal()
    try:
        users_count = db.query(User).count()
        admin_count = db.query(User).filter(User.role == "admin").count()
        courses_count = db.query(Course).count()
        chats_count = db.query(Chat).count()
        
        print(f"📊 本地数据库状态:")
        print(f"  👥 用户总数: {users_count}")
        print(f"  👑 管理员: {admin_count}")
        print(f"  📚 课程: {courses_count}")
        print(f"  💬 聊天: {chats_count}")
        
        # 检查登录凭据
        admin = db.query(User).filter(User.username == "admin").first()
        testuser = db.query(User).filter(User.username == "testuser").first()
        
        print(f"\n🔑 登录信息:")
        print(f"  👑 管理员: {'✅ 存在' if admin else '❌ 缺失'}")
        print(f"  👤 测试用户: {'✅ 存在' if testuser else '❌ 缺失'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="本地数据库管理脚本")
    parser.add_argument("action", choices=["init", "check"], 
                       help="操作类型: init(初始化), check(检查)")
    
    args = parser.parse_args()
    
    if args.action == "init":
        init_local_database()
    elif args.action == "check":
        check_local_database()