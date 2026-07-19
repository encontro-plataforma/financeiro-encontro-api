from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM

from app.database.base import Base
from app.models.enums import (
    TipoLancamento,
    FormaPagamento,
    StatusLancamento
)

# ✅ ENUMs definidos (PostgreSQL)
tipo_enum = ENUM(
    TipoLancamento,
    name="tipo_lancamento",
    create_type=True
)

forma_pagamento_enum = ENUM(
    FormaPagamento,
    name="forma_pagamento",
    create_type=True
)

status_enum = ENUM(
    StatusLancamento,
    name="status_lancamento",
    create_type=True
)


class Lancamento(Base):
    __tablename__ = "lancamentos"

    id = Column(Integer, primary_key=True, index=True)
    finalidade_id = Column(Integer, ForeignKey("finalidades.id", ondelete="SET NULL"), nullable=True)
    sugestao_finalidade_id = Column(Integer, ForeignKey("finalidades.id", ondelete="SET NULL"), nullable=True)

    descricao = Column(String(255), nullable=False)
    valor = Column(Float, nullable=False)
    tipo = Column(tipo_enum, nullable=False)
    forma_pagamento = Column(forma_pagamento_enum, nullable=False)
    status = Column(status_enum, nullable=False, server_default="NAO_CONCILIADO")
    data_pagamento = Column(DateTime, nullable=False)
    hash_transacao = Column(String(255), nullable=True, unique=True, index=True) # 🔥 usado para evitar duplicação via CSV
    observacao = Column(String(255), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # relacionamento
    finalidade = relationship("Finalidade", foreign_keys=[finalidade_id], back_populates="lancamentos")
    sugestao_finalidade = relationship("Finalidade", foreign_keys=[sugestao_finalidade_id])

    __table_args__ = (
        Index("idx_lancamento_data", "data_pagamento"),
        Index("idx_lancamento_tipo", "tipo"),
        Index("idx_lancamento_status", "status"),
    )