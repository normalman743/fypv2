from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_username(self, db: Session, *, username: str) -> User | None:
        return db.query(self.model).filter(self.model.username == username).first()

    def get_by_email(self, db: Session, *, email: str) -> User | None:
        return db.query(self.model).filter(self.model.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        hashed_password = pwd_context.hash(obj_in.password)
        db_obj = self.model(
            username=obj_in.username,
            email=obj_in.email,
            password_hash=hashed_password,
            role=obj_in.role,
            preferred_language=obj_in.preferred_language,
            preferred_theme=obj_in.preferred_theme,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def authenticate(self, db: Session, *, username: str, password: str) -> User | None:
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        if not pwd_context.verify(password, user.password_hash):
            return None
        return user

user = CRUDUser(User)
