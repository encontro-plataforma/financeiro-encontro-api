"""merge finalidade inscricao encontreiro/encontrista into inscricao

Revision ID: 68cef3548c60
Revises: c9d1f4a7b2e5
Create Date: 2026-07-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "68cef3548c60"
down_revision: Union[str, None] = "c9d1f4a7b2e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ID_INSCRICAO_ENCONTRISTA = 3
_ID_INSCRICAO_ENCONTREIRO = 4


def upgrade() -> None:
    op.execute(
        f"UPDATE lancamentos SET finalidade_id = {_ID_INSCRICAO_ENCONTRISTA} "
        f"WHERE finalidade_id = {_ID_INSCRICAO_ENCONTREIRO}"
    )
    op.execute(
        f"UPDATE lancamentos SET sugestao_finalidade_id = {_ID_INSCRICAO_ENCONTRISTA} "
        f"WHERE sugestao_finalidade_id = {_ID_INSCRICAO_ENCONTREIRO}"
    )
    op.execute(
        f"UPDATE finalidades SET nome = 'INSCRIÇÃO' WHERE id = {_ID_INSCRICAO_ENCONTRISTA}"
    )
    op.execute(f"DELETE FROM finalidades WHERE id = {_ID_INSCRICAO_ENCONTREIRO}")


def downgrade() -> None:
    # NOTA: não é possível recuperar quais lançamentos tinham originalmente
    # finalidade_id=4 ("INSCRIÇÃO ENCONTREIRO") — todos permanecerão com o id 3.
    op.execute(
        f"INSERT INTO finalidades (id, nome, descricao, tipo, ativo) "
        f"VALUES ({_ID_INSCRICAO_ENCONTREIRO}, 'INSCRIÇÃO ENCONTREIRO', "
        f"'Finalidade padrão: INSCRIÇÃO ENCONTREIRO', 'RECEITA', true)"
    )
    op.execute(
        f"UPDATE finalidades SET nome = 'INSCRIÇÃO ENCONTRISTA' WHERE id = {_ID_INSCRICAO_ENCONTRISTA}"
    )
