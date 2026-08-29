"""add onde_veio_ficha to encontristas

Revision ID: c3d5e7f9a1b2
Revises: b1c4d7e9a2f5
Create Date: 2026-08-29 00:00:00.000001

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3d5e7f9a1b2"
down_revision: Union[str, None] = "b1c4d7e9a2f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "encontristas",
        sa.Column("onde_veio_ficha", sa.String(150), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("encontristas", "onde_veio_ficha")
