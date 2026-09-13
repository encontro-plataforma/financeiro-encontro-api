from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import TipoDetalhamento
from app.schemas.lancamento_schema import LancamentoResumo


class DetalhamentoResponse(BaseModel):
    id: int
    lancamento_id: int
    tipo: TipoDetalhamento
    referencia_id: int | None
    valor: Decimal
    descricao: str
    # Calculados na serialização (ver DetalhamentoService): nome de quem foi
    # detalhado (ou "OFERTA"/"OUTRO") e o texto de observação efetivo — pra
    # inscrições, vem ao vivo do Encontreiro/Encontrista referenciado; pra
    # oferta/outro, é o próprio `descricao`.
    detalhe_nome: str = ""
    observacao_efetiva: str = ""
    lancamento: LancamentoResumo | None = None
    criado_em: datetime

    class Config:
        from_attributes = True


class DetalhamentoCreate(BaseModel):
    lancamento_id: int
    tipo: TipoDetalhamento
    referencia_id: int | None = None
    valor: Decimal = Field(..., gt=0)
    descricao: str = ""


class DetalhamentoUpdate(BaseModel):
    lancamento_id: int | None = None
    tipo: TipoDetalhamento | None = None
    referencia_id: int | None = None
    valor: Decimal | None = Field(None, gt=0)
    descricao: str | None = None
