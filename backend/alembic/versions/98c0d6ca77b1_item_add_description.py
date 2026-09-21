"""Item add description

Revision ID: 98c0d6ca77b1
Revises: 0001_initial
Create Date: 2026-09-21 10:27:00.165343
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '98c0d6ca77b1'
down_revision: str | None = '0001_initial'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "item",
        sa.Column("description", sa.Text, nullable=True)
    )


def downgrade() -> None:
    op.drop_column("item", "description")
