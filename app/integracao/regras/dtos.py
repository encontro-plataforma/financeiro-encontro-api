from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from app.models.enums import FormaPagamento, TipoDetalhamento


@dataclass
class PendenciaAuditoria:
    """Encontreiro/Encontrista pendente sendo avaliado pela auditoria.
    `nome` é o nome da própria pessoa (usado pelo modo de extração
    NOME_NA_LISTA); `nome_pagador` é quem de fato pagou (usado só na Etapa A
    — pode ser um responsável, diferente de `nome`)."""
    id: int
    nome: str
    nome_pagador: Optional[str]
    dt_pagamento: date
    pagamento: Decimal
    observacao: Optional[str]


@dataclass
class CandidatoLancamento:
    """Lancamento RECEITA na mesma data da pendência, candidato ao Match.
    `valor` é o total original do lançamento (estável mesmo depois que outras
    pessoas já consumiram parte dele); `capacidade_restante` é o que ainda
    sobra para novos Detalhamentos."""
    id: int
    descricao: str
    valor: Decimal
    capacidade_restante: Decimal
    forma_pagamento: FormaPagamento


@dataclass
class ItemDetalhamento:
    """Um Detalhamento a ser criado (ainda sem lancamento_id — resolvido
    depois que a Etapa A encontra o lançamento)."""
    tipo: TipoDetalhamento
    valor: Decimal
    referencia_id: Optional[int]
