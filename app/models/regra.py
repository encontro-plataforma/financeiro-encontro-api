from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Regra(Base):
    __tablename__ = "regras"

    id = Column(Integer, primary_key=True)
    regra_grupo_id = Column(Integer, ForeignKey("regra_grupos.id", ondelete="CASCADE"), nullable=False, index=True)
    nome = Column(String(150), nullable=False)
    ordem = Column(Integer, nullable=False)
    ativo = Column(Boolean, nullable=False, server_default="true")
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    regra_grupo = relationship("RegraGrupo", back_populates="regras")
    condicoes = relationship(
        "RegraCondicao",
        back_populates="regra",
        order_by="RegraCondicao.ordem",
        cascade="all, delete-orphan",
    )
