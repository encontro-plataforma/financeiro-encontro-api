from datetime import datetime
from typing import List, Optional

from fastapi import Query

from app.models.enums import FormaPagamento, StatusLancamento, TipoLancamento


class DashboardFilterDto:
    def __init__(
        self,
        data_inicio: Optional[datetime] = Query(None, description="Data inicial do período"),
        data_fim: Optional[datetime] = Query(None, description="Data final do período"),
        forma_pagamento: Optional[List[FormaPagamento]] = Query(None, description="Uma ou mais formas de pagamento"),
        finalidade_id: Optional[List[int]] = Query(None, description="Um ou mais IDs de finalidade"),
        tipo: Optional[TipoLancamento] = Query(None, description="RECEITA ou DESPESA"),
        status: Optional[StatusLancamento] = Query(None, description="CONCILIADO ou NAO_CONCILIADO"),
    ):
        self.data_inicio = data_inicio
        self.data_fim = data_fim
        self.forma_pagamento = forma_pagamento
        self.finalidade_id = finalidade_id
        self.tipo = tipo
        self.status = status
