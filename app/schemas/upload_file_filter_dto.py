from typing import Optional
from datetime import datetime

from app.schemas.query_params import QueryParams

class UploadFileFilterDto(QueryParams):
    nome_arquivo: Optional[str] = None

    processado_em_inicio: Optional[datetime] = None
    processado_em_fim: Optional[datetime] = None
