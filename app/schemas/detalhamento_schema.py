from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import TipoDetalhamento


class DetalhamentoResponse(BaseModel):
    id: int
    lancamento_id: int
    tipo: TipoDetalhamento
    referencia_id: Optional[int]
    valor: Decimal
    descricao: str
    # Calculados na serialização (ver DetalhamentoService): nome de quem foi
    # detalhado (ou "OFERTA"/"OUTRO") e o texto de observação efetivo — pra
    # inscrições, vem ao vivo do Encontreiro/Encontrista referenciado; pra
    # oferta/outro, é o próprio `descricao`.
    detalhe_nome: str = ""
    observacao_efetiva: str = ""
    criado_em: datetime

    class Config:
        from_attributes = True


class DetalhamentoCreate(BaseModel):
    lancamento_id: int
    tipo: TipoDetalhamento
    referencia_id: Optional[int] = None
    valor: Decimal = Field(..., gt=0)
    descricao: str = ""


class DetalhamentoUpdate(BaseModel):
    lancamento_id: Optional[int] = None
    tipo: Optional[TipoDetalhamento] = None
    referencia_id: Optional[int] = None
    valor: Optional[Decimal] = Field(None, gt=0)
    descricao: Optional[str] = None
