"""Add github source type

Revision ID: 1c3770f4ef2c
Revises: 3b7c1f9a2d4e
Create Date: 2026-09-27 22:50:27.349561
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1c3770f4ef2c'
down_revision: Union[str, None] = '3b7c1f9a2d4e'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE source_type ADD VALUE 'gh'")


def downgrade() -> None:
    pass
