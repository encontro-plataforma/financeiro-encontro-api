from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from app.models.enums import TipoDetalhamento


class DetalhamentoResponse(BaseModel):
    id: int
    lancamento_id: int
    tipo: TipoDetalhamento
    referencia_id: Optional[int]
    valor: Decimal
    observacao: str
    criado_em: datetime

    class Config:
        from_attributes = True


class DetalhamentoCreate(BaseModel):
    lancamento_id: int
    tipo: TipoDetalhamento
    referencia_id: Optional[int] = None
    valor: Decimal
    observacao: str = ""


class DetalhamentoUpdate(BaseModel):
    lancamento_id: Optional[int] = None
    tipo: Optional[TipoDetalhamento] = None
    referencia_id: Optional[int] = None
    valor: Optional[Decimal] = None
    observacao: Optional[str] = None
