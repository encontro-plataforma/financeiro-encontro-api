from typing import Optional

from app.models.enums import TipoDetalhamento
from app.schemas.query_params import QueryParams


class DetalhamentoFilterDto(QueryParams):
    lancamento_id: Optional[int] = None
    tipo: Optional[TipoDetalhamento] = None
    referencia_id: Optional[int] = None
