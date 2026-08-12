from typing import Optional

from app.models.enums import EscopoRegraGrupo
from app.schemas.query_params import QueryParams


class RegraGrupoFilterDto(QueryParams):
    escopo: Optional[EscopoRegraGrupo] = None
    ativo: Optional[bool] = None
    nome: Optional[str] = None
