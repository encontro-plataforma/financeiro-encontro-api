from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedException
from app.core.security import create_access_token, verify_password
from app.repositories.usuario_repository import UsuarioRepository


class AuthService:

    @staticmethod
    def login(db: Session, email: str, senha: str) -> dict:
        usuario = UsuarioRepository.get_by_email(db, email)
        if not usuario or not verify_password(senha, usuario.senha_hash):
            raise UnauthorizedException("Email ou senha inválidos")

        token = create_access_token({"sub": str(usuario.id)})
        return {"access_token": token, "token_type": "bearer"}

    @staticmethod
    def get_by_id(db: Session, usuario_id: int):
        usuario = UsuarioRepository.get_by_id(db, usuario_id)
        if not usuario or not usuario.ativo:
            raise UnauthorizedException("Usuário não encontrado ou inativo")
        return usuario
