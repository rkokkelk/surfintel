from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPk


class Organization(Base, UUIDPk, TimestampMixin):
    """A SURF member institution — or SURF itself, when is_platform_operator is set.

    Platform-wide super-admins are just app_users of the platform-operator
    organization with is_platform_admin=True, so every user still belongs to
    exactly one organization without needing a separate concept.
    """

    __tablename__ = "organization"

    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    sso_entity_id: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_platform_operator: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
