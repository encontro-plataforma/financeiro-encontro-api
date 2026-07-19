from datetime import datetime
from typing import Optional, List

from app.models.enums import FormaPagamento, StatusLancamento, TipoLancamento
from app.schemas.query_params import QueryParams


class LancamentoFilterDto(QueryParams):
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    status: Optional[StatusLancamento] = None
    tipo: Optional[TipoLancamento] = None
    finalidade_id: Optional[int] = None           # scalar — tela de lançamentos (select único)
    finalidade_ids: Optional[List[int]] = None    # lista — injetada pelo router (dashboard)
    forma_pagamento: Optional[List[FormaPagamento]] = None  # injetada pelo router
    descricao: Optional[str] = None
    exclude_ids: Optional[List[int]] = None
