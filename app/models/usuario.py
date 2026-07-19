from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.sql import func

from app.database.base import Base
from app.models.enums import PerfilUsuario

perfil_enum = ENUM(PerfilUsuario, name="perfil_usuario", create_type=True)


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    senha_hash = Column(String(255), nullable=False)
    ativo = Column(Boolean, default=True)
    perfil = Column(perfil_enum, nullable=False, server_default=PerfilUsuario.CONCILIADOR)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())
