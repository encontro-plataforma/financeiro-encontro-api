from typing import Optional

from app.schemas.query_params import QueryParams


class UsuarioFilterDto(QueryParams):
    nome: Optional[str] = None
    email: Optional[str] = None
    nomeOrEmail: Optional[str] = None
    ativo: Optional[bool] = None
    perfil: Optional[str] = None
