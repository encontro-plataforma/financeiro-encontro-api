"""add tipo_origem to uploads

Revision ID: 95c95957c2d5
Revises: afc6df80dffc
Create Date: 2026-08-13 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "95c95957c2d5"
down_revision: Union[str, None] = "afc6df80dffc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tipo_origem_upload = postgresql.ENUM(
        "BANCARIO", "ESPECIE", "CARTAO",
        name="tipo_origem_upload",
    )
    tipo_origem_upload.create(op.get_bind())

    op.add_column(
        "uploads",
        sa.Column("tipo_origem", tipo_origem_upload, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("uploads", "tipo_origem")
    op.execute("DROP TYPE IF EXISTS tipo_origem_upload")
