"""Add per-source enrichment toggles

Revision ID: 3b7c1f9a2d4e
Revises: fa0e326994cf
Create Date: 2026-09-24 09:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '3b7c1f9a2d4e'
down_revision: Union[str, None] = 'fa0e326994cf'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None

TOGGLES = ("enrich_cve", "enrich_cpe", "enrich_kev", "enrich_ai")


def upgrade() -> None:
    # server_default=true backfills existing sources: enrichment stays on for
    # everything that already exists.
    for column in TOGGLES:
        op.add_column(
            "source",
            sa.Column(column, sa.Boolean, nullable=False, server_default=sa.true()),
        )


def downgrade() -> None:
    for column in TOGGLES:
        op.drop_column("source", column)
