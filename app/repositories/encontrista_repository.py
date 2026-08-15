from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.encontreiro import Encontreiro
from app.models.encontrista import Encontrista
from app.models.circulo import Circulo
from app.utils.sort_utils import apply_sort

SORT_FIELDS = {
    "id": Encontrista.id,
    "nome": Encontrista.nome,
    "apelido": Encontrista.apelido,
    "dt_entrega": Encontrista.dt_entrega,
    "dt_nascimento": Encontrista.dt_nascimento,
    "dt_pagamento": Encontrista.dt_pagamento,
    "idade": Encontrista.idade,
    "circulo": Circulo.nome,
}

DEFAULT_SORT = "id:asc"


def _apply_filters(query, params):
    if params.nome:
        query = query.filter(Encontrista.nome.ilike(f"%{params.nome}%"))

    if params.apelido:
        query = query.filter(Encontrista.apelido.ilike(f"%{params.apelido}%"))

    if getattr(params, "nome_ou_apelido", None):
        busca = f"%{params.nome_ou_apelido}%"
        query = query.filter(
            (Encontrista.nome.ilike(busca)) | (Encontrista.apelido.ilike(busca))
        )

    if getattr(params, "nome_pagador", None):
        query = query.filter(Encontrista.nome_pagador.ilike(f"%{params.nome_pagador}%"))

    if params.circulo_nome:
        query = query.join(Circulo, Encontrista.circulo_id == Circulo.id)
        query = query.filter(Circulo.nome.ilike(f"%{params.circulo_nome}%"))

    if getattr(params, "circulo_ids", None):
        ids_reais = [i for i in params.circulo_ids if i]
        inclui_sem_circulo = 0 in params.circulo_ids

        condicoes = []
        if ids_reais:
            condicoes.append(Encontrista.circulo_id.in_(ids_reais))
        if inclui_sem_circulo:
            condicoes.append(Encontrista.circulo_id.is_(None))

        if condicoes:
            query = query.filter(or_(*condicoes))

    if getattr(params, "padrinho_id", None):
        query = query.filter(Encontrista.padrinho_id == params.padrinho_id)

    if getattr(params, "auditado", None) is not None:
        query = query.filter(Encontrista.auditado.is_(params.auditado))

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


def _join_para_sort(query, sort: str):
    """`apply_sort` só referencia colunas -- se a ordenação pedir um campo
    de outra tabela (ex.: "circulo", que ordena por Circulo.nome), o JOIN
    precisa existir explicitamente na query (o `joinedload` do circulo é só
    pra popular o relacionamento, não fica disponível pro ORDER BY de fora,
    principalmente no `query.count()` do list_with_count)."""
    if sort and "circulo:" in sort:
        query = query.outerjoin(Circulo, Encontrista.circulo_id == Circulo.id)
    return query


class EncontristaRepository:

    @staticmethod
    def get_by_id(db: Session, encontrista_id: int):
        return (
            db.query(Encontrista)
            .options(
                joinedload(Encontrista.circulo),
                joinedload(Encontrista.padrinho).joinedload(Encontreiro.equipe),
            )
            .filter(Encontrista.id == encontrista_id)
            .first()
        )

    @staticmethod
    def list_all(db: Session, params):
        query = db.query(Encontrista).options(
            joinedload(Encontrista.circulo),
            joinedload(Encontrista.padrinho).joinedload(Encontreiro.equipe),
        )
        query = _apply_filters(query, params)
        query = _join_para_sort(query, params.sort)
        query = apply_sort(query, Encontrista, params.sort, SORT_FIELDS, DEFAULT_SORT)
        return query.all()

    @staticmethod
    def list_with_count(db: Session, params):
        query = db.query(Encontrista).options(
            joinedload(Encontrista.circulo),
            joinedload(Encontrista.padrinho).joinedload(Encontreiro.equipe),
        )
        query = _apply_filters(query, params)
        query = _join_para_sort(query, params.sort)
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

    @staticmethod
    def get_padrinhos_disponiveis(db: Session):
        return (
            db.query(Encontreiro)
            .options(joinedload(Encontreiro.equipe))
            .join(Encontrista, Encontrista.padrinho_id == Encontreiro.id)
            .distinct()
            .order_by(Encontreiro.nome)
            .all()
        )
