from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.enums import PerfilUsuario


class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: str
    ativo: bool
    perfil: PerfilUsuario
    criado_em: datetime

    class Config:
        from_attributes = True


class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    ativo: bool = True
    perfil: PerfilUsuario = PerfilUsuario.CONCILIADOR


class UsuarioUpdate(BaseModel):
    nome: str
    email: EmailStr
    senha: Optional[str] = None
    ativo: bool
    perfil: PerfilUsuario
