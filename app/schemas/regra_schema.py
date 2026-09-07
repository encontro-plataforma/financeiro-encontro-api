from decimal import Decimal

from pydantic import BaseModel, Field

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
    condicoes: list[RegraCondicaoBase] = []


class RegraResponse(RegraBase):
    id: int
    condicoes: list[RegraCondicaoResponse] = []

    class Config:
        from_attributes = True


class RegraGrupoResponse(BaseModel):
    id: int
    nome: str
    descricao: str | None
    escopo: EscopoRegraGrupo
    ordem: int
    ativo: bool
    regras: list[RegraResponse] = []

    class Config:
        from_attributes = True


class RegraGrupoCreate(BaseModel):
    nome: str
    descricao: str | None = None
    escopo: EscopoRegraGrupo
    ordem: int
    ativo: bool = True
    regras: list[RegraBase] = []


class RegraGrupoUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    escopo: EscopoRegraGrupo | None = None
    ordem: int | None = None
    ativo: bool | None = None
    # Substitui a lista inteira de regras (e suas condições) quando informada —
    # editar um grupo na tela envia sempre a árvore completa de volta.
    regras: list[RegraBase] | None = None


class TesteObservacaoRequest(BaseModel):
    nome: str = Field(..., min_length=1)
    observacao: str = Field(..., min_length=1)


class TesteDetalhamentoResponse(BaseModel):
    tipo: TipoDetalhamento
    valor: Decimal
    referencia_id: int | None = None


class TesteRegraResponse(BaseModel):
    nome: str
    forma_pagamento: str
    detalhamentos: list[TesteDetalhamentoResponse]


class TesteObservacaoResponse(BaseModel):
    modelo_extracao: str
    total_gerado: Decimal
    numero_parcelas: Decimal
    regras: list[TesteRegraResponse]
