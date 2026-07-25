from typing import Optional

from app.models.enums import AcessoEquipe
from app.schemas.query_params import QueryParams


class EquipeFilterDto(QueryParams):
    nome: Optional[str] = None
    acesso: Optional[AcessoEquipe] = None
