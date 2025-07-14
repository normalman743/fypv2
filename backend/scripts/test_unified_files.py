#!/usr/bin/env python3
"""
测试统一文件系统功能
"""

import os
import sys
import tempfile
from io import BytesIO

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import UploadFile
from app.services.unified_file_service import UnifiedFileService
from app.models.database import engine
from app.models.file import File
from app.models.user import User
from sqlalchemy.orm import sessionmaker

def create_test_file():
    """创建测试文件"""
    content = b"This is a test file for unified file system"
    file_obj = BytesIO(content)
    
    # 模拟 UploadFile
    class MockUploadFile:
        def __init__(self, content, filename):
            self.file = BytesIO(content)
            self.filename = filename
            self.content_type = "text/plain"
    
    return MockUploadFile(content, "test_unified_file.txt")

def test_unified_file_system():
    """测试统一文件系统"""
    print("🧪 开始测试统一文件系统...")
    
    # 创建数据库会话
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 初始化服务
        service = UnifiedFileService(session)
        
        # 检查用户是否存在
        user = session.query(User).first()
        if not user:
            print("❌ 没有找到用户，请先创建用户")
            return
        
        print(f"✅ 使用用户: {user.username} (ID: {user.id})")
        
        # 1. 测试个人文件上传
        print("\n🔄 测试1: 上传个人文件...")
        test_file = create_test_file()
        
        personal_file = service.upload_file(
            file=test_file,
            user_id=user.id,
            scope='personal',
            description="测试个人文件",
            tags=["test", "personal"],
            visibility='private'
        )
        
        print(f"✅ 个人文件上传成功: {personal_file.original_name}")
        print(f"   - ID: {personal_file.id}")
        print(f"   - Scope: {personal_file.scope}")
        print(f"   - Visibility: {personal_file.visibility}")
        print(f"   - File Hash: {personal_file.file_hash}")
        
        # 2. 测试获取可访问文件
        print("\n🔄 测试2: 获取用户可访问文件...")
        accessible_files = service.get_accessible_files(
            user_id=user.id,
            include_shared=True
        )
        
        print(f"✅ 找到 {len(accessible_files)} 个可访问文件:")
        for f in accessible_files:
            print(f"   - {f.original_name} (scope: {f.scope}, visibility: {f.visibility})")
        
        # 3. 测试文件访问日志
        print("\n🔄 测试3: 记录文件访问...")
        service.log_file_access(
            file_id=personal_file.id,
            user_id=user.id,
            action='view',
            access_via='test'
        )
        print("✅ 文件访问日志记录成功")
        
        # 4. 测试文件去重
        print("\n🔄 测试4: 测试文件去重...")
        test_file_2 = create_test_file()  # 相同内容的文件
        
        duplicate_file = service.upload_file(
            file=test_file_2,
            user_id=user.id,
            scope='personal',
            description="重复文件测试",
            visibility='private'
        )
        
        if duplicate_file.file_hash == personal_file.file_hash:
            print("✅ 文件去重功能正常工作")
            print(f"   - 新文件ID: {duplicate_file.id}")
            print(f"   - 相同文件Hash: {duplicate_file.file_hash}")
        else:
            print("⚠️  文件去重可能有问题")
        
        # 5. 测试统计信息
        print("\n📊 最终统计:")
        total_files = session.query(File).count()
        personal_files = session.query(File).filter(File.scope == 'personal').count()
        course_files = session.query(File).filter(File.scope == 'course').count()
        global_files = session.query(File).filter(File.scope == 'global').count()
        
        print(f"   - 总文件数: {total_files}")
        print(f"   - 个人文件: {personal_files}")
        print(f"   - 课程文件: {course_files}")
        print(f"   - 全局文件: {global_files}")
        
        # 清理测试数据
        print("\n🧹 清理测试数据...")
        service.delete_file(personal_file.id, user.id)
        if duplicate_file.id != personal_file.id:
            service.delete_file(duplicate_file.id, user.id)
        print("✅ 测试数据清理完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
    
    print("\n🎉 统一文件系统测试完成！")

if __name__ == "__main__":
    test_unified_file_system()