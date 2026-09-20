from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.base import AuthProvider
from app.core.security import verify_password
from app.models.user import AppUser


class LocalPasswordAuthProvider(AuthProvider):
    def authenticate(self, db: Session, *, email: str, password: str) -> AppUser | None:
        user = db.scalar(select(AppUser).where(AppUser.email == email, AppUser.is_active.is_(True)))
        if user is None or user.password_hash is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
