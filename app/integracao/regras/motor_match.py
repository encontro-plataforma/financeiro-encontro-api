from decimal import Decimal
from typing import Optional

from app.integracao.regras.dtos import CandidatoLancamento, PendenciaAuditoria
from app.utils.parse_utils import remover_acentos

_TOLERANCIA = Decimal("0.01")


def selecionar_lancamento(
    pendencia: PendenciaAuditoria,
    candidatos: list[CandidatoLancamento],
) -> Optional[CandidatoLancamento]:
    """Etapa A (Match): entre os candidatos (já filtrados por mesma data e
    tipo RECEITA na consulta ao banco), escolhe o lançamento cuja capacidade
    restante comporta o valor pago e cujo nome do pagador aparece na
    descrição do lançamento. Em caso de empate, vence o de menor id (mais
    antigo)."""
    if not pendencia.nome_pagador:
        return None

    nome_normalizado = remover_acentos(pendencia.nome_pagador).lower()

    validos = [
        candidato for candidato in candidatos
        if candidato.capacidade_restante >= pendencia.pagamento - _TOLERANCIA
        and nome_normalizado in remover_acentos(candidato.descricao or "").lower()
    ]

    if not validos:
        return None

    return min(validos, key=lambda candidato: candidato.id)
