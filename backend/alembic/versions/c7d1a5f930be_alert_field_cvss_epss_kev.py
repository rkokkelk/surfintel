"""Add cvss_score, epss_score, kev to alert_field enum

Revision ID: c7d1a5f930be
Revises: a3f6c9e21d47
Create Date: 2026-09-28 21:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'c7d1a5f930be'
down_revision: Union[str, None] = 'a3f6c9e21d47'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE alert_field ADD VALUE IF NOT EXISTS 'cvss_score'")
    op.execute("ALTER TYPE alert_field ADD VALUE IF NOT EXISTS 'epss_score'")
    op.execute("ALTER TYPE alert_field ADD VALUE IF NOT EXISTS 'kev'")


def downgrade() -> None:
    # Postgres has no ALTER TYPE ... DROP VALUE — reverting would mean
    # rebuilding the enum from scratch, which isn't worth it for an additive
    # field list. Left as a no-op, matching how this project treats other
    # enum-add migrations.
    pass
