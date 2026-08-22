"""add N/A ao acesso_equipe

Revision ID: 3ae2a2c65566
Revises: 95c95957c2d5
Create Date: 2026-08-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "3ae2a2c65566"
down_revision: Union[str, None] = "95c95957c2d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE acesso_equipe ADD VALUE IF NOT EXISTS 'N/A'")


def downgrade() -> None:
    # Nota: o Postgres não suporta remover um valor de enum (ALTER TYPE ... DROP VALUE),
    # então o downgrade não reverte a adição de 'N/A' ao enum acesso_equipe.
    pass
