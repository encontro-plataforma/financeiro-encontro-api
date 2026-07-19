"""add tipo to finalidades

Revision ID: b2e4a8f1c6d3
Revises: a7f3c9d2e1b8
Create Date: 2026-06-16 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b2e4a8f1c6d3'
down_revision: Union[str, Sequence[str], None] = 'a7f3c9d2e1b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Adiciona coluna tipo reutilizando o enum tipo_lancamento já existente no PostgreSQL
    op.add_column('finalidades',
        sa.Column(
            'tipo',
            sa.Enum('RECEITA', 'DESPESA', name='tipo_lancamento', create_type=False),
            nullable=False,
            server_default='RECEITA',
        )
    )

    # 2. Remove o índice único em nome (para permitir "OUTROS" em RECEITA e DESPESA)
    op.drop_index('ix_finalidades_nome', table_name='finalidades')

    # 3. Recria índice simples em nome (para performance de busca)
    op.create_index('ix_finalidades_nome', 'finalidades', ['nome'], unique=False)

    # 4. Unicidade passa a ser (nome, tipo) — mesma finalidade não se repete dentro do mesmo tipo
    op.create_unique_constraint('uq_finalidades_nome_tipo', 'finalidades', ['nome', 'tipo'])


def downgrade() -> None:
    op.drop_constraint('uq_finalidades_nome_tipo', 'finalidades', type_='unique')
    op.drop_index('ix_finalidades_nome', table_name='finalidades')
    op.create_index('ix_finalidades_nome', 'finalidades', ['nome'], unique=True)
    op.drop_column('finalidades', 'tipo')
