from pydantic import BaseModel
from datetime import datetime


class ExtratoBancarioResponse(BaseModel):
    id: int
    nome_arquivo: str
    tamanho_bytes: int | None
    processado_em: datetime

    class Config:
        from_attributes = True