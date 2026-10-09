"""add ENCONTREIRO/ENCONTRISTA ao tipo_origem_upload

Revision ID: 51ca10ea476f
Revises: e5f1a9c4b7d2
Create Date: 2026-10-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "51ca10ea476f"
down_revision: Union[str, None] = "e5f1a9c4b7d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE tipo_origem_upload ADD VALUE IF NOT EXISTS 'ENCONTREIRO'")
        op.execute("ALTER TYPE tipo_origem_upload ADD VALUE IF NOT EXISTS 'ENCONTRISTA'")


def downgrade() -> None:
    # Nota: o Postgres não suporta remover um valor de enum (ALTER TYPE ... DROP VALUE),
    # então o downgrade não reverte a adição de 'ENCONTREIRO'/'ENCONTRISTA' ao enum.
    pass
