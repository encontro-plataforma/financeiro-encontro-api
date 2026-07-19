from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.enums import TipoLancamento, FormaPagamento, StatusLancamento
from app.schemas.finalidade_schema import FinalidadeResponse


class LancamentoBase(BaseModel):
    descricao: str = Field(..., min_length=3, max_length=255)
    valor: float = Field(..., gt=0)
    tipo: TipoLancamento
    forma_pagamento: FormaPagamento
    data_pagamento: datetime
    finalidade_id: Optional[int]
    sugestao_finalidade: Optional[int] = None
    observacao: Optional[str] = None


class LancamentoCreate(LancamentoBase):
    pass


class LancamentoConciliarRequest(BaseModel):
    observacao: Optional[str] = None


class LancamentoUpdate(BaseModel):
    descricao: Optional[str] = None
    valor: Optional[float] = None
    tipo: Optional[TipoLancamento] = None
    forma_pagamento: Optional[FormaPagamento] = None
    status: Optional[StatusLancamento] = None
    data_pagamento: Optional[datetime] = None
    finalidade_id: Optional[int] = None
    observacao: Optional[str] = None


class LancamentoResponse(LancamentoBase):
    id: int
    status: StatusLancamento
    finalidade: Optional[FinalidadeResponse] = None
    sugestao_finalidade: Optional[FinalidadeResponse] = None

    criado_em: datetime
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True