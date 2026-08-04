from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from app.models.enums import TipoDetalhamento


@dataclass
class PendenciaAuditoria:
    """Encontreiro/Encontrista pendente sendo avaliado pela auditoria."""
    id: int
    nome_pagador: Optional[str]
    dt_pagamento: date
    pagamento: Decimal
    observacao: Optional[str]


@dataclass
class CandidatoLancamento:
    """Lancamento RECEITA na mesma data da pendência, candidato ao Match."""
    id: int
    descricao: str
    capacidade_restante: Decimal


@dataclass
class ItemDetalhamento:
    """Um Detalhamento a ser criado (ainda sem lancamento_id — resolvido
    depois que a Etapa A encontra o lançamento)."""
    tipo: TipoDetalhamento
    valor: Decimal
    referencia_id: Optional[int]
