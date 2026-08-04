from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base
from app.models.enums import TipoDetalhamento
from app.models.detalhamento import tipo_detalhamento_enum


class RegraCondicao(Base):
    __tablename__ = "regra_condicoes"

    id = Column(Integer, primary_key=True)
    regra_id = Column(Integer, ForeignKey("regras.id", ondelete="CASCADE"), nullable=False, index=True)
    ordem = Column(Integer, nullable=False)
    # Regex com 1 grupo de captura numérico: o valor do Detalhamento gerado
    # quando o padrão for encontrado na observação da pendência avaliada.
    padrao_regex = Column(String(500), nullable=False)
    tipo_detalhamento_resultado = Column(tipo_detalhamento_enum, nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    regra = relationship("Regra", back_populates="condicoes")
