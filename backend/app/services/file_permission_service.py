from typing import Optional
from sqlalchemy.orm import Session
from app.models.file import File
from app.models.user import User
from app.models.course import Course
from app.models.file_share import FileShare


class FilePermissionService:
    """文件权限检查服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def can_access_file(self, file_id: int, user_id: int) -> bool:
        """检查用户是否可以访问文件"""
        file_record = self.db.query(File).filter(File.id == file_id).first()
        if not file_record:
            return False
        
        return self._check_file_access(file_record, user_id)
    
    def can_edit_file(self, file_id: int, user_id: int) -> bool:
        """检查用户是否可以编辑文件"""
        file_record = self.db.query(File).filter(File.id == file_id).first()
        if not file_record:
            return False
        
        # 只有文件所有者可以编辑
        if file_record.user_id == user_id:
            return True
        
        # 检查是否有编辑权限的共享
        share = self.db.query(FileShare).filter(
            FileShare.file_id == file_id,
            FileShare.shared_with_type == 'user',
            FileShare.shared_with_id == user_id,
            FileShare.permission_level.in_(['edit', 'manage'])
        ).first()
        
        return share is not None
    
    def can_delete_file(self, file_id: int, user_id: int) -> bool:
        """检查用户是否可以删除文件"""
        file_record = self.db.query(File).filter(File.id == file_id).first()
        if not file_record:
            return False
        
        # 只有文件所有者可以删除
        if file_record.user_id == user_id:
            return True
        
        # 检查是否有管理权限的共享
        share = self.db.query(FileShare).filter(
            FileShare.file_id == file_id,
            FileShare.shared_with_type == 'user',
            FileShare.shared_with_id == user_id,
            FileShare.permission_level == 'manage'
        ).first()
        
        return share is not None
    
    def can_share_file(self, file_id: int, user_id: int) -> bool:
        """检查用户是否可以共享文件"""
        file_record = self.db.query(File).filter(File.id == file_id).first()
        if not file_record:
            return False
        
        # 文件所有者可以共享
        if file_record.user_id == user_id:
            return True
        
        # 检查是否有重新共享权限
        share = self.db.query(FileShare).filter(
            FileShare.file_id == file_id,
            FileShare.shared_with_type == 'user',
            FileShare.shared_with_id == user_id,
            FileShare.can_reshare == True
        ).first()
        
        return share is not None
    
    def _check_file_access(self, file: File, user_id: int) -> bool:
        """内部方法：检查文件访问权限"""
        
        # 1. 文件所有者总是有权限
        if file.user_id == user_id:
            return True
        
        # 2. 公开文件任何人都可以访问
        if file.visibility == 'public':
            return True
        
        # 3. 检查直接共享给用户的权限
        if self._has_direct_share(file.id, user_id):
            return True
        
        # 4. 课程文件的特殊处理
        if file.scope == 'course' and file.course_id:
            if self._has_course_access(file.course_id, user_id, file.visibility):
                return True
        
        # 5. 检查组共享权限
        if self._has_group_access(file.id, user_id):
            return True
        
        # 6. 管理员可以访问所有文件（可选）
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.role == 'admin':
            return True
        
        return False
    
    def _has_direct_share(self, file_id: int, user_id: int) -> bool:
        """检查是否直接共享给用户"""
        share = self.db.query(FileShare).filter(
            FileShare.file_id == file_id,
            FileShare.shared_with_type == 'user',
            FileShare.shared_with_id == user_id
        ).first()
        
        # TODO: 检查过期时间
        return share is not None
    
    def _has_course_access(self, course_id: int, user_id: int, file_visibility: str) -> bool:
        """检查课程访问权限"""
        
        # 获取课程信息
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            return False
        
        # 课程所有者可以访问所有课程文件
        if course.user_id == user_id:
            return True
        
        # 如果文件可见性是 'course'，需要检查用户是否是课程成员
        if file_visibility == 'course':
            # TODO: 实现课程成员检查
            # 目前简化处理：如果有课程级别的共享，则允许访问
            course_share = self.db.query(FileShare).filter(
                FileShare.shared_with_type == 'course',
                FileShare.shared_with_id == course_id
            ).first()
            return course_share is not None
        
        return False
    
    def _has_group_access(self, file_id: int, user_id: int) -> bool:
        """检查组共享权限"""
        # TODO: 实现组权限检查
        # 查找用户所在的所有组，然后检查是否有组级别的文件共享
        return False
    
    def get_accessible_files(self, user_id: int, scope: Optional[str] = None, course_id: Optional[int] = None) -> list:
        """获取用户可访问的文件列表"""
        
        # 基础查询
        query = self.db.query(File)
        
        # 作用域过滤
        if scope:
            query = query.filter(File.scope == scope)
        
        # 课程过滤
        if course_id:
            query = query.filter(File.course_id == course_id)
        
        all_files = query.all()
        
        # 使用权限检查过滤
        accessible_files = []
        for file in all_files:
            if self._check_file_access(file, user_id):
                accessible_files.append(file)
        
        return accessible_files
    
    def get_file_permission_summary(self, file_id: int, user_id: int) -> dict:
        """获取用户对文件的权限摘要"""
        return {
            'can_access': self.can_access_file(file_id, user_id),
            'can_edit': self.can_edit_file(file_id, user_id),
            'can_delete': self.can_delete_file(file_id, user_id),
            'can_share': self.can_share_file(file_id, user_id)
        }