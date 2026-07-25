"""create detalhamentos

Revision ID: f4a7c9e2b380
Revises: e6f8b2c1d4a7
Create Date: 2026-07-24 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f4a7c9e2b380"
down_revision: Union[str, None] = "e6f8b2c1d4a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "detalhamentos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lancamento_id", sa.Integer(), nullable=False),
        sa.Column(
            "tipo",
            postgresql.ENUM(
                "INSCRICAO_ENCONTREIRO", "INSCRICAO_ENCONTRISTA", "OFERTA", "OUTRO",
                name="tipo_detalhamento",
            ),
            nullable=False,
        ),
        sa.Column("referencia_id", sa.Integer(), nullable=True),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column("observacao", sa.String(500), server_default="", nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["lancamento_id"], ["lancamentos.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_detalhamentos_lancamento_id"), "detalhamentos", ["lancamento_id"], unique=False)
    op.create_index(op.f("ix_detalhamentos_referencia_id"), "detalhamentos", ["referencia_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_detalhamentos_referencia_id"), table_name="detalhamentos")
    op.drop_index(op.f("ix_detalhamentos_lancamento_id"), table_name="detalhamentos")
    op.drop_table("detalhamentos")
