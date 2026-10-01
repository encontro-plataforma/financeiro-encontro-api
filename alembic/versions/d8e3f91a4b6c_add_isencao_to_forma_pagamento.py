"""add ISENCAO ao forma_pagamento

Revision ID: d8e3f91a4b6c
Revises: c3d5e7f9a1b2
Create Date: 2026-10-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "d8e3f91a4b6c"
down_revision: Union[str, None] = "c3d5e7f9a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE forma_pagamento ADD VALUE IF NOT EXISTS 'ISENCAO'")


def downgrade() -> None:
    # Nota: o Postgres não suporta remover um valor de enum (ALTER TYPE ... DROP VALUE),
    # então o downgrade não reverte a adição de 'ISENCAO' ao enum forma_pagamento.
    pass
