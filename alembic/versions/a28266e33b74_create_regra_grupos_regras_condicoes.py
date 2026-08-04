"""create regra_grupos, regras e regra_condicoes

Revision ID: a28266e33b74
Revises: 68cef3548c60
Create Date: 2026-08-04 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a28266e33b74"
down_revision: Union[str, None] = "68cef3548c60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "regra_grupos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("descricao", sa.String(500), nullable=True),
        sa.Column(
            "escopo",
            postgresql.ENUM("EXTRACAO_ENCONTREIRO", "EXTRACAO_ENCONTRISTA", name="escopo_regra_grupo"),
            nullable=False,
        ),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_regra_grupos_escopo"), "regra_grupos", ["escopo"], unique=False)

    op.create_table(
        "regras",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("regra_grupo_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["regra_grupo_id"], ["regra_grupos.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_regras_regra_grupo_id"), "regras", ["regra_grupo_id"], unique=False)

    op.create_table(
        "regra_condicoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("regra_id", sa.Integer(), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column("padrao_regex", sa.String(500), nullable=False),
        sa.Column(
            "tipo_detalhamento_resultado",
            postgresql.ENUM(
                "INSCRICAO_ENCONTREIRO", "INSCRICAO_ENCONTRISTA", "OFERTA", "OUTRO",
                name="tipo_detalhamento",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["regra_id"], ["regras.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_regra_condicoes_regra_id"), "regra_condicoes", ["regra_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_regra_condicoes_regra_id"), table_name="regra_condicoes")
    op.drop_table("regra_condicoes")

    op.drop_index(op.f("ix_regras_regra_grupo_id"), table_name="regras")
    op.drop_table("regras")

    op.drop_index(op.f("ix_regra_grupos_escopo"), table_name="regra_grupos")
    op.drop_table("regra_grupos")

    op.execute("DROP TYPE IF EXISTS escopo_regra_grupo")
