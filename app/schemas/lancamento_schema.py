from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import FormaPagamento, StatusLancamento, TipoLancamento
from app.schemas.finalidade_schema import FinalidadeResponse


class LancamentoBase(BaseModel):
    descricao: str = Field(..., min_length=3, max_length=255)
    valor: float = Field(..., gt=0)
    tipo: TipoLancamento
    forma_pagamento: FormaPagamento
    data_pagamento: datetime
    finalidade_id: int | None
    sugestao_finalidade: int | None = None
    observacao: str | None = None
    cart_taxa: float | None = None
    cart_valor_liquido: float | None = None
    cart_parcelas: int | None = None


class LancamentoCreate(LancamentoBase):
    pass


class DetalhamentoFinalDto(BaseModel):
    descricao: str = Field(..., min_length=1, max_length=500)


class LancamentoConciliarRequest(BaseModel):
    observacao: str | None = None
    detalhamento_final: DetalhamentoFinalDto | None = None


class LancamentoUpdate(BaseModel):
    descricao: str | None = None
    valor: float | None = None
    tipo: TipoLancamento | None = None
    forma_pagamento: FormaPagamento | None = None
    status: StatusLancamento | None = None
    data_pagamento: datetime | None = None
    finalidade_id: int | None = None
    observacao: str | None = None
    cart_taxa: float | None = None
    cart_valor_liquido: float | None = None
    cart_parcelas: int | None = None


class LancamentoResumo(BaseModel):
    id: int
    descricao: str
    valor: float
    data_pagamento: datetime
    status: StatusLancamento
    forma_pagamento: FormaPagamento

    class Config:
        from_attributes = True


class LancamentoResponse(LancamentoBase):
    id: int
    status: StatusLancamento
    finalidade: FinalidadeResponse | None = None
    sugestao_finalidade: FinalidadeResponse | None = None
    quantidade_detalhamentos: int = 0
    soma_detalhamentos: float = 0

    criado_em: datetime
    atualizado_em: datetime | None = None

    class Config:
        from_attributes = True
