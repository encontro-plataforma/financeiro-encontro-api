"""add modo_extracao to regras

Revision ID: afc6df80dffc
Revises: a28266e33b74
Create Date: 2026-08-05 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "afc6df80dffc"
down_revision: Union[str, None] = "a28266e33b74"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    modo_extracao_regra = postgresql.ENUM(
        "TOKEN_VALOR", "NOME_NA_LISTA",
        name="modo_extracao_regra",
    )
    modo_extracao_regra.create(op.get_bind())

    op.add_column(
        "regras",
        sa.Column(
            "modo_extracao",
            modo_extracao_regra,
            server_default="TOKEN_VALOR",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("regras", "modo_extracao")
    op.execute("DROP TYPE IF EXISTS modo_extracao_regra")
