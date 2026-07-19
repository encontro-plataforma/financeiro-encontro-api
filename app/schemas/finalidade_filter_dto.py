from typing import Optional

from app.models.enums import TipoLancamento
from app.schemas.query_params import QueryParams


class FinalidadeFilterDto(QueryParams):
    nome: Optional[str] = None
    tipo: Optional[TipoLancamento] = None
