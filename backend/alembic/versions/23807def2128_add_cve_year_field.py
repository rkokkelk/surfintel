"""Add CVE year field

Revision ID: 23807def2128
Revises: 9a4d2e7b6c13
Create Date: 2026-11-07 20:11:22.114389
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.models.cve import Cve


revision: str = '23807def2128'
down_revision: Union[str, None] = '9a4d2e7b6c13'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cve",
        sa.Column("year", sa.Integer, nullable=False)
    )

    bind = op.get_bind()
    session = sa.Session(bind=bind)

    for cve in session.query(Cve).all():
        cve.year = cve.get_year()

    session.commit()


def downgrade() -> None:
    op.drop_column("cve", "year")