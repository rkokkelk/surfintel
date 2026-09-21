"""Add SourceType HTML

Revision ID: d842151242b6
Revises: 98c0d6ca77b1
Create Date: 2026-09-21 17:37:39.134407
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd842151242b6'
down_revision: Union[str, None] = '98c0d6ca77b1'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE source_type ADD VALUE 'html'")

def downgrade() -> None:
    pass
