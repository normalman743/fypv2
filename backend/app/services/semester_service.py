from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.semester import Semester
from app.schemas.semester import SemesterCreate, SemesterUpdate
from app.core.exceptions import ConflictError, NotFoundError, BadRequestError


class SemesterService:
    def __init__(self, db: Session):
        self.db = db

    def get_semesters(self) -> List[Semester]:
        """Get all active semesters"""
        return self.db.query(Semester).filter(Semester.is_active == True).all()

    def get_semester_by_id(self, semester_id: int) -> Optional[Semester]:
        """Get semester by ID"""
        return self.db.query(Semester).filter(
            Semester.id == semester_id,
            Semester.is_active == True
        ).first()
    
    def get_semester(self, semester_id: int) -> Optional[Semester]:
        """Get semester by ID (alias for get_semester_by_id)"""
        return self.get_semester_by_id(semester_id)

    def create_semester(self, semester_data: SemesterCreate) -> Semester:
        """Create new semester"""
        # Check if semester code already exists
        existing = self.db.query(Semester).filter(
            Semester.code == semester_data.code
        ).first()
        if existing:
            raise BadRequestError(f"Semester code '{semester_data.code}' already exists", "SEMESTER_CODE_EXISTS")

        try:
            semester = Semester(**semester_data.model_dump())
            self.db.add(semester)
            self.db.commit()
            self.db.refresh(semester)
            return semester
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("Semester code already exists or data conflict")

    def update_semester(self, semester_id: int, semester_data: SemesterUpdate) -> Semester:
        """Update semester information"""
        semester = self.get_semester_by_id(semester_id)
        if not semester:
            raise NotFoundError("Semester not found", "SEMESTER_NOT_FOUND")

        # Check code conflict if updating code
        if semester_data.code and semester_data.code != semester.code:
            existing = self.db.query(Semester).filter(
                Semester.code == semester_data.code,
                Semester.id != semester_id
            ).first()
            if existing:
                raise BadRequestError(f"Semester code '{semester_data.code}' already exists", "SEMESTER_CODE_EXISTS")

        try:
            # Only update provided fields
            update_data = semester_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(semester, field, value)

            self.db.commit()
            self.db.refresh(semester)
            return semester
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("Semester code already exists or data conflict")

    def delete_semester(self, semester_id: int) -> bool:
        """Delete semester (soft delete)"""
        semester = self.get_semester_by_id(semester_id)
        if not semester:
            raise NotFoundError("Semester not found", "SEMESTER_NOT_FOUND")

        # Check if there are associated courses
        from app.models.course import Course
        course_count = self.db.query(Course).filter(
            Course.semester_id == semester_id
        ).count()
        
        if course_count > 0:
            raise ConflictError(f"Cannot delete semester, {course_count} courses are associated with this semester")

        semester.is_active = False
        self.db.commit()
        return True