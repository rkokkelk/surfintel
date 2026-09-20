"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organization",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("sso_entity_id", sa.String(300), nullable=True),
        sa.Column("is_platform_operator", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "app_user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organization.id"), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("role", sa.Enum("admin", "viewer", name="user_role"), nullable=False, server_default="viewer"),
        sa.Column("is_platform_admin", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("password_hash", sa.String(200), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_app_user_organization_id", "app_user", ["organization_id"])

    op.create_table(
        "source",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("type", sa.Enum("rss", "custom_module", name="source_type"), nullable=False),
        sa.Column("config", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("poll_interval_seconds", sa.Integer, nullable=False, server_default="3600"),
        sa.Column("last_polled_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "item",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("source.id"), nullable=False),
        sa.Column("url", sa.String(2000), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("discovered", "fetched", "enriched", "error", name="item_status"),
            nullable=False,
            server_default="discovered",
        ),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("last_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_html", sa.Text, nullable=True),
        sa.Column("extracted_text", sa.Text, nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("url"),
    )
    op.create_index("ix_item_source_id", "item", ["source_id"])

    op.create_table(
        "item_enrichment",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("item.id"), nullable=False),
        sa.Column("module_name", sa.String(100), nullable=False),
        sa.Column("module_version", sa.String(20), nullable=False),
        sa.Column("data", sa.JSON, nullable=False, server_default="{}"),
        sa.UniqueConstraint("item_id", "module_name", name="uq_item_module"),
    )
    op.create_index("ix_item_enrichment_item_id", "item_enrichment", ["item_id"])

    op.create_table(
        "alert_rule",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organization.id"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("app_user.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "paused", name="alert_rule_status"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_alert_rule_organization_id", "alert_rule", ["organization_id"])

    op.create_table(
        "alert_condition",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("alert_rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("alert_rule.id"), nullable=False),
        sa.Column(
            "field",
            sa.Enum(
                "vendor", "product", "severity", "category", "cve_id", "source", "tag", "keyword",
                name="alert_field",
            ),
            nullable=False,
        ),
        sa.Column("values", sa.JSON, nullable=False),
    )
    op.create_index("ix_alert_condition_alert_rule_id", "alert_condition", ["alert_rule_id"])

    op.create_table(
        "alert_channel",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("alert_rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("alert_rule.id"), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("apprise_url_encrypted", sa.LargeBinary, nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_alert_channel_alert_rule_id", "alert_channel", ["alert_rule_id"])

    op.create_table(
        "alert_match",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("alert_rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("alert_rule.id"), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("item.id"), nullable=False),
        sa.Column("matched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "notification_status",
            sa.Enum("pending", "sent", "failed", name="notification_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.UniqueConstraint("alert_rule_id", "item_id", name="uq_alert_rule_item"),
    )
    op.create_index("ix_alert_match_alert_rule_id", "alert_match", ["alert_rule_id"])
    op.create_index("ix_alert_match_item_id", "alert_match", ["item_id"])


def downgrade() -> None:
    op.drop_table("alert_match")
    op.drop_table("alert_channel")
    op.drop_table("alert_condition")
    op.drop_table("alert_rule")
    op.drop_table("item_enrichment")
    op.drop_table("item")
    op.drop_table("source")
    op.drop_table("app_user")
    op.drop_table("organization")

    for enum_name in (
        "notification_status",
        "alert_field",
        "alert_rule_status",
        "item_status",
        "source_type",
        "user_role",
    ):
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
