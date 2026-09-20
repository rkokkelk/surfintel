import datetime as dt
import enum
import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPk


class ItemStatus(str, enum.Enum):
    discovered = "discovered"
    fetched = "fetched"
    enriched = "enriched"
    error = "error"


class Item(Base, UUIDPk, TimestampMixin):
    """One tracked link, deduplicated on URL. Only the latest fetched content
    is kept (content_hash + last_changed_at), not a full revision history —
    a deliberate MVP simplification.
    """

    __tablename__ = "item"

    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("source.id"), index=True)
    url: Mapped[str] = mapped_column(String(2000), unique=True, index=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[ItemStatus] = mapped_column(
        Enum(ItemStatus, name="item_status"), default=ItemStatus.discovered
    )
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_changed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_checked_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
