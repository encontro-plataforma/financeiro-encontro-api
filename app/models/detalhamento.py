from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, case, select
from sqlalchemy.orm import column_property, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM

from app.database.base import Base
from app.models.enums import TipoDetalhamento
from app.models.encontreiro import Encontreiro
from app.models.encontrista import Encontrista
from app.models.lancamento import Lancamento
from app.utils.decimal_utils import TOLERANCIA_VINCULO

tipo_detalhamento_enum = ENUM(TipoDetalhamento, name="tipo_detalhamento", create_type=True)


class Detalhamento(Base):
    __tablename__ = "detalhamentos"

    id = Column(Integer, primary_key=True)
    lancamento_id = Column(Integer, ForeignKey("lancamentos.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo = Column(tipo_detalhamento_enum, nullable=False)
    referencia_id = Column(Integer, nullable=True, index=True)
    valor = Column(Numeric(10, 2), nullable=False)
    # Só usado quando tipo é OFERTA/OUTRO. Para INSCRICAO_*, a "observação"
    # mostrada vem ao vivo do Encontreiro/Encontrista referenciado (sem
    # duplicar/sincronizar texto) — ver DetalhamentoService/AuditoriaService.
    descricao = Column(String(500), nullable=False, server_default="")
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    lancamento = relationship("Lancamento")


# "auditado", "total_vinculado" e "quantidade_vinculos" não são colunas
# persistidas: são calculados via subquery correlacionada em Detalhamento,
# direto no SELECT (sem N+1). Definidos aqui (e não nos models
# Encontreiro/Encontrista) para evitar import circular com Detalhamento.
#
# Fase 1 (pagamentos múltiplos): uma pessoa pode ter vários Detalhamentos de
# inscrição (em lançamentos diferentes, ex. pagamento parcelado). "auditado"
# deixou de ser "existe algum vínculo" e passou a ser "a soma dos vínculos já
# atingiu o pagamento total, dentro da tolerância de R$0,01" — uma pessoa com
# um único Detalhamento parcial permanece não-auditada.
def _soma_vinculos_subquery(tipo, modelo_pessoa):
    return (
        select(func.coalesce(func.sum(Detalhamento.valor), 0))
        .where(
            Detalhamento.tipo == tipo,
            Detalhamento.referencia_id == modelo_pessoa.id,
        )
        .correlate_except(Detalhamento)
        .scalar_subquery()
    )


Encontreiro.total_vinculado = column_property(
    _soma_vinculos_subquery(TipoDetalhamento.INSCRICAO_ENCONTREIRO, Encontreiro)
)

Encontrista.total_vinculado = column_property(
    _soma_vinculos_subquery(TipoDetalhamento.INSCRICAO_ENCONTRISTA, Encontrista)
)

# case() explícito para pagamento IS NULL: sem ele, "total_vinculado >= (NULL - tolerancia)"
# vira SQL NULL, e ".auditado.is_(False)" (usado pelos repositórios e pelo
# AuditoriaService) deixaria de casar essas linhas.
Encontreiro.auditado = column_property(
    case(
        (Encontreiro.pagamento.is_(None), False),
        else_=Encontreiro.total_vinculado >= (Encontreiro.pagamento - TOLERANCIA_VINCULO),
    )
)

Encontrista.auditado = column_property(
    case(
        (Encontrista.pagamento.is_(None), False),
        else_=Encontrista.total_vinculado >= (Encontrista.pagamento - TOLERANCIA_VINCULO),
    )
)


def _saldo_pendente_expr(tipo, modelo_pessoa):
    soma = _soma_vinculos_subquery(tipo, modelo_pessoa)
    return case(
        (modelo_pessoa.pagamento.is_(None), None),
        else_=func.greatest(modelo_pessoa.pagamento - soma, 0),
    )


Encontreiro.saldo_pendente = column_property(
    _saldo_pendente_expr(TipoDetalhamento.INSCRICAO_ENCONTREIRO, Encontreiro)
)

Encontrista.saldo_pendente = column_property(
    _saldo_pendente_expr(TipoDetalhamento.INSCRICAO_ENCONTRISTA, Encontrista)
)


def _quantidade_vinculos_subquery(tipo, modelo_pessoa):
    return (
        select(func.count(Detalhamento.id))
        .where(
            Detalhamento.tipo == tipo,
            Detalhamento.referencia_id == modelo_pessoa.id,
        )
        .correlate_except(Detalhamento)
        .scalar_subquery()
    )


Encontreiro.quantidade_vinculos = column_property(
    _quantidade_vinculos_subquery(TipoDetalhamento.INSCRICAO_ENCONTREIRO, Encontreiro)
)

Encontrista.quantidade_vinculos = column_property(
    _quantidade_vinculos_subquery(TipoDetalhamento.INSCRICAO_ENCONTRISTA, Encontrista)
)

# Id do lançamento vinculado (ou NULL) — usado pela listagem pra saber, sem N+1,
# se deve mostrar o botão "Ver Lançamento Vinculado". Com múltiplos vínculos,
# representa o mais antigo (criado_em asc) — mesmo critério usado por
# vinculo_pessoa_service.enriquecer_vinculos() para popular os campos legados
# no detalhe, para os dois nunca divergirem. O detalhe completo de todos os
# vínculos (detalhamentos_vinculados) só vem no get_by_id.
Encontreiro.lancamento_vinculado_id = column_property(
    select(Detalhamento.lancamento_id)
    .where(
        Detalhamento.tipo == TipoDetalhamento.INSCRICAO_ENCONTREIRO,
        Detalhamento.referencia_id == Encontreiro.id,
    )
    .order_by(Detalhamento.criado_em.asc())
    .limit(1)
    .correlate_except(Detalhamento)
    .scalar_subquery()
)

Encontrista.lancamento_vinculado_id = column_property(
    select(Detalhamento.lancamento_id)
    .where(
        Detalhamento.tipo == TipoDetalhamento.INSCRICAO_ENCONTRISTA,
        Detalhamento.referencia_id == Encontrista.id,
    )
    .order_by(Detalhamento.criado_em.asc())
    .limit(1)
    .correlate_except(Detalhamento)
    .scalar_subquery()
)

# Mesmo motivo/padrão acima: evita N+1 nos cards de conciliação, que
# precisam saber quantos Detalhamentos e qual a soma já vinculados a
# cada Lancamento sem uma chamada extra por card.
Lancamento.quantidade_detalhamentos = column_property(
    select(func.count(Detalhamento.id))
    .where(Detalhamento.lancamento_id == Lancamento.id)
    .correlate_except(Detalhamento)
    .scalar_subquery()
)

Lancamento.soma_detalhamentos = column_property(
    select(func.coalesce(func.sum(Detalhamento.valor), 0))
    .where(Detalhamento.lancamento_id == Lancamento.id)
    .correlate_except(Detalhamento)
    .scalar_subquery()
)
