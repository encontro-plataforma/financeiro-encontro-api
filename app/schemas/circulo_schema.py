from typing import Optional

from pydantic import BaseModel


class CirculoResponse(BaseModel):
    id: int
    nome: str
    rgb: str
    cancelado: bool = False

    class Config:
        from_attributes = True


class CirculoCreate(BaseModel):
    nome: str
    rgb: str
    cancelado: bool = False


class CirculoUpdate(BaseModel):
    nome: Optional[str] = None
    rgb: Optional[str] = None
    cancelado: Optional[bool] = None
