"""renomear extratos_bancarios para uploads e adicionar error_code/error_message

Revision ID: b7d1e4f8a293
Revises: 9c3d7e2f4a81
Create Date: 2026-07-24 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7d1e4f8a293"
down_revision: Union[str, None] = "9c3d7e2f4a81"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("extratos_bancarios", "uploads")
    op.add_column("uploads", sa.Column("error_code", sa.String(50), nullable=True))
    op.add_column("uploads", sa.Column("error_message", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("uploads", "error_message")
    op.drop_column("uploads", "error_code")
    op.rename_table("uploads", "extratos_bancarios")
