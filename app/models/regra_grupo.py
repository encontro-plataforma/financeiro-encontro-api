from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base
from app.models.enums import EscopoRegraGrupo

escopo_regra_grupo_enum = ENUM(EscopoRegraGrupo, name="escopo_regra_grupo", create_type=True)


class RegraGrupo(Base):
    __tablename__ = "regra_grupos"

    id = Column(Integer, primary_key=True)
    nome = Column(String(150), nullable=False)
    descricao = Column(String(500), nullable=True)
    # Um único grupo por escopo — o nome do grupo é sempre igual ao escopo.
    escopo = Column(escopo_regra_grupo_enum, nullable=False, unique=True, index=True)
    ordem = Column(Integer, nullable=False)
    ativo = Column(Boolean, nullable=False, server_default="true")
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    regras = relationship(
        "Regra",
        back_populates="regra_grupo",
        order_by="Regra.ordem",
        cascade="all, delete-orphan",
    )
