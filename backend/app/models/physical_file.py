from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.models.database import Base

class PhysicalFile(Base):
    __tablename__ = "physical_files"

    id = Column(Integer, primary_key=True, index=True)
    file_hash = Column(String(64), unique=True, nullable=False, index=True)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    storage_path = Column(String(500), nullable=False)
    first_uploaded_at = Column(DateTime, server_default=func.now())
    reference_count = Column(Integer, default=0)

    # 关系
    files = relationship("File", back_populates="physical_file")
