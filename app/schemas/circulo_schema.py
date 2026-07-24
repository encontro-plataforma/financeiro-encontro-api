from typing import Optional

from pydantic import BaseModel


class CirculoResponse(BaseModel):
    id: int
    nome: str
    rgb: str

    class Config:
        from_attributes = True


class CirculoCreate(BaseModel):
    nome: str
    rgb: str


class CirculoUpdate(BaseModel):
    nome: Optional[str] = None
    rgb: Optional[str] = None
