from sqlalchemy.orm import Session
from app.models.lancamento import Lancamento

from app.utils.sort_utils import apply_sort

SORT_FIELDS = {
    "valor": Lancamento.valor,
    "data_pagamento": Lancamento.data_pagamento,
    "criado_em": Lancamento.criado_em,
}

DEFAULT_SORT = "data_pagamento:desc"

def _apply_filters(query, params):
    if params.data_inicio:
        query = query.filter(Lancamento.data_pagamento >= params.data_inicio)

    if params.data_fim:
        query = query.filter(Lancamento.data_pagamento <= params.data_fim)

    if params.status:
        query = query.filter(Lancamento.status == params.status)

    if params.tipo:
        query = query.filter(Lancamento.tipo == params.tipo)

    if getattr(params, 'finalidade_ids', None):
        query = query.filter(Lancamento.finalidade_id.in_(params.finalidade_ids))
    elif params.finalidade_id is not None:
        query = query.filter(Lancamento.finalidade_id == params.finalidade_id)

    if getattr(params, 'forma_pagamento', None):
        query = query.filter(Lancamento.forma_pagamento.in_(params.forma_pagamento))

    if params.descricao:
        query = query.filter(Lancamento.descricao.ilike(f"%{params.descricao}%"))

    # Excluir IDs já carregados (lazy load optimization)
    if params.exclude_ids:
        query = query.filter(~Lancamento.id.in_(params.exclude_ids))

    if params.limit > 1000 or params.limit <= 0:
        params.limit = 1000
        
    return query

class LancamentoRepository:

    @staticmethod
    def create(db: Session, data: dict) -> Lancamento:
        obj = Lancamento(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

   
    @staticmethod
    def delete(db: Session, obj: Lancamento):
        db.delete(obj)
        db.commit()

    @staticmethod
    def update(db: Session, obj: Lancamento, data: dict):
        for key, value in data.items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_by_id(db: Session, lancamento_id: int):
        return db.query(Lancamento).filter(Lancamento.id == lancamento_id).first()

    @staticmethod
    def list_all(db: Session, params):
        query = db.query(Lancamento)

        query = _apply_filters(query, params)

        query = apply_sort(query, Lancamento, params.sort, SORT_FIELDS, DEFAULT_SORT)

        return query.offset(params.skip).limit(params.limit).all()

    @staticmethod
    def list_with_count(db: Session, params):
        query = db.query(Lancamento)

        query = _apply_filters(query, params)

        query = apply_sort(query, Lancamento, params.sort, SORT_FIELDS, DEFAULT_SORT)

        total = query.count()
        items = query.offset(params.skip).limit(params.limit).all()
        return items, total
