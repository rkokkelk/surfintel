"""Add source favicon

Revision ID: fa0e326994cf
Revises: d842151242b6
Create Date: 2026-09-21 20:50:46.690516
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'fa0e326994cf'
down_revision: Union[str, None] = 'd842151242b6'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "source",
        sa.Column("favicon", sa.Text)
    )


def downgrade() -> None:
    op.drop_column(
        "source",
        "favicon"
    )
