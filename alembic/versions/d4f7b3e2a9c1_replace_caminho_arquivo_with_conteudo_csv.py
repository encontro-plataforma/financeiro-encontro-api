"""replace caminho_arquivo with conteudo_csv

Revision ID: d4f7b3e2a9c1
Revises: b2e4a8f1c6d3
Create Date: 2026-06-17 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4f7b3e2a9c1"
down_revision: Union[str, None] = "b2e4a8f1c6d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("extratos_bancarios", sa.Column("conteudo_csv", sa.Text(), nullable=True))
    op.drop_column("extratos_bancarios", "caminho_arquivo")


def downgrade() -> None:
    op.add_column("extratos_bancarios", sa.Column("caminho_arquivo", sa.String(500), nullable=True))
    op.drop_column("extratos_bancarios", "conteudo_csv")
