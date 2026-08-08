from typing import List, Optional

from pydantic import BaseModel

from app.models.enums import EscopoRegraGrupo, ModoExtracaoRegra, TipoDetalhamento


class RegraCondicaoBase(BaseModel):
    ordem: int
    padrao_regex: str


class RegraCondicaoResponse(RegraCondicaoBase):
    id: int

    class Config:
        from_attributes = True


class RegraBase(BaseModel):
    nome: str
    ordem: int
    ativo: bool = True
    tipo_detalhamento_resultado: TipoDetalhamento
    modo_extracao: ModoExtracaoRegra = ModoExtracaoRegra.TOKEN_VALOR
    condicoes: List[RegraCondicaoBase] = []


class RegraResponse(RegraBase):
    id: int
    condicoes: List[RegraCondicaoResponse] = []

    class Config:
        from_attributes = True


class RegraGrupoResponse(BaseModel):
    id: int
    nome: str
    descricao: Optional[str]
    escopo: EscopoRegraGrupo
    ordem: int
    ativo: bool
    regras: List[RegraResponse] = []

    class Config:
        from_attributes = True


class RegraGrupoCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    escopo: EscopoRegraGrupo
    ordem: int
    ativo: bool = True
    regras: List[RegraBase] = []


class RegraGrupoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    escopo: Optional[EscopoRegraGrupo] = None
    ordem: Optional[int] = None
    ativo: Optional[bool] = None
    # Substitui a lista inteira de regras (e suas condições) quando informada —
    # editar um grupo na tela envia sempre a árvore completa de volta.
    regras: Optional[List[RegraBase]] = None
