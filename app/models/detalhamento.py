from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, and_, exists, select
from sqlalchemy.orm import column_property, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM

from app.database.base import Base
from app.models.enums import TipoDetalhamento
from app.models.encontreiro import Encontreiro
from app.models.encontrista import Encontrista
from app.models.lancamento import Lancamento

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


# "auditado" não é uma coluna persistida: é calculado via EXISTS correlacionado
# em Detalhamento, direto no SELECT (sem N+1). Definido aqui (e não nos models
# Encontreiro/Encontrista) para evitar import circular com Detalhamento.
Encontreiro.auditado = column_property(
    exists().where(
        and_(
            Detalhamento.tipo == TipoDetalhamento.INSCRICAO_ENCONTREIRO,
            Detalhamento.referencia_id == Encontreiro.id,
        )
    )
)

Encontrista.auditado = column_property(
    exists().where(
        and_(
            Detalhamento.tipo == TipoDetalhamento.INSCRICAO_ENCONTRISTA,
            Detalhamento.referencia_id == Encontrista.id,
        )
    )
)

# Id do lançamento vinculado (ou NULL) — usado pela listagem pra saber, sem N+1,
# se deve mostrar o botão "Ver Lançamento Vinculado". O detalhe completo
# (lancamento_vinculado) continua vindo só no get_by_id, via join explícito.
Encontreiro.lancamento_vinculado_id = column_property(
    select(Detalhamento.lancamento_id)
    .where(
        Detalhamento.tipo == TipoDetalhamento.INSCRICAO_ENCONTREIRO,
        Detalhamento.referencia_id == Encontreiro.id,
    )
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
