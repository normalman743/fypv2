from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.database import Base

class MessageFile(Base):
    __tablename__ = "message_files"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint('message_id', 'file_id', name='unique_message_file'),
    )

    # 关系
    message = relationship("Message", back_populates="message_files")
    file = relationship("File")
