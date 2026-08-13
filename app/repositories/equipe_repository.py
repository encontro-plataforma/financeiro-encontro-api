from sqlalchemy.orm import Session

from app.models.equipe import Equipe
from app.utils.sort_utils import apply_sort

SORT_FIELDS = {
    "nome": Equipe.nome,
    "acesso": Equipe.acesso,
}

DEFAULT_SORT = "nome:asc"


def _apply_filters(query, params):
    if params.nome:
        query = query.filter(Equipe.nome.ilike(f"%{params.nome}%"))
    if params.acesso:
        query = query.filter(Equipe.acesso == params.acesso)
    return query


class EquipeRepository:

    @staticmethod
    def get_by_id(db: Session, equipe_id: int):
        return db.query(Equipe).filter(Equipe.id == equipe_id).first()

    @staticmethod
    def get_by_nome(db: Session, nome: str):
        return db.query(Equipe).filter(Equipe.nome.ilike(nome)).first()

    @staticmethod
    def list_all(db: Session, params):
        query = db.query(Equipe)
        query = _apply_filters(query, params)
        query = apply_sort(query, Equipe, params.sort, SORT_FIELDS, DEFAULT_SORT)
        return query.all()

    @staticmethod
    def list_with_count(db: Session, params):
        query = db.query(Equipe)
        query = _apply_filters(query, params)
        query = apply_sort(query, Equipe, params.sort, SORT_FIELDS, DEFAULT_SORT)
        total = query.count()
        items = query.offset(params.skip).limit(params.limit).all()
        return items, total

    @staticmethod
    def create(db: Session, data: dict):
        obj = Equipe(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: Equipe, data: dict):
        for key, value in data.items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: Equipe):
        db.delete(obj)
        db.commit()
