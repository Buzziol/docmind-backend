from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth_schema import UserCreate


class DuplicateEmailError(ValueError):
    pass


def get_user_by_email(db: Session, email: str) -> User | None:
    normalized_email = email.lower()
    return db.query(User).filter(User.email == normalized_email).first()


def create_user(db: Session, user_data: UserCreate) -> User:
    normalized_email = str(user_data.email).lower()
    if email_exists(db, normalized_email):
        raise DuplicateEmailError("Email is already registered")

    user = User(
        name=user_data.name,
        email=normalized_email,
        password_hash=get_password_hash(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user is None:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def email_exists(db: Session, email: str) -> bool:
    return get_user_by_email(db, email) is not None
