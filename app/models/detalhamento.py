from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, and_, exists
from sqlalchemy.orm import column_property, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM

from app.database.base import Base
from app.models.enums import TipoDetalhamento
from app.models.encontreiro import Encontreiro
from app.models.encontrista import Encontrista

tipo_detalhamento_enum = ENUM(TipoDetalhamento, name="tipo_detalhamento", create_type=True)


class Detalhamento(Base):
    __tablename__ = "detalhamentos"

    id = Column(Integer, primary_key=True)
    lancamento_id = Column(Integer, ForeignKey("lancamentos.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo = Column(tipo_detalhamento_enum, nullable=False)
    referencia_id = Column(Integer, nullable=True, index=True)
    valor = Column(Numeric(10, 2), nullable=False)
    observacao = Column(String(500), nullable=False, server_default="")
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
