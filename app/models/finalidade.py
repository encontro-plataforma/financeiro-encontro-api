from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base
from app.models.enums import TipoLancamento


class Finalidade(Base):
    __tablename__ = "finalidades"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, index=True)
    descricao = Column(String(255), nullable=True)
    ativo = Column(Boolean, default=True)
    tipo = Column(
        SAEnum(TipoLancamento, name='tipo_lancamento', create_type=False),
        nullable=False,
        default=TipoLancamento.RECEITA,
    )
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())

    lancamentos = relationship(
        "Lancamento",
        foreign_keys="Lancamento.finalidade_id",
        back_populates="finalidade",
    )
