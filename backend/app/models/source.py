import datetime as dt
import enum

from sqlalchemy import JSON, Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPk


class SourceType(str, enum.Enum):
    rss = "rss"
    html = "html"
    custom_module = "custom_module"


class Source(Base, UUIDPk, TimestampMixin):
    """A feed to poll. `config` is interpreted by the Source implementation
    registered for `type` (e.g. {"feed_url": "..."} for rss, or
    {"module": "vendor_x_advisories", ...} for a custom module).
    """

    __tablename__ = "source"

    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[SourceType] = mapped_column(Enum(SourceType, name="source_type"))
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    poll_interval_seconds: Mapped[int] = mapped_column(Integer, default=3600)
    last_polled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
