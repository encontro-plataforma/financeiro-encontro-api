from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class RegraCondicao(Base):
    """Um padrão que precisa ser encontrado na observação para que a Regra
    dona desta condição seja considerada "casada" (todas as condições de uma
    mesma Regra combinam com AND). Quando o padrão tem um grupo de captura
    numérico, esse é o valor candidato a virar o Detalhamento da Regra."""

    __tablename__ = "regra_condicoes"

    id = Column(Integer, primary_key=True)
    regra_id = Column(Integer, ForeignKey("regras.id", ondelete="CASCADE"), nullable=False, index=True)
    ordem = Column(Integer, nullable=False)
    padrao_regex = Column(String(500), nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    regra = relationship("Regra", back_populates="condicoes")
