from sqlalchemy import Column, Integer, String, DateTime, Boolean, CheckConstraint, Index
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from app.models.database import Base

class Semester(Base):
    __tablename__ = "semesters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    courses = relationship("Course", back_populates="semester")
    
    # 表级约束
    __table_args__ = (
        CheckConstraint('end_date > start_date', name='check_semester_dates'),
        Index('idx_semester_active_dates', 'is_active', 'start_date', 'end_date'),
        Index('idx_semester_code_active', 'code', 'is_active'),
    )
    
    @validates('start_date', 'end_date')
    def validate_dates(self, key, value):
        """验证日期逻辑"""
        if key == 'end_date' and hasattr(self, 'start_date') and self.start_date:
            if value and value <= self.start_date:
                raise ValueError("End date must be after start date")
        return value
    
    @validates('code')
    def validate_code(self, key, value):
        """验证学期代码格式"""
        if not value or len(value.strip()) == 0:
            raise ValueError("Semester code cannot be empty")
        if len(value) > 20:
            raise ValueError("Semester code too long")
        return value.strip().upper()
    
    @validates('name')
    def validate_name(self, key, value):
        """验证学期名称"""
        if not value or len(value.strip()) == 0:
            raise ValueError("Semester name cannot be empty")
        if len(value) > 100:
            raise ValueError("Semester name too long")
        return value.strip()
