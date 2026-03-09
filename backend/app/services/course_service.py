from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.models.course import Course
from app.models.semester import Semester
from app.schemas.course import CourseCreate, CourseUpdate
from app.core.exceptions import ConflictError, NotFoundError, ForbiddenError, BadRequestError


class CourseService:
    def __init__(self, db: Session):
        self.db = db

    def get_courses(self, user_id: Optional[int] = None, semester_id: Optional[int] = None) -> List[Course]:
        """Get course list (optionally filtered by user and/or semester)"""
        query = self.db.query(Course).options(
            joinedload(Course.semester)
        )
        
        if user_id is not None:
            query = query.filter(Course.user_id == user_id)
        
        if semester_id:
            query = query.filter(Course.semester_id == semester_id)
            
        return query.all()

    def get_course_by_id(self, course_id: int, user_id: int) -> Optional[Course]:
        """Get course by ID (check ownership)"""
        return self.db.query(Course).options(
            joinedload(Course.semester)
        ).filter(
            Course.id == course_id,
            Course.user_id == user_id
        ).first()
    
    def get_course(self, course_id: int, user_id: int) -> Optional[Course]:
        """Get course by ID (alias for get_course_by_id)"""
        return self.get_course_by_id(course_id, user_id)

    def create_course(self, course_data: CourseCreate, user_id: int) -> Course:
        """Create new course"""
        # Check if semester exists and is active
        semester = self.db.query(Semester).filter(
            Semester.id == course_data.semester_id,
            Semester.is_active == True
        ).first()
        if not semester:
            raise BadRequestError("Semester not found or deactivated", "SEMESTER_NOT_FOUND")

        # Check if same user already has same course code in same semester
        existing = self.db.query(Course).filter(
            Course.code == course_data.code,
            Course.semester_id == course_data.semester_id,
            Course.user_id == user_id
        ).first()
        if existing:
            raise BadRequestError(f"Course code '{course_data.code}' already exists in this semester", "COURSE_CODE_EXISTS")

        try:
            course = Course(
                **course_data.model_dump(),
                user_id=user_id
            )
            self.db.add(course)
            self.db.commit()
            self.db.refresh(course)
            return course
        except IntegrityError:
            self.db.rollback()
            raise BadRequestError("Course code already exists in this semester", "COURSE_CODE_EXISTS")

    def update_course(self, course_id: int, course_data: CourseUpdate, user_id: int) -> Course:
        """Update course information"""
        # First check if course exists at all
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise NotFoundError("Course not found", "COURSE_NOT_FOUND")
        
        # Then check ownership
        if course.user_id != user_id:
            raise ForbiddenError("You don't have permission to update this course")
        
        # Load with semester info for response
        course = self.get_course_by_id(course_id, user_id)

        # Check code conflict if updating code
        if course_data.code and course_data.code != course.code:
            existing = self.db.query(Course).filter(
                Course.code == course_data.code,
                Course.semester_id == course.semester_id,
                Course.user_id == user_id,
                Course.id != course_id
            ).first()
            if existing:
                raise BadRequestError(f"Course code '{course_data.code}' already exists in this semester", "COURSE_CODE_EXISTS")

        try:
            # Only update provided fields
            update_data = course_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(course, field, value)

            self.db.commit()
            self.db.refresh(course)
            return course
        except IntegrityError:
            self.db.rollback()
            raise BadRequestError("Course code already exists in this semester", "COURSE_CODE_EXISTS")

    def delete_course(self, course_id: int, user_id: int) -> bool:
        """Delete course"""
        # First check if course exists at all
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise NotFoundError("Course not found", "COURSE_NOT_FOUND")
        
        # Then check ownership
        if course.user_id != user_id:
            raise ForbiddenError("You don't have permission to delete this course")

        # Check for associated folders or chats
        # For now, allow direct deletion - will add checks when implementing file/chat modules
        
        self.db.delete(course)
        self.db.commit()
        return True

    def get_course_stats(self, course_id: int, user_id: int) -> dict:
        """Get course statistics"""
        course = self.get_course_by_id(course_id, user_id)
        if not course:
            raise NotFoundError("Course not found", "COURSE_NOT_FOUND")

        # Get file and chat statistics (return fake data for now, will implement when file/chat modules are ready)
        return {
            "file_count": 0,
            "chat_count": 0
        }

    def get_batch_course_stats(self, course_ids: list) -> dict:
        """Get stats for multiple courses without re-querying each course (避免 N+1)"""
        # 目前 stats 还是返回固定值，但避免了每个 course 多一次 get_course_by_id 查询
        return {cid: {"file_count": 0, "chat_count": 0} for cid in course_ids}