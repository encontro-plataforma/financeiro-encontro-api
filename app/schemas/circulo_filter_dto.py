from typing import Optional

from app.schemas.query_params import QueryParams


class CirculoFilterDto(QueryParams):
    nome: Optional[str] = None
