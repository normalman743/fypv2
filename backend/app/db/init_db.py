from app.db.base import Base
from app.db.session import engine

# Import all models to ensure they are registered with SQLAlchemy Base.metadata
# This is necessary for Base.metadata.create_all to find all tables.
from app.models.user import User  # noqa
from app.models.semester import Semester  # noqa
from app.models.course import Course  # noqa
from app.models.chat import Chat  # noqa
from app.models.file import PhysicalFile, Folder, File, GlobalFile, DocumentChunk  # noqa
from app.models.invite_code import InviteCode  # noqa
from app.models.message import Message, MessageFile  # noqa

def init_db():
    print("Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

if __name__ == "__main__":
    init_db()
