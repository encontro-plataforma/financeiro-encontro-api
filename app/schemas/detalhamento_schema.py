from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import TipoDetalhamento
from app.schemas.lancamento_schema import LancamentoResumo


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
    # Resumo do lançamento vinculado — usado pela listagem de Encontreiros/
    # Encontristas para montar o menu "escolher lançamento" quando a pessoa
    # tem mais de um vínculo, sem precisar de uma chamada extra por lançamento.
    lancamento: Optional[LancamentoResumo] = None

    class Config:
        from_attributes = True


class DetalhamentoVinculoResumo(BaseModel):
    """Um vínculo de inscrição (Encontreiro/Encontrista) com um lançamento,
    já com o resumo do lançamento embutido — usado em
    EncontreiroResponse/EncontristaResponse.detalhamentos_vinculados."""

    id: int
    lancamento_id: int
    tipo: TipoDetalhamento
    valor: Decimal
    lancamento: LancamentoResumo

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
