"""renomear detalhamentos.observacao para descricao

Revision ID: c9d1f4a7b2e5
Revises: a2c5e8f1d3b6
Create Date: 2026-07-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "c9d1f4a7b2e5"
down_revision: Union[str, None] = "a2c5e8f1d3b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("detalhamentos", "observacao", new_column_name="descricao")


def downgrade() -> None:
    op.alter_column("detalhamentos", "descricao", new_column_name="observacao")
