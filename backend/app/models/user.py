import datetime as dt
import enum
import uuid

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPk


class UserRole(str, enum.Enum):
    admin = "admin"
    viewer = "viewer"


class AppUser(Base, UUIDPk, TimestampMixin):
    """Named app_user, not user — `user` is a reserved-ish identifier in Postgres."""

    __tablename__ = "app_user"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organization.id"), index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), default=UserRole.viewer)
    is_platform_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    # Nullable: an organization that is SURFconext SSO-only has no local password.
    password_hash: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
