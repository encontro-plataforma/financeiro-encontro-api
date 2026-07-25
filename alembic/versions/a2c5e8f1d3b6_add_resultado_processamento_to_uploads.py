"""add resultado_processamento to uploads

Revision ID: a2c5e8f1d3b6
Revises: f4a7c9e2b380
Create Date: 2026-07-25 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a2c5e8f1d3b6"
down_revision: Union[str, None] = "f4a7c9e2b380"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("uploads", sa.Column("resultado_processamento", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("uploads", "resultado_processamento")
