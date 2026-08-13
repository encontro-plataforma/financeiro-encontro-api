from sqlalchemy.orm import Session, joinedload

from app.models.encontreiro import Encontreiro
from app.models.equipe import Equipe
from app.utils.sort_utils import apply_sort

SORT_FIELDS = {
    "nome": Encontreiro.nome,
    "apelido": Encontreiro.apelido,
    "dt_inscricao": Encontreiro.dt_inscricao,
    "dt_pagamento": Encontreiro.dt_pagamento,
}

DEFAULT_SORT = "id:asc"


def _apply_filters(query, params):
    if params.nome:
        query = query.filter(Encontreiro.nome.ilike(f"%{params.nome}%"))

    if params.apelido:
        query = query.filter(Encontreiro.apelido.ilike(f"%{params.apelido}%"))

    if getattr(params, "nome_ou_apelido", None):
        busca = f"%{params.nome_ou_apelido}%"
        query = query.filter(
            (Encontreiro.nome.ilike(busca)) | (Encontreiro.apelido.ilike(busca))
        )

    if getattr(params, "nome_pagador", None):
        query = query.filter(Encontreiro.nome_pagador.ilike(f"%{params.nome_pagador}%"))

    if params.equipe_nome or params.equipe_acesso:
        query = query.join(Equipe, Encontreiro.equipe_id == Equipe.id)

        if params.equipe_nome:
            query = query.filter(Equipe.nome.ilike(f"%{params.equipe_nome}%"))

        if params.equipe_acesso:
            query = query.filter(Equipe.acesso == params.equipe_acesso)

    if getattr(params, "equipe_ids", None):
        query = query.filter(Encontreiro.equipe_id.in_(params.equipe_ids))

    if getattr(params, "situacao_camisa", None):
        query = query.filter(Encontreiro.situacao_camisa.in_(params.situacao_camisa))

    if getattr(params, "auditado", None) is not None:
        query = query.filter(Encontreiro.auditado.is_(params.auditado))

    if params.dt_inscricao_inicio:
        query = query.filter(Encontreiro.dt_inscricao >= params.dt_inscricao_inicio)

    if params.dt_inscricao_fim:
        query = query.filter(Encontreiro.dt_inscricao <= params.dt_inscricao_fim)

    return query


class EncontreiroRepository:

    @staticmethod
    def get_by_id(db: Session, encontreiro_id: int):
        return (
            db.query(Encontreiro)
            .options(joinedload(Encontreiro.equipe))
            .filter(Encontreiro.id == encontreiro_id)
            .first()
        )

    @staticmethod
    def get_by_nome_telefone(db: Session, nome: str, telefone: str):
        return (
            db.query(Encontreiro)
            .filter(
                Encontreiro.nome.ilike(nome or ""),
                Encontreiro.telefone == telefone,
            )
            .first()
        )

    @staticmethod
    def list_all(db: Session, params):
        query = db.query(Encontreiro).options(joinedload(Encontreiro.equipe))
        query = _apply_filters(query, params)
        query = apply_sort(query, Encontreiro, params.sort, SORT_FIELDS, DEFAULT_SORT)
        return query.all()

    @staticmethod
    def list_with_count(db: Session, params):
        query = db.query(Encontreiro).options(joinedload(Encontreiro.equipe))
        query = _apply_filters(query, params)
        query = apply_sort(query, Encontreiro, params.sort, SORT_FIELDS, DEFAULT_SORT)
        total = query.count()
        items = query.offset(params.skip).limit(params.limit).all()
        return items, total

    @staticmethod
    def create(db: Session, data: dict):
        obj = Encontreiro(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: Encontreiro, data: dict):
        for key, value in data.items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: Encontreiro):
        db.delete(obj)
        db.commit()
