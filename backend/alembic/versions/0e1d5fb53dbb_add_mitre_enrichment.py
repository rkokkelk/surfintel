"""Add mitre enrichment

Revision ID: 0e1d5fb53dbb
Revises: c7d1a5f930be
Create Date: 2026-10-10 13:31:48.250364
"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = '0e1d5fb53dbb'
down_revision: Union[str, None] = 'c7d1a5f930be'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "source",
        sa.Column("enrich_mitre", sa.Boolean, nullable=False, server_default=sa.false()),
    )
    op.drop_column("source", "enrich_kev")


def downgrade() -> None:
    op.drop_column("source", "enrich_mitre")
    op.add_column(
        "source",
        sa.Column("enrich_kev", sa.Boolean, nullable=False, server_default=sa.true()),
    )