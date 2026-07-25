from datetime import date
from typing import List, Optional

from app.models.enums import AcessoEquipe, SituacaoCamisa
from app.schemas.query_params import QueryParams


class EncontreiroFilterDto(QueryParams):
    nome: Optional[str] = None
    apelido: Optional[str] = None
    nome_ou_apelido: Optional[str] = None
    equipe_nome: Optional[str] = None
    equipe_acesso: Optional[AcessoEquipe] = None
    equipe_ids: Optional[List[int]] = None
    situacao_camisa: Optional[List[SituacaoCamisa]] = None
    auditado: Optional[bool] = None
    dt_inscricao_inicio: Optional[date] = None
    dt_inscricao_fim: Optional[date] = None
