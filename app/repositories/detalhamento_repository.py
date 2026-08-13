from sqlalchemy.orm import Session

from app.models.detalhamento import Detalhamento
from app.utils.sort_utils import apply_sort

SORT_FIELDS = {
    "criado_em": Detalhamento.criado_em,
    "valor": Detalhamento.valor,
}

DEFAULT_SORT = "criado_em:desc"


def _apply_filters(query, params):
    if params.lancamento_id is not None:
        query = query.filter(Detalhamento.lancamento_id == params.lancamento_id)

    if params.tipo:
        query = query.filter(Detalhamento.tipo == params.tipo)

    if params.referencia_id is not None:
        query = query.filter(Detalhamento.referencia_id == params.referencia_id)

    return query


class DetalhamentoRepository:

    @staticmethod
    def get_by_id(db: Session, detalhamento_id: int):
        return db.query(Detalhamento).filter(Detalhamento.id == detalhamento_id).first()

    @staticmethod
    def list_all(db: Session, params):
        query = db.query(Detalhamento)
        query = _apply_filters(query, params)
        query = apply_sort(query, Detalhamento, params.sort, SORT_FIELDS, DEFAULT_SORT)
        return query.all()

    @staticmethod
    def list_with_count(db: Session, params):
        query = db.query(Detalhamento)
        query = _apply_filters(query, params)
        query = apply_sort(query, Detalhamento, params.sort, SORT_FIELDS, DEFAULT_SORT)
        total = query.count()
        items = query.offset(params.skip).limit(params.limit).all()
        return items, total

    @staticmethod
    def create(db: Session, data: dict):
        obj = Detalhamento(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: Detalhamento, data: dict):
        for key, value in data.items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: Detalhamento):
        db.delete(obj)
        db.commit()
