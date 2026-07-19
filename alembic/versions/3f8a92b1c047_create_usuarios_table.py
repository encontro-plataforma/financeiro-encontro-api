"""create usuarios table

Revision ID: 3f8a92b1c047
Revises: c6e82d177d5e
Create Date: 2026-05-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '3f8a92b1c047'
down_revision: Union[str, Sequence[str], None] = 'c6e82d177d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'usuarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('senha_hash', sa.String(255), nullable=False),
        sa.Column('ativo', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_usuarios_id'), 'usuarios', ['id'], unique=False)
    op.create_index(op.f('ix_usuarios_email'), 'usuarios', ['email'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_usuarios_email'), table_name='usuarios')
    op.drop_index(op.f('ix_usuarios_id'), table_name='usuarios')
    op.drop_table('usuarios')
