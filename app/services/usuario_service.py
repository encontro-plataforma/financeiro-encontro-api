from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException
from app.core.security import hash_password
from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario_schema import UsuarioCreate, UsuarioUpdate

_ADMIN_ID = 1


class UsuarioService:

    @staticmethod
    def list(db: Session, params):
        items, total = UsuarioRepository.list_with_count(db, params)
        return {"items": items, "total": total, "skip": params.skip, "limit": params.limit}

    @staticmethod
    def get_by_id(db: Session, usuario_id: int) -> Usuario:
        obj = UsuarioRepository.get_by_id(db, usuario_id)
        if not obj:
            raise NotFoundException("Usuário")
        return obj

    @staticmethod
    def create(db: Session, data: UsuarioCreate) -> Usuario:
        if UsuarioRepository.get_by_email(db, data.email):
            raise BadRequestException("Já existe um usuário com este e-mail")
        return UsuarioRepository.create(db, {
            "nome":       data.nome,
            "email":      data.email,
            "senha_hash": hash_password(data.senha),
            "ativo":      data.ativo,
            "perfil":     data.perfil,
        })

    @staticmethod
    def update(db: Session, usuario_id: int, data: UsuarioUpdate) -> Usuario:
        if usuario_id == _ADMIN_ID:
            raise BadRequestException("Não é possível atualizar o administrador geral")

        obj = UsuarioService.get_by_id(db, usuario_id)

        existing = UsuarioRepository.get_by_email(db, data.email)
        if existing and existing.id != usuario_id:
            raise BadRequestException("Já existe um usuário com este e-mail")

        update_data: dict = {"nome": data.nome, "email": data.email, "ativo": data.ativo, "perfil": data.perfil}
        if data.senha:
            update_data["senha_hash"] = hash_password(data.senha)

        return UsuarioRepository.update(db, obj, update_data)

    @staticmethod
    def delete(db: Session, usuario_id: int, current_user: Usuario) -> None:
        if usuario_id == _ADMIN_ID:
            raise BadRequestException("Não é possível excluir o administrador geral")
        if usuario_id == current_user.id:
            raise BadRequestException("Não é possível excluir seu próprio usuário")

        obj = UsuarioService.get_by_id(db, usuario_id)
        UsuarioRepository.delete(db, obj)
