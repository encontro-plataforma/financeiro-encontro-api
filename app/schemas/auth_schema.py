from datetime import datetime

from pydantic import BaseModel

from app.models.enums import PerfilUsuario

class LoginRequest(BaseModel):
    email: str
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: str
    perfil: PerfilUsuario
    ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True
