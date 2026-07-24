from datetime import date
from typing import Optional

from app.schemas.query_params import QueryParams


class EncontristaFilterDto(QueryParams):
    nome: Optional[str] = None
    apelido: Optional[str] = None
    circulo_nome: Optional[str] = None
    camisa: Optional[str] = None
    blusa: Optional[bool] = None
    carta: Optional[bool] = None
    album: Optional[bool] = None
    dt_entrega_inicio: Optional[date] = None
    dt_entrega_fim: Optional[date] = None
    dt_nascimento_inicio: Optional[date] = None
    dt_nascimento_fim: Optional[date] = None
