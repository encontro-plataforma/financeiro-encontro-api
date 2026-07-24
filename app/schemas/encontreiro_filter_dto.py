from datetime import date
from typing import Optional

from app.models.enums import AcessoEquipe
from app.schemas.query_params import QueryParams


class EncontreiroFilterDto(QueryParams):
    nome: Optional[str] = None
    apelido: Optional[str] = None
    equipe_nome: Optional[str] = None
    equipe_acesso: Optional[AcessoEquipe] = None
    dt_inscricao_inicio: Optional[date] = None
    dt_inscricao_fim: Optional[date] = None
