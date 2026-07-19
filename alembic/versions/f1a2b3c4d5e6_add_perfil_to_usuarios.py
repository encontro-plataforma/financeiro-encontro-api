"""add perfil to usuarios

Revision ID: f1a2b3c4d5e6
Revises: d4f7b3e2a9c1
Create Date: 2026-06-17 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "d4f7b3e2a9c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

perfil_enum = postgresql.ENUM(
    "ADMINISTRADOR", "CONCILIADOR", "REPORTER",
    name="perfil_usuario",
)


def upgrade() -> None:
    perfil_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "usuarios",
        sa.Column(
            "perfil",
            sa.Enum("ADMINISTRADOR", "CONCILIADOR", "REPORTER", name="perfil_usuario", create_type=False),
            nullable=False,
            server_default="CONCILIADOR",
        ),
    )


def downgrade() -> None:
    op.drop_column("usuarios", "perfil")
    perfil_enum.drop(op.get_bind(), checkfirst=True)
