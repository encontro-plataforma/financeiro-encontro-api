from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Numeric,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM

from app.database.base import Base
from app.models.enums import SituacaoCamisa

situacao_camisa_enum = ENUM(SituacaoCamisa, name="situacao_camisa", create_type=True)


class Encontreiro(Base):
    __tablename__ = "encontreiros"

    id = Column(Integer, primary_key=True)
    dt_inscricao = Column(Date, nullable=True)
    nome = Column(String(150), nullable=False, index=True)
    apelido = Column(String(100), nullable=True)
    instagram = Column(String(100), nullable=True)
    telefone = Column(String(30), nullable=True)
    estado_civil = Column(String(50), nullable=True)
    igreja = Column(String(150), nullable=True)
    religiao = Column(String(100), nullable=True)
    contato_emerg = Column(String(30), nullable=True)
    nome_emerg = Column(String(150), nullable=True)
    parentesco_emerg = Column(String(50), nullable=True)
    alergia_comorbidade = Column(String(255), nullable=True)

    equipe_id = Column(Integer, ForeignKey("equipes.id", ondelete="SET NULL"), nullable=True)

    camisa = Column(String(20), nullable=True)
    situacao_camisa = Column(situacao_camisa_enum, nullable=False, server_default=SituacaoCamisa.SEM_BLUSA.value)
    veiculo = Column(String(100), nullable=True)

    dt_pagamento = Column(Date, nullable=True)
    nome_pagador = Column(String(150), nullable=True)
    pagamento = Column(Numeric(10, 2), nullable=True)
    observacao = Column(String(500), nullable=True)

    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    equipe = relationship("Equipe")

    __table_args__ = (
        UniqueConstraint("nome", "telefone", name="uq_encontreiro_nome_telefone"),
    )
