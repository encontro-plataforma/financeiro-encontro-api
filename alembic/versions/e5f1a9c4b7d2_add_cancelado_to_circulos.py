"""add cancelado to circulos

Revision ID: e5f1a9c4b7d2
Revises: d8e3f91a4b6c
Create Date: 2026-10-01 00:00:00.000001

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5f1a9c4b7d2"
down_revision: Union[str, None] = "d8e3f91a4b6c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "circulos",
        sa.Column("cancelado", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("circulos", "cancelado")
