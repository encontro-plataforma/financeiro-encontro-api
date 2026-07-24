"""create equipes e circulos, add SECRETARIO ao perfil_usuario

Revision ID: 9c3d7e2f4a81
Revises: f1a2b3c4d5e6
Create Date: 2026-07-24 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "9c3d7e2f4a81"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "equipes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column(
            "acesso",
            postgresql.ENUM("EDG", "VERMELHO", "AMARELO", "VERDE", name="acesso_equipe"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_equipes_id"), "equipes", ["id"], unique=False)
    op.create_index(op.f("ix_equipes_nome"), "equipes", ["nome"], unique=False)

    op.create_table(
        "circulos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("rgb", sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_circulos_id"), "circulos", ["id"], unique=False)
    op.create_index(op.f("ix_circulos_nome"), "circulos", ["nome"], unique=False)

    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE perfil_usuario ADD VALUE IF NOT EXISTS 'SECRETARIO'")


def downgrade() -> None:
    op.drop_index(op.f("ix_circulos_nome"), table_name="circulos")
    op.drop_index(op.f("ix_circulos_id"), table_name="circulos")
    op.drop_table("circulos")

    op.drop_index(op.f("ix_equipes_nome"), table_name="equipes")
    op.drop_index(op.f("ix_equipes_id"), table_name="equipes")
    op.drop_table("equipes")

    # Nota: o Postgres não suporta remover um valor de enum (ALTER TYPE ... DROP VALUE),
    # então o downgrade não reverte a adição de 'SECRETARIO' ao enum perfil_usuario.
