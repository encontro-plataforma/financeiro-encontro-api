from typing import Optional

from pydantic import BaseModel

from app.models.enums import AcessoEquipe


class EquipeResponse(BaseModel):
    id: int
    nome: str
    acesso: AcessoEquipe

    class Config:
        from_attributes = True


class EquipeCreate(BaseModel):
    nome: str
    acesso: AcessoEquipe


class EquipeUpdate(BaseModel):
    nome: Optional[str] = None
    acesso: Optional[AcessoEquipe] = None
