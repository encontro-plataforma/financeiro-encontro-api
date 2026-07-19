from sqlalchemy.orm import Session

from app.models.finalidade import Finalidade
from app.utils.sort_utils import apply_sort

SORT_FIELDS = {
    "nome": Finalidade.nome,
    "tipo": Finalidade.tipo,
}

DEFAULT_SORT = "nome:asc"


def _apply_filters(query, params):
    if params.nome:
        query = query.filter(Finalidade.nome.ilike(f"%{params.nome}%"))
    if params.tipo:
        query = query.filter(Finalidade.tipo == params.tipo)
    return query


class FinalidadeRepository:

    @staticmethod
    def get_by_id(db: Session, finalidade_id: int):
        return db.query(Finalidade).filter(Finalidade.id == finalidade_id).first()

    @staticmethod
    def list_all(db: Session, params):
        query = db.query(Finalidade)
        query = _apply_filters(query, params)
        query = apply_sort(query, Finalidade, params.sort, SORT_FIELDS, DEFAULT_SORT)
        return query.offset(params.skip).limit(params.limit).all()

    @staticmethod
    def list_with_count(db: Session, params):
        query = db.query(Finalidade)
        query = _apply_filters(query, params)
        query = apply_sort(query, Finalidade, params.sort, SORT_FIELDS, DEFAULT_SORT)
        total = query.count()
        items = query.offset(params.skip).limit(params.limit).all()
        return items, total

    @staticmethod
    def create(db: Session, data: dict):
        obj = Finalidade(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: Finalidade, data: dict):
        for key, value in data.items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: Finalidade):
        db.delete(obj)
        db.commit()
