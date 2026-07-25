from sqlalchemy import Column, Integer, String

from app.database.base import Base


class Circulo(Base):
    __tablename__ = "circulos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, index=True)
    rgb = Column(String(50), nullable=False)
