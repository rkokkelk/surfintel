"""Add message_template to alert_rule

Revision ID: a3f6c9e21d47
Revises: 8f2a1d6c4b90
Create Date: 2026-09-28 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3f6c9e21d47'
down_revision: Union[str, None] = '8f2a1d6c4b90'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('alert_rule', sa.Column('message_template', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('alert_rule', 'message_template')
