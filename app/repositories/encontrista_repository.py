from sqlalchemy.orm import Session

from app.models.encontrista import Encontrista
from app.models.circulo import Circulo
from app.utils.sort_utils import apply_sort

SORT_FIELDS = {
    "nome": Encontrista.nome,
    "apelido": Encontrista.apelido,
    "dt_entrega": Encontrista.dt_entrega,
    "dt_nascimento": Encontrista.dt_nascimento,
}

DEFAULT_SORT = "nome:asc"


def _apply_filters(query, params):
    if params.nome:
        query = query.filter(Encontrista.nome.ilike(f"%{params.nome}%"))

    if params.apelido:
        query = query.filter(Encontrista.apelido.ilike(f"%{params.apelido}%"))

    if params.circulo_nome:
        query = query.join(Circulo, Encontrista.circulo_id == Circulo.id)
        query = query.filter(Circulo.nome.ilike(f"%{params.circulo_nome}%"))

    if params.camisa:
        query = query.filter(Encontrista.camisa.ilike(f"%{params.camisa}%"))

    if params.blusa is not None:
        query = query.filter(Encontrista.blusa == params.blusa)

    if params.carta is not None:
        query = query.filter(Encontrista.carta == params.carta)

    if params.album is not None:
        query = query.filter(Encontrista.album == params.album)

    if params.dt_entrega_inicio:
        query = query.filter(Encontrista.dt_entrega >= params.dt_entrega_inicio)

    if params.dt_entrega_fim:
        query = query.filter(Encontrista.dt_entrega <= params.dt_entrega_fim)

    if params.dt_nascimento_inicio:
        query = query.filter(Encontrista.dt_nascimento >= params.dt_nascimento_inicio)

    if params.dt_nascimento_fim:
        query = query.filter(Encontrista.dt_nascimento <= params.dt_nascimento_fim)

    return query


class EncontristaRepository:

    @staticmethod
    def get_by_id(db: Session, encontrista_id: int):
        return db.query(Encontrista).filter(Encontrista.id == encontrista_id).first()

    @staticmethod
    def list_all(db: Session, params):
        query = db.query(Encontrista)
        query = _apply_filters(query, params)
        query = apply_sort(query, Encontrista, params.sort, SORT_FIELDS, DEFAULT_SORT)
        return query.offset(params.skip).limit(params.limit).all()

    @staticmethod
    def list_with_count(db: Session, params):
        query = db.query(Encontrista)
        query = _apply_filters(query, params)
        query = apply_sort(query, Encontrista, params.sort, SORT_FIELDS, DEFAULT_SORT)
        total = query.count()
        items = query.offset(params.skip).limit(params.limit).all()
        return items, total

    @staticmethod
    def create(db: Session, data: dict):
        obj = Encontrista(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: Encontrista, data: dict):
        for key, value in data.items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: Encontrista):
        db.delete(obj)
        db.commit()
