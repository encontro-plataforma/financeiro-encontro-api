from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.utils.sort_utils import apply_sort
from sqlalchemy import or_

SORT_FIELDS = {
    "nome": Usuario.nome,
    "email": Usuario.email,
    "criado_em": Usuario.criado_em,
}

DEFAULT_SORT = "nome:asc"

def _apply_filters(query, params):
    # Filters
    if hasattr(params, 'nome') and params.nome:
        query = query.filter(Usuario.nome.ilike(f"%{params.nome}%"))
    if hasattr(params, 'email') and params.email:
        query = query.filter(Usuario.email.ilike(f"%{params.email}%"))
    if hasattr(params, 'nomeOrEmail') and params.nomeOrEmail:
        query = query.filter(
            or_(Usuario.nome.ilike(f"%{params.nomeOrEmail}%"), Usuario.email.ilike(f"%{params.nomeOrEmail}%"))
        )
    if hasattr(params, 'ativo') and params.ativo is not None:
        query = query.filter(Usuario.ativo == params.ativo)
    if hasattr(params, 'perfil') and params.perfil:
        query = query.filter(Usuario.perfil == params.perfil)
    return query

class UsuarioRepository:

    @staticmethod
    def get_by_id(db: Session, usuario_id: int):
        return db.query(Usuario).filter(Usuario.id == usuario_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str):
        return db.query(Usuario).filter(Usuario.email == email).first()

    @staticmethod
    def list_all(db: Session, params):
        query = db.query(Usuario)
        query = _apply_filters(query, params)
        query = apply_sort(query, Usuario, params.sort, SORT_FIELDS, DEFAULT_SORT)
        return query.offset(params.skip).limit(params.limit).all()

    @staticmethod
    def list_with_count(db: Session, params):
        query = db.query(Usuario)
        query = _apply_filters(query, params)
        query = apply_sort(query, Usuario, params.sort, SORT_FIELDS, DEFAULT_SORT)
        total = query.count()
        items = query.offset(params.skip).limit(params.limit).all()
        return items, total

    @staticmethod
    def create(db: Session, data: dict):
        obj = Usuario(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: Usuario, data: dict):
        for key, value in data.items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: Usuario):
        db.delete(obj)
        db.commit()
