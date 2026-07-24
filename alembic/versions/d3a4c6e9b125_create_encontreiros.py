"""create encontreiros

Revision ID: d3a4c6e9b125
Revises: b7d1e4f8a293
Create Date: 2026-07-24 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d3a4c6e9b125"
down_revision: Union[str, None] = "b7d1e4f8a293"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "encontreiros",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dt_inscricao", sa.Date(), nullable=True),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("apelido", sa.String(100), nullable=True),
        sa.Column("instagram", sa.String(100), nullable=True),
        sa.Column("telefone", sa.String(30), nullable=True),
        sa.Column("estado_civil", sa.String(50), nullable=True),
        sa.Column("igreja", sa.String(150), nullable=True),
        sa.Column("religiao", sa.String(100), nullable=True),
        sa.Column("contato_emerg", sa.String(30), nullable=True),
        sa.Column("nome_emerg", sa.String(150), nullable=True),
        sa.Column("parentesco_emerg", sa.String(50), nullable=True),
        sa.Column("alergia_comorbidade", sa.String(255), nullable=True),
        sa.Column("equipe_id", sa.Integer(), nullable=True),
        sa.Column("camisa", sa.String(20), nullable=True),
        sa.Column(
            "situacao_camisa",
            postgresql.ENUM(
                "PENDENTE", "SOLICITADA", "RECEBIDA", "ENTREGUE", "SEM_BLUSA",
                name="situacao_camisa",
            ),
            nullable=False,
            server_default="SEM_BLUSA",
        ),
        sa.Column("veiculo", sa.String(100), nullable=True),
        sa.Column("dt_pagamento", sa.Date(), nullable=True),
        sa.Column("nome_pagador", sa.String(150), nullable=True),
        sa.Column("pagamento", sa.Numeric(10, 2), nullable=True),
        sa.Column("observacao", sa.String(500), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["equipe_id"], ["equipes.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("nome", "telefone", name="uq_encontreiro_nome_telefone"),
    )
    op.create_index(op.f("ix_encontreiros_nome"), "encontreiros", ["nome"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_encontreiros_nome"), table_name="encontreiros")
    op.drop_table("encontreiros")
