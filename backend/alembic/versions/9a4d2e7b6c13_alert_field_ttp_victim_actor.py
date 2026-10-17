"""Add ttp, victim_category, victim_country, actor to alert_field enum

Revision ID: 9a4d2e7b6c13
Revises: 0e1d5fb53dbb
Create Date: 2026-10-17 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = '9a4d2e7b6c13'
down_revision: Union[str, None] = '0e1d5fb53dbb'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE alert_field ADD VALUE IF NOT EXISTS 'ttp'")
    op.execute("ALTER TYPE alert_field ADD VALUE IF NOT EXISTS 'victim_category'")
    op.execute("ALTER TYPE alert_field ADD VALUE IF NOT EXISTS 'victim_country'")
    op.execute("ALTER TYPE alert_field ADD VALUE IF NOT EXISTS 'actor'")


def downgrade() -> None:
    # Postgres has no ALTER TYPE ... DROP VALUE — see c7d1a5f930be, which
    # left the same kind of migration as a no-op downgrade for the same reason.
    pass
