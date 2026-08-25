from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import ENUM

from app.database.base import Base
from app.models.enums import AcessoEquipe

acesso_equipe_enum = ENUM(
    AcessoEquipe,
    name="acesso_equipe",
    create_type=True,
    values_callable=lambda enum_cls: [e.value for e in enum_cls],
)


class Equipe(Base):
    __tablename__ = "equipes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, index=True)
    acesso = Column(acesso_equipe_enum, nullable=False)
