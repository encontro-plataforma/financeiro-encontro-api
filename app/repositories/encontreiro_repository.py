from sqlalchemy.orm import Session

from app.models.encontreiro import Encontreiro
from app.models.equipe import Equipe
from app.utils.sort_utils import apply_sort

SORT_FIELDS = {
    "nome": Encontreiro.nome,
    "apelido": Encontreiro.apelido,
    "dt_inscricao": Encontreiro.dt_inscricao,
}

DEFAULT_SORT = "id:asc"


def _apply_filters(query, params):
    if params.nome:
        query = query.filter(Encontreiro.nome.ilike(f"%{params.nome}%"))

    if params.apelido:
        query = query.filter(Encontreiro.apelido.ilike(f"%{params.apelido}%"))

    if params.equipe_nome or params.equipe_acesso:
        query = query.join(Equipe, Encontreiro.equipe_id == Equipe.id)

        if params.equipe_nome:
            query = query.filter(Equipe.nome.ilike(f"%{params.equipe_nome}%"))

        if params.equipe_acesso:
            query = query.filter(Equipe.acesso == params.equipe_acesso)

    if params.dt_inscricao_inicio:
        query = query.filter(Encontreiro.dt_inscricao >= params.dt_inscricao_inicio)

    if params.dt_inscricao_fim:
        query = query.filter(Encontreiro.dt_inscricao <= params.dt_inscricao_fim)

    return query


class EncontreiroRepository:

    @staticmethod
    def get_by_id(db: Session, encontreiro_id: int):
        return db.query(Encontreiro).filter(Encontreiro.id == encontreiro_id).first()

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
        query = db.query(Encontreiro)
        query = _apply_filters(query, params)
        query = apply_sort(query, Encontreiro, params.sort, SORT_FIELDS, DEFAULT_SORT)
        return query.offset(params.skip).limit(params.limit).all()

    @staticmethod
    def list_with_count(db: Session, params):
        query = db.query(Encontreiro)
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
