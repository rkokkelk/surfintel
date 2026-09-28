import datetime as dt
import uuid

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPk


class Cve(Base, TimestampMixin):
    """One row per CVE, synced from OpenCVE — shared across every item that
    mentions it (see ItemCve), rather than re-fetched and duplicated into
    every item's own item_enrichment row. `cve_id` is the primary key: CVE
    identifiers are already globally unique, a surrogate UUID would just be
    an extra join key for no benefit.
    """

    __tablename__ = "cve"

    cve_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    cvss_v3_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    cvss_v3_vector: Mapped[str | None] = mapped_column(String(200), nullable=True)
    cvss_v4_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    cvss_v4_vector: Mapped[str | None] = mapped_column(String(200), nullable=True)
    epss_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    in_kev: Mapped[bool] = mapped_column(Boolean, default=False)
    kev_date_added: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    cpes: Mapped[list] = mapped_column(JSON, default=list)
    weaknesses: Mapped[list] = mapped_column(JSON, default=list)
    references: Mapped[list] = mapped_column(JSON, default=list)

    # The full OpenCVE payload, kept as a fallback so a new field we want to
    # surface later doesn't need another round of (rate-limited) API calls —
    # only the fields above are relied on elsewhere in the app.
    raw_data: Mapped[dict] = mapped_column(JSON, default=dict)

    fetched_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ItemCve(Base, UUIDPk):
    """Many-to-many: one item can mention several CVEs, and (across the whole
    feed) one CVE is typically mentioned by several items.
    """

    __tablename__ = "item_cve"
    __table_args__ = (UniqueConstraint("item_id", "cve_id", name="uq_item_cve"),)

    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("item.id"), index=True)
    cve_id: Mapped[str] = mapped_column(ForeignKey("cve.cve_id"), index=True)
