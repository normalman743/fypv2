"""
测试数据初始化脚本
为API测试创建完整的测试数据集
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.semester import Semester
from app.models.course import Course
from app.models.folder import Folder
from app.models.file import File
from app.models.chat import Chat
from app.models.message import Message
from app.models.invite_code import InviteCode
from app.core.security import get_password_hash
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import string

def generate_invite_code(length=10):
    """生成随机邀请码"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def init_test_data():
    """初始化完整的测试数据"""
    print("🚀 开始初始化测试数据...")
    
    # 创建所有表
    print("📋 创建数据库表...")
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    try:
        # 清空现有数据（可选）
        print("🧹 清理现有测试数据...")
        # 注意删除顺序，避免外键约束冲突
        db.query(Message).delete()
        db.query(Chat).delete()
        db.query(File).delete()
        db.query(Folder).delete()
        db.query(Course).delete()
        db.query(Semester).delete()
        db.query(InviteCode).delete()
        # 只删除测试用户，保留可能存在的管理员
        db.query(User).filter(User.username.like('test%')).delete()
        db.query(User).filter(User.username.like('api_test%')).delete()
        db.commit()
        
        # 1. 创建管理员用户
        print("👑 创建管理员用户...")
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@campus-llm.com",
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
        else:
            print(f"ℹ️ 管理员用户已存在: {admin_user.username}")
        
        # 2. 创建有效的邀请码
        print("🎫 创建测试邀请码...")
        now = datetime.now()
        
        # 创建多个有效的邀请码供测试使用
        invite_codes_data = [
            {"code": "TEST2025", "description": "主要测试邀请码", "days": 365},
            {"code": "INVITE2025", "description": "备用测试邀请码", "days": 365},
            {"code": "API_TEST", "description": "API自动化测试专用", "days": 30},
            {"code": "DEMO2025", "description": "演示用邀请码", "days": 90},
        ]
        
        for i in range(10):  # 创建10个随机邀请码
            invite_codes_data.append({
                "code": f"AUTO_{generate_invite_code(8)}",
                "description": f"自动生成邀请码 #{i+1}",
                "days": 180
            })
        
        created_codes = []
        for code_data in invite_codes_data:
            existing_code = db.query(InviteCode).filter(InviteCode.code == code_data["code"]).first()
            if not existing_code:
                invite_code = InviteCode(
                    code=code_data["code"],
                    description=code_data["description"],
                    is_used=False,
                    expires_at=now + timedelta(days=code_data["days"]),
                    is_active=True,
                    created_by=admin_user.id
                )
                db.add(invite_code)
                created_codes.append(code_data["code"])
        
        db.commit()
        print(f"✅ 创建了 {len(created_codes)} 个新邀请码")
        print(f"🔑 主要测试邀请码: TEST2025, INVITE2025")
        
        # 3. 创建测试用户
        print("👥 创建测试用户...")
        test_users_data = [
            {"username": "testuser", "email": "test@example.com", "role": "user"},
            {"username": "testuser2", "email": "test2@example.com", "role": "user"},
            {"username": "api_test_user", "email": "api_test@example.com", "role": "user"},
            {"username": "demo_user", "email": "demo@example.com", "role": "user"},
        ]
        
        test_users = []
        for user_data in test_users_data:
            existing_user = db.query(User).filter(User.username == user_data["username"]).first()
            if not existing_user:
                # 使用第一个可用的邀请码
                available_code = db.query(InviteCode).filter(
                    InviteCode.is_used == False,
                    InviteCode.is_active == True,
                    InviteCode.expires_at > now
                ).first()
                
                if available_code:
                    user = User(
                        username=user_data["username"],
                        email=user_data["email"],
                        password_hash=get_password_hash("testpass123"),
                        role=user_data["role"],
                        balance=100.00,
                        total_spent=0.00,
                        preferred_language="zh_CN",
                        preferred_theme="light",
                        is_active=True
                    )
                    db.add(user)
                    
                    # 标记邀请码为已使用
                    available_code.is_used = True
                    available_code.used_by = user.id  # 这里先设置，commit后会更新
                    available_code.used_at = now
                    
                    test_users.append(user)
            else:
                test_users.append(existing_user)
        
        db.commit()
        
        # 更新用户ID到邀请码
        for user in test_users:
            if hasattr(user, 'id'):
                db.refresh(user)
        
        print(f"✅ 创建了 {len([u for u in test_users if u.id])} 个测试用户")
        
        # 4. 创建测试学期
        print("📅 创建测试学期...")
        semesters_data = [
            {
                "name": "2024-2025第一学期",
                "code": "2024S1", 
                "start_date": datetime(2024, 9, 1),
                "end_date": datetime(2025, 1, 15)
            },
            {
                "name": "2024-2025第二学期",
                "code": "2024S2",
                "start_date": datetime(2025, 2, 15),
                "end_date": datetime(2025, 6, 30)
            },
            {
                "name": "2025测试学期",
                "code": "TEST2025",
                "start_date": datetime(2025, 1, 1),
                "end_date": datetime(2025, 12, 31)
            }
        ]
        
        semesters = []
        for sem_data in semesters_data:
            existing_semester = db.query(Semester).filter(Semester.code == sem_data["code"]).first()
            if not existing_semester:
                semester = Semester(
                    name=sem_data["name"],
                    code=sem_data["code"],
                    start_date=sem_data["start_date"],
                    end_date=sem_data["end_date"],
                    is_active=True
                )
                db.add(semester)
                semesters.append(semester)
            else:
                semesters.append(existing_semester)
        
        db.commit()
        print(f"✅ 创建了 {len(semesters)} 个学期")
        
        # 5. 创建测试课程
        print("📚 创建测试课程...")
        if test_users and semesters:
            courses_data = [
                {"name": "数据结构与算法", "code": "CS101", "description": "计算机科学基础课程"},
                {"name": "机器学习导论", "code": "ML101", "description": "机器学习入门课程"},
                {"name": "深度学习", "code": "DL101", "description": "深度学习理论与实践"},
                {"name": "自然语言处理", "code": "NLP101", "description": "NLP技术与应用"},
                {"name": "API测试课程", "code": "API001", "description": "用于API测试的课程"},
            ]
            
            courses = []
            for course_data in courses_data:
                for user in test_users[:2]:  # 为前两个用户创建课程
                    for semester in semesters[:2]:  # 在前两个学期中创建
                        course_code = f"{course_data['code']}_{user.username[:4]}_{semester.code}"
                        existing_course = db.query(Course).filter(
                            Course.code == course_code,
                            Course.semester_id == semester.id,
                            Course.user_id == user.id
                        ).first()
                        
                        if not existing_course:
                            course = Course(
                                name=f"{course_data['name']} ({user.username})",
                                code=course_code,
                                description=course_data["description"],
                                semester_id=semester.id,
                                user_id=user.id
                            )
                            db.add(course)
                            courses.append(course)
            
            db.commit()
            print(f"✅ 创建了 {len(courses)} 个课程")
            
            # 6. 创建测试文件夹
            print("📁 创建测试文件夹...")
            if courses:
                folder_types = ["lecture", "tutorial", "exam", "assignment", "outline", "others"]
                folders = []
                
                for course in courses[:5]:  # 为前5个课程创建文件夹
                    for i, folder_type in enumerate(folder_types):
                        folder = Folder(
                            name=f"{folder_type.title()}文件夹",
                            folder_type=folder_type,
                            course_id=course.id,
                            is_default=(i == 0)  # 第一个文件夹设为默认
                        )
                        db.add(folder)
                        folders.append(folder)
                
                db.commit()
                print(f"✅ 创建了 {len(folders)} 个文件夹")
                
                # 7. 创建测试聊天
                print("💬 创建测试聊天...")
                chats = []
                
                for user in test_users[:2]:
                    # 创建通用聊天
                    general_chat = Chat(
                        title="通用AI助手聊天",
                        chat_type="general",
                        user_id=user.id,
                        custom_prompt="你是一个友好的AI助手，请帮助用户解答问题。",
                        rag_enabled=True,
                        max_context_length=4000
                    )
                    db.add(general_chat)
                    chats.append(general_chat)
                    
                    # 为每个课程创建专门的聊天
                    user_courses = [c for c in courses if c.user_id == user.id]
                    for course in user_courses[:2]:  # 限制数量
                        course_chat = Chat(
                            title=f"{course.name} - 课程助教",
                            chat_type="course",
                            course_id=course.id,
                            user_id=user.id,
                            custom_prompt=f"你是{course.name}的专业助教，请基于课程资料回答学生问题。",
                            rag_enabled=True,
                            max_context_length=6000
                        )
                        db.add(course_chat)
                        chats.append(course_chat)
                
                db.commit()
                print(f"✅ 创建了 {len(chats)} 个聊天")
                
                # 8. 创建测试消息
                print("📝 创建测试消息...")
                messages = []
                
                sample_conversations = [
                    [
                        {"role": "user", "content": "你好，请介绍一下你自己。"},
                        {"role": "assistant", "content": "你好！我是你的AI学习助手，我可以帮助你解答学习中的各种问题，包括课程内容、作业指导、学习方法等。有什么我可以帮助你的吗？", "model": "gpt-3.5-turbo", "tokens": 150, "cost": 0.0003, "time": 1200},
                    ],
                    [
                        {"role": "user", "content": "什么是机器学习？"},
                        {"role": "assistant", "content": "机器学习是人工智能的一个分支，它通过算法让计算机系统能够从数据中自动学习和改进，而无需被明确编程。主要包括监督学习、无监督学习和强化学习三种类型。", "model": "gpt-3.5-turbo", "tokens": 200, "cost": 0.0004, "time": 1500},
                    ],
                    [
                        {"role": "user", "content": "请解释一下数据结构中的栈和队列的区别。"},
                        {"role": "assistant", "content": "栈(Stack)和队列(Queue)是两种重要的线性数据结构：\n\n**栈(Stack)**：\n- 遵循LIFO(Last In First Out)原则\n- 只能在一端进行插入和删除操作\n- 主要操作：push(入栈)、pop(出栈)、top(查看栈顶)\n\n**队列(Queue)**：\n- 遵循FIFO(First In First Out)原则\n- 在两端进行操作：一端插入，另一端删除\n- 主要操作：enqueue(入队)、dequeue(出队)、front(查看队头)", "model": "gpt-4", "tokens": 350, "cost": 0.0105, "time": 2000},
                    ]
                ]
                
                for chat in chats[:3]:  # 为前3个聊天创建消息
                    conversation = random.choice(sample_conversations)
                    for msg_data in conversation:
                        message = Message(
                            chat_id=chat.id,
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
                print(f"✅ 创建了 {len(messages)} 条测试消息")
        
        # 9. 创建一些已使用和过期的邀请码
        print("🎫 创建各种状态的邀请码用于测试...")
        
        # 已使用的邀请码
        used_code = InviteCode(
            code="USED2025",
            description="已使用的测试邀请码",
            is_used=True,
            used_by=test_users[0].id if test_users else admin_user.id,
            used_at=now - timedelta(days=10),
            expires_at=now + timedelta(days=100),
            is_active=True,
            created_by=admin_user.id
        )
        db.add(used_code)
        
        # 过期的邀请码
        expired_code = InviteCode(
            code="EXPIRED2024",
            description="过期的测试邀请码",
            is_used=False,
            expires_at=now - timedelta(days=30),
            is_active=True,
            created_by=admin_user.id
        )
        db.add(expired_code)
        
        # 停用的邀请码
        inactive_code = InviteCode(
            code="INACTIVE2025",
            description="停用的测试邀请码", 
            is_used=False,
            expires_at=now + timedelta(days=100),
            is_active=False,
            created_by=admin_user.id
        )
        db.add(inactive_code)
        
        db.commit()
        print("✅ 创建了各种状态的邀请码用于测试")
        
        print("\n🎉 测试数据初始化完成！")
        print("\n📋 测试数据摘要:")
        print(f"👑 管理员用户: admin (密码: admin123)")
        print(f"👥 测试用户: {len(test_users)} 个 (密码: testpass123)")
        print(f"🎫 有效邀请码: TEST2025, INVITE2025, API_TEST 等")
        print(f"📅 学期: {len(semesters)} 个")
        print(f"📚 课程: {len(courses) if 'courses' in locals() else 0} 个")
        print(f"📁 文件夹: {len(folders) if 'folders' in locals() else 0} 个")
        print(f"💬 聊天: {len(chats) if 'chats' in locals() else 0} 个")
        print(f"📝 消息: {len(messages) if 'messages' in locals() else 0} 条")
        
        return True
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

def check_test_data():
    """检查测试数据状态"""
    print("🔍 检查测试数据状态...")
    
    db: Session = SessionLocal()
    try:
        # 检查各表数据量
        users_count = db.query(User).count()
        invite_codes_count = db.query(InviteCode).count()
        semesters_count = db.query(Semester).count()
        courses_count = db.query(Course).count()
        folders_count = db.query(Folder).count()
        files_count = db.query(File).count()
        chats_count = db.query(Chat).count()
        messages_count = db.query(Message).count()
        
        print(f"📊 数据统计:")
        print(f"  👥 用户: {users_count}")
        print(f"  🎫 邀请码: {invite_codes_count}")
        print(f"  📅 学期: {semesters_count}")
        print(f"  📚 课程: {courses_count}")
        print(f"  📁 文件夹: {folders_count}")
        print(f"  📄 文件: {files_count}")
        print(f"  💬 聊天: {chats_count}")
        print(f"  📝 消息: {messages_count}")
        
        # 检查关键测试数据
        print(f"\n🔑 关键测试数据:")
        
        # 管理员用户
        admin = db.query(User).filter(User.username == "admin").first()
        print(f"  👑 管理员用户: {'✅ 存在' if admin else '❌ 缺失'}")
        
        # 测试用户
        testuser = db.query(User).filter(User.username == "testuser").first()
        print(f"  👤 测试用户: {'✅ 存在' if testuser else '❌ 缺失'}")
        
        # 有效邀请码
        valid_codes = db.query(InviteCode).filter(
            InviteCode.is_used == False,
            InviteCode.is_active == True,
            InviteCode.expires_at > datetime.now()
        ).count()
        print(f"  🎫 有效邀请码: {valid_codes} 个")
        
        # 测试邀请码
        test_code = db.query(InviteCode).filter(InviteCode.code == "TEST2025").first()
        print(f"  🔑 TEST2025邀请码: {'✅ 存在' if test_code else '❌ 缺失'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False
    finally:
        db.close()

def clean_test_data():
    """清理测试数据"""
    print("🧹 清理测试数据...")
    
    db: Session = SessionLocal()
    try:
        # 删除测试数据（保留真实数据）
        db.query(Message).delete()
        db.query(Chat).delete()
        db.query(File).delete()
        db.query(Folder).delete()
        db.query(Course).delete()
        
        # 只删除测试学期
        db.query(Semester).filter(Semester.code.like('TEST%')).delete()
        
        # 只删除测试邀请码
        db.query(InviteCode).filter(InviteCode.code.like('TEST%')).delete()
        db.query(InviteCode).filter(InviteCode.code.like('AUTO_%')).delete()
        db.query(InviteCode).filter(InviteCode.code.in_(['INVITE2025', 'API_TEST', 'DEMO2025', 'USED2025', 'EXPIRED2024', 'INACTIVE2025'])).delete()
        
        # 只删除测试用户
        db.query(User).filter(User.username.like('test%')).delete()
        db.query(User).filter(User.username.like('api_test%')).delete()
        db.query(User).filter(User.username == 'demo_user').delete()
        
        db.commit()
        print("✅ 测试数据清理完成")
        
    except Exception as e:
        print(f"❌ 清理失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试数据管理脚本")
    parser.add_argument("action", choices=["init", "check", "clean"], 
                       help="操作类型: init(初始化), check(检查), clean(清理)")
    
    args = parser.parse_args()
    
    if args.action == "init":
        init_test_data()
    elif args.action == "check":
        check_test_data()
    elif args.action == "clean":
        clean_test_data()