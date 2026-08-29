"""add cart columns to lancamentos

Revision ID: b1c4d7e9a2f5
Revises: 3ae2a2c65566
Create Date: 2026-08-29 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b1c4d7e9a2f5"
down_revision: Union[str, None] = "3ae2a2c65566"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("lancamentos", sa.Column("cart_taxa", sa.Float(), nullable=True))
    op.add_column("lancamentos", sa.Column("cart_valor_liquido", sa.Float(), nullable=True))
    op.add_column("lancamentos", sa.Column("cart_parcelas", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("lancamentos", "cart_parcelas")
    op.drop_column("lancamentos", "cart_valor_liquido")
    op.drop_column("lancamentos", "cart_taxa")
