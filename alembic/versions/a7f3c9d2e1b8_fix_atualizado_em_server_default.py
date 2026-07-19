"""fix atualizado_em server_default in lancamentos

Revision ID: a7f3c9d2e1b8
Revises: 3f8a92b1c047
Create Date: 2026-05-09 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a7f3c9d2e1b8'
down_revision: Union[str, Sequence[str], None] = '3f8a92b1c047'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # backfill: registros sem atualizado_em recebem o valor de criado_em
    op.execute("""
        UPDATE lancamentos
        SET atualizado_em = criado_em
        WHERE atualizado_em IS NULL
    """)

    op.alter_column(
        'lancamentos',
        'atualizado_em',
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        'lancamentos',
        'atualizado_em',
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        nullable=True,
    )
