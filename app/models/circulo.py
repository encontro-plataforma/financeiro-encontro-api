from sqlalchemy import Boolean, Column, Integer, String

from app.database.base import Base


class Circulo(Base):
    __tablename__ = "circulos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, index=True)
    rgb = Column(String(50), nullable=False)
    # Marca o(s) círculo(s) que representam cancelamento (ex.: "CANCELADO") --
    # usado por Encontrista.auditado (ver app/models/detalhamento.py) para
    # considerar a ficha já auditada independente de ter Detalhamento
    # vinculado, mesmo padrão de Equipe.acesso == N/A para Encontreiro.
    cancelado = Column(Boolean, nullable=False, server_default="false")
