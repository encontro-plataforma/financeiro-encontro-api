from typing import Optional

from pydantic import BaseModel

from app.models.enums import TipoLancamento


class FinalidadeResponse(BaseModel):
    id: int
    nome: str
    descricao: str | None
    tipo: TipoLancamento

    class Config:
        from_attributes = True


class FinalidadeCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    tipo: TipoLancamento


class FinalidadeUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    tipo: Optional[TipoLancamento] = None
