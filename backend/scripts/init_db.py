from app.models.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.semester import Semester
from app.models.course import Course
from app.core.security import get_password_hash
from sqlalchemy.orm import Session, sessionmaker
from datetime import datetime, timedelta
from app.models.invite_code import InviteCode

# 创建所有表
Base.metadata.create_all(bind=engine)

def init_data():
    db: Session = SessionLocal()
    # 清空所有表
    db.query(Course).delete()
    db.query(Semester).delete()
    db.query(User).delete()
    db.query(InviteCode).delete()
    db.commit()

    # 创建测试用户
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        role="user",
        balance=10.0,
        total_spent=0.0,
        preferred_language="zh_CN",
        preferred_theme="light"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 创建测试学期
    semester = Semester(
        name="2025第三学期",
        code="2025S3",
        start_date=datetime(2025, 9, 1),
        end_date=datetime(2025, 12, 31),
        is_active=True
    )
    db.add(semester)
    db.commit()
    db.refresh(semester)

    # 创建测试课程
    course = Course(
        name="数据结构与算法",
        code="CS1101A",
        description="学习各种数据结构和算法",
        semester_id=semester.id,
        user_id=user.id
    )
    db.add(course)
    db.commit()
    db.refresh(course)

    # 批量插入10条未使用的邀请码
    now = datetime.now()
    for i in range(1, 11):
        code = f"INVITE2025_{i}"
        invite = InviteCode(
            code=code,
            description="测试邀请码",
            is_used=False,
            expires_at=now + timedelta(days=30)
        )
        db.add(invite)
    db.commit()

    # 插入兼容老测试用例的邀请码
    invite_old = InviteCode(
        code="INVITE2025",
        description="老测试邀请码",
        is_used=False,
        expires_at=now + timedelta(days=30)
    )
    db.add(invite_old)
    db.commit()

    # 插入一个已使用的邀请码
    invite_used = InviteCode(
        code="USED2025",
        description="已使用的邀请码",
        is_used=True,
        expires_at=now + timedelta(days=30)
    )
    db.add(invite_used)
    db.commit()

    print("✅ 测试数据初始化完成！")
    db.close()

if __name__ == "__main__":
    init_data() 