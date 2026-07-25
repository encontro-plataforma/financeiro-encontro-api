from sqlalchemy.orm import Session

from app.models.circulo import Circulo
from app.utils.sort_utils import apply_sort

SORT_FIELDS = {
    "nome": Circulo.nome,
}

DEFAULT_SORT = "nome:asc"


def _apply_filters(query, params):
    if params.nome:
        query = query.filter(Circulo.nome.ilike(f"%{params.nome}%"))
    return query


class CirculoRepository:

    @staticmethod
    def get_by_id(db: Session, circulo_id: int):
        return db.query(Circulo).filter(Circulo.id == circulo_id).first()

    @staticmethod
    def get_by_nome(db: Session, nome: str):
        return db.query(Circulo).filter(Circulo.nome.ilike(nome)).first()

    @staticmethod
    def list_all(db: Session, params):
        query = db.query(Circulo)
        query = _apply_filters(query, params)
        query = apply_sort(query, Circulo, params.sort, SORT_FIELDS, DEFAULT_SORT)
        return query.offset(params.skip).limit(params.limit).all()

    @staticmethod
    def list_with_count(db: Session, params):
        query = db.query(Circulo)
        query = _apply_filters(query, params)
        query = apply_sort(query, Circulo, params.sort, SORT_FIELDS, DEFAULT_SORT)
        total = query.count()
        items = query.offset(params.skip).limit(params.limit).all()
        return items, total

    @staticmethod
    def create(db: Session, data: dict):
        obj = Circulo(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: Circulo, data: dict):
        for key, value in data.items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: Circulo):
        db.delete(obj)
        db.commit()
