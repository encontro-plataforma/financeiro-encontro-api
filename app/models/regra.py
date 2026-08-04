from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base
from app.models.detalhamento import tipo_detalhamento_enum


class Regra(Base):
    """Uma Regra avalia a observação de uma pendência: se TODAS as suas
    RegraCondicao derem match (AND), a Regra "casa" e gera exatamente 1
    Detalhamento do tipo `tipo_detalhamento_resultado` (o valor vem do grupo
    de captura da primeira condição, em ordem, que tiver um). Cada Regra do
    grupo é avaliada independentemente contra a mesma observação — várias
    podem casar ao mesmo tempo (ex.: "Regra Inscrição" + "Regra Oferta" na
    mesma observação geram 2 Detalhamentos)."""

    __tablename__ = "regras"

    id = Column(Integer, primary_key=True)
    regra_grupo_id = Column(Integer, ForeignKey("regra_grupos.id", ondelete="CASCADE"), nullable=False, index=True)
    nome = Column(String(150), nullable=False)
    ordem = Column(Integer, nullable=False)
    ativo = Column(Boolean, nullable=False, server_default="true")
    tipo_detalhamento_resultado = Column(tipo_detalhamento_enum, nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    regra_grupo = relationship("RegraGrupo", back_populates="regras")
    condicoes = relationship(
        "RegraCondicao",
        back_populates="regra",
        order_by="RegraCondicao.ordem",
        cascade="all, delete-orphan",
    )
