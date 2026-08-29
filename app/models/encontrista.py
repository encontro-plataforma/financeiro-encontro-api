from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Numeric,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Encontrista(Base):
    __tablename__ = "encontristas"

    id = Column(Integer, primary_key=True)
    dt_entrega = Column(Date, nullable=True)
    dt_validade = Column(Date, nullable=True)

    padrinho_id = Column(Integer, ForeignKey("encontreiros.id", ondelete="RESTRICT"), nullable=False)

    carta = Column(Boolean, nullable=False, server_default="false")
    album = Column(Boolean, nullable=False, server_default="false")

    nome = Column(String(150), nullable=False, index=True)
    apelido = Column(String(100), nullable=True)
    dt_nascimento = Column(Date, nullable=True)
    idade = Column(Integer, nullable=True)

    circulo_id = Column(Integer, ForeignKey("circulos.id", ondelete="SET NULL"), nullable=True)

    onde_veio_ficha = Column(String(150), nullable=False, server_default="")

    instagram = Column(String(100), nullable=True)
    contato = Column(String(30), nullable=True)
    religiao = Column(String(100), nullable=True)
    igreja = Column(String(150), nullable=True)
    endereco = Column(String(255), nullable=True)
    cidade = Column(String(100), nullable=True)
    camisa = Column(String(20), nullable=True)
    blusa = Column(Boolean, nullable=False, server_default="false")
    veiculo = Column(String(100), nullable=True)

    contato_emerg = Column(String(30), nullable=True)
    nome_emerg = Column(String(150), nullable=True)
    parentesco_emerg = Column(String(50), nullable=True)
    medicacao = Column(String(255), nullable=True)
    alergia_comorbidade = Column(String(255), nullable=True)

    dt_pagamento = Column(Date, nullable=True)
    nome_pagador = Column(String(150), nullable=True)
    pagamento = Column(Numeric(10, 2), nullable=True)
    observacao = Column(String(500), nullable=True)

    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    padrinho = relationship("Encontreiro")
    circulo = relationship("Circulo")
