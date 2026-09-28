"""Add cve and item_cve tables

Revision ID: 8f2a1d6c4b90
Revises: 1c3770f4ef2c
Create Date: 2026-09-28 09:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '8f2a1d6c4b90'
down_revision: Union[str, None] = '1c3770f4ef2c'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cve",
        sa.Column("cve_id", sa.String(20), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("cvss_v3_score", sa.Float, nullable=True),
        sa.Column("cvss_v3_vector", sa.String(200), nullable=True),
        sa.Column("cvss_v4_score", sa.Float, nullable=True),
        sa.Column("cvss_v4_vector", sa.String(200), nullable=True),
        sa.Column("epss_score", sa.Float, nullable=True),
        sa.Column("in_kev", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("kev_date_added", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cpes", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("weaknesses", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("references", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("raw_data", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "item_cve",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("item.id"), nullable=False),
        sa.Column("cve_id", sa.String(20), sa.ForeignKey("cve.cve_id"), nullable=False),
        sa.UniqueConstraint("item_id", "cve_id", name="uq_item_cve"),
    )
    op.create_index("ix_item_cve_item_id", "item_cve", ["item_id"])
    op.create_index("ix_item_cve_cve_id", "item_cve", ["cve_id"])


def downgrade() -> None:
    op.drop_table("item_cve")
    op.drop_table("cve")
