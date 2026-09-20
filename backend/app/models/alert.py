import datetime as dt
import enum
import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    LargeBinary,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPk


class AlertRuleStatus(str, enum.Enum):
    active = "active"
    paused = "paused"


class AlertField(str, enum.Enum):
    vendor = "vendor"
    product = "product"
    severity = "severity"
    category = "category"
    cve_id = "cve_id"
    source = "source"
    tag = "tag"
    keyword = "keyword"


class NotificationStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"


class AlertRule(Base, UUIDPk, TimestampMixin):
    __tablename__ = "alert_rule"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organization.id"), index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id"))
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[AlertRuleStatus] = mapped_column(
        Enum(AlertRuleStatus, name="alert_rule_status"), default=AlertRuleStatus.active
    )
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AlertCondition(Base, UUIDPk):
    """All conditions under one alert_rule are AND-ed; `values` holds the
    OR-within-field list (e.g. field=vendor, values=["Ivanti", "Fortinet"]).
    """

    __tablename__ = "alert_condition"

    alert_rule_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("alert_rule.id"), index=True)
    field: Mapped[AlertField] = mapped_column(Enum(AlertField, name="alert_field"))
    values: Mapped[list] = mapped_column(JSON)


class AlertChannel(Base, UUIDPk, TimestampMixin):
    """apprise_url is encrypted at rest (app.core.encryption) — Apprise URLs
    routinely embed webhook tokens or SMTP credentials.
    """

    __tablename__ = "alert_channel"

    alert_rule_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("alert_rule.id"), index=True)
    label: Mapped[str] = mapped_column(String(100))
    apprise_url_encrypted: Mapped[bytes] = mapped_column(LargeBinary)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class AlertMatch(Base, UUIDPk):
    """One row per (rule, item) match — the unique constraint is what makes
    alert evaluation idempotent: an item can never notify twice for the same rule.
    """

    __tablename__ = "alert_match"
    __table_args__ = (UniqueConstraint("alert_rule_id", "item_id", name="uq_alert_rule_item"),)

    alert_rule_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("alert_rule.id"), index=True)
    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("item.id"), index=True)
    matched_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    notified_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notification_status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, name="notification_status"), default=NotificationStatus.pending
    )
