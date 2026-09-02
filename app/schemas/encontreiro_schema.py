from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from app.models.enums import SituacaoCamisa
from app.schemas.detalhamento_schema import DetalhamentoVinculoResumo
from app.schemas.equipe_schema import EquipeResponse
from app.schemas.lancamento_schema import LancamentoResumo


class EncontreiroResponse(BaseModel):
    id: int
    dt_inscricao: Optional[date]
    nome: str
    apelido: Optional[str]
    instagram: Optional[str]
    telefone: Optional[str]
    estado_civil: Optional[str]
    igreja: Optional[str]
    religiao: Optional[str]
    contato_emerg: Optional[str]
    nome_emerg: Optional[str]
    parentesco_emerg: Optional[str]
    alergia_comorbidade: Optional[str]
    equipe_id: Optional[int]
    equipe: Optional[EquipeResponse]
    camisa: Optional[str]
    situacao_camisa: SituacaoCamisa
    veiculo: Optional[str]
    dt_pagamento: Optional[date]
    nome_pagador: Optional[str]
    pagamento: Optional[Decimal]
    observacao: Optional[str]
    criado_em: datetime
    auditado: bool
    # Campos legados (compatibilidade) — representam sempre o vínculo mais
    # antigo (criado_em asc), mesmo quando há vários. Preferir os campos
    # abaixo para lidar com múltiplos pagamentos.
    detalhamento_id: Optional[int] = None
    lancamento_vinculado_id: Optional[int] = None
    lancamento_vinculado: Optional[LancamentoResumo] = None
    # Só vêm populados no GET /encontreiros/{id} (detalhe); na listagem ficam
    # como [] — não significa "sem vínculos", só "não carregado nesta resposta".
    detalhamentos_vinculados: list[DetalhamentoVinculoResumo] = []
    lancamentos_vinculados: list[LancamentoResumo] = []
    total_vinculado: Decimal = Decimal("0")
    saldo_pendente: Optional[Decimal] = None
    quantidade_vinculos: int = 0

    class Config:
        from_attributes = True


class EncontreiroCreate(BaseModel):
    dt_inscricao: Optional[date] = None
    nome: str
    apelido: Optional[str] = None
    instagram: Optional[str] = None
    telefone: Optional[str] = None
    estado_civil: Optional[str] = None
    igreja: Optional[str] = None
    religiao: Optional[str] = None
    contato_emerg: Optional[str] = None
    nome_emerg: Optional[str] = None
    parentesco_emerg: Optional[str] = None
    alergia_comorbidade: Optional[str] = None
    equipe_id: int
    camisa: Optional[str] = None
    situacao_camisa: SituacaoCamisa = SituacaoCamisa.SEM_BLUSA
    veiculo: Optional[str] = None
    dt_pagamento: Optional[date] = None
    nome_pagador: Optional[str] = None
    pagamento: Optional[Decimal] = None
    observacao: Optional[str] = None


class EncontreiroUpdate(BaseModel):
    dt_inscricao: Optional[date] = None
    nome: Optional[str] = None
    apelido: Optional[str] = None
    instagram: Optional[str] = None
    telefone: Optional[str] = None
    estado_civil: Optional[str] = None
    igreja: Optional[str] = None
    religiao: Optional[str] = None
    contato_emerg: Optional[str] = None
    nome_emerg: Optional[str] = None
    parentesco_emerg: Optional[str] = None
    alergia_comorbidade: Optional[str] = None
    equipe_id: Optional[int] = None
    camisa: Optional[str] = None
    situacao_camisa: Optional[SituacaoCamisa] = None
    veiculo: Optional[str] = None
    dt_pagamento: Optional[date] = None
    nome_pagador: Optional[str] = None
    pagamento: Optional[Decimal] = None
    observacao: Optional[str] = None
