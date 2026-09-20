import uuid

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPk


class ItemEnrichment(Base, UUIDPk, TimestampMixin):
    """One row per enrichment module per item. Re-running a module upserts
    this row (latest result only, no history) — new modules become usable
    without touching the schema or the modules that ran before them.
    """

    __tablename__ = "item_enrichment"
    __table_args__ = (UniqueConstraint("item_id", "module_name", name="uq_item_module"),)

    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("item.id"), index=True)
    module_name: Mapped[str] = mapped_column(String(100))
    module_version: Mapped[str] = mapped_column(String(20))
    data: Mapped[dict] = mapped_column(JSON, default=dict)
