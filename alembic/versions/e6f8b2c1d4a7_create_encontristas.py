"""create encontristas

Revision ID: e6f8b2c1d4a7
Revises: d3a4c6e9b125
Create Date: 2026-07-24 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e6f8b2c1d4a7"
down_revision: Union[str, None] = "d3a4c6e9b125"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "encontristas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dt_entrega", sa.Date(), nullable=True),
        sa.Column("dt_validade", sa.Date(), nullable=True),
        sa.Column("padrinho_id", sa.Integer(), nullable=False),
        sa.Column("carta", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("album", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("apelido", sa.String(100), nullable=True),
        sa.Column("dt_nascimento", sa.Date(), nullable=True),
        sa.Column("idade", sa.Integer(), nullable=True),
        sa.Column("circulo_id", sa.Integer(), nullable=True),
        sa.Column("instagram", sa.String(100), nullable=True),
        sa.Column("contato", sa.String(30), nullable=True),
        sa.Column("religiao", sa.String(100), nullable=True),
        sa.Column("igreja", sa.String(150), nullable=True),
        sa.Column("endereco", sa.String(255), nullable=True),
        sa.Column("cidade", sa.String(100), nullable=True),
        sa.Column("camisa", sa.String(20), nullable=True),
        sa.Column("blusa", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("veiculo", sa.String(100), nullable=True),
        sa.Column("contato_emerg", sa.String(30), nullable=True),
        sa.Column("nome_emerg", sa.String(150), nullable=True),
        sa.Column("parentesco_emerg", sa.String(50), nullable=True),
        sa.Column("medicacao", sa.String(255), nullable=True),
        sa.Column("alergia_comorbidade", sa.String(255), nullable=True),
        sa.Column("dt_pagamento", sa.Date(), nullable=True),
        sa.Column("nome_pagador", sa.String(150), nullable=True),
        sa.Column("pagamento", sa.Numeric(10, 2), nullable=True),
        sa.Column("observacao", sa.String(500), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["padrinho_id"], ["encontreiros.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["circulo_id"], ["circulos.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_encontristas_nome"), "encontristas", ["nome"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_encontristas_nome"), table_name="encontristas")
    op.drop_table("encontristas")
