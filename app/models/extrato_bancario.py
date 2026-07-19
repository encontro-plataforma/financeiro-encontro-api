from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM
from app.models.enums import StatusProcessamento

from app.database.base import Base

status_enum = ENUM(
    StatusProcessamento,
    name="status_processamento",
    create_type=True
)

class ExtratoBancario(Base):
    __tablename__ = "extratos_bancarios"

    id = Column(Integer, primary_key=True)
    nome_arquivo = Column(String(255), nullable=False)
    conteudo_csv = Column(String, nullable=True)
    tamanho_bytes = Column(Integer, nullable=True)
    processado_em = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(status_enum, nullable=False, server_default="PROCESSANDO")
    