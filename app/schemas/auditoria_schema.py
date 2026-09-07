from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from app.models.enums import FormaPagamento, TipoDetalhamento


class InscricaoResumoDto(BaseModel):
    id: int
    nome: str
    tipo: str  # "ENCONTREIRO" | "ENCONTRISTA"
    # Valor total registrado como pagamento da própria pessoa — pode ser
    # maior que o `valor` do Detalhamento quando o pagamento é compartilhado
    # (ex.: duas pessoas registradas com o mesmo valor total da transação).
    pagamento: Optional[Decimal] = None
    observacao: Optional[str] = None


class ItemDetalhamentoSimuladoDto(BaseModel):
    tipo: TipoDetalhamento
    valor: Decimal
    referencia_id: Optional[int]
    descricao: str = ""
    origem: str  # "EXISTENTE" | "SIMULADO"
    # Nome da Regra que gerou o item (só para origem=SIMULADO); "FALLBACK"
    # quando nenhuma regra bateu e o valor bruto registrado foi usado; None
    # para origem=EXISTENTE, cuja regra de origem não é rastreada.
    regra: Optional[str] = None
    inscricao: Optional[InscricaoResumoDto] = None


class PendenciaNaoIncluidaDto(BaseModel):
    tipo: str  # "ENCONTREIRO" | "ENCONTRISTA"
    id: int
    nome: str
    pagamento: Optional[Decimal] = None
    observacao: Optional[str] = None
    motivo: str


class SimulacaoAuditoriaResponse(BaseModel):
    lancamento_id: int
    descricao: str
    data_pagamento: datetime
    valor: Decimal
    forma_pagamento: FormaPagamento
    parcelas: Optional[int] = None
    status_lancamento: str
    ja_conciliado: bool
    detalhamentos: list[ItemDetalhamentoSimuladoDto]
    nao_incluidos: list[PendenciaNaoIncluidaDto]
