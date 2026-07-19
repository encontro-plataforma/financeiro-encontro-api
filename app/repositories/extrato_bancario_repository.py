from sqlalchemy.orm import Session
from app.models.extrato_bancario import ExtratoBancario
from app.utils.sort_utils import apply_sort


SORT_FIELDS = {
    "nome_arquivo": ExtratoBancario.nome_arquivo,
    "tamanho_bytes": ExtratoBancario.tamanho_bytes,
    "processado_em": ExtratoBancario.processado_em,
}

DEFAULT_SORT = "processado_em:desc"


class ExtratoBancarioRepository:

    @staticmethod
    def get_by_id(db: Session, extrato_id: int):
        return (
            db.query(ExtratoBancario)
            .filter(ExtratoBancario.id == extrato_id)
            .first()
        )

    @staticmethod
    def _apply_filters(query, params):
        if params.nome_arquivo:
            query = query.filter(
                ExtratoBancario.nome_arquivo.ilike(f"%{params.nome_arquivo}%")
            )

        # 🔥 RANGE FILTER (profissional)
        if params.processado_em_inicio:
            query = query.filter(
                ExtratoBancario.processado_em >= params.processado_em_inicio
            )

        if params.processado_em_fim:
            query = query.filter(
                ExtratoBancario.processado_em <= params.processado_em_fim
            )

        return query

    @staticmethod
    def list_all(db: Session, params):
        query = db.query(ExtratoBancario)

        query = ExtratoBancarioRepository._apply_filters(query, params)

        query = apply_sort(
            query,
            ExtratoBancario,
            params.sort,
            SORT_FIELDS,
            DEFAULT_SORT
        )

        return query.offset(params.skip).limit(params.limit).all()

    @staticmethod
    def list_with_count(db: Session, params):
        query = db.query(ExtratoBancario)

        query = ExtratoBancarioRepository._apply_filters(query, params)

        query = apply_sort(
            query,
            ExtratoBancario,
            params.sort,
            SORT_FIELDS,
            DEFAULT_SORT
        )

        total = query.count()
        items = query.offset(params.skip).limit(params.limit).all()

        return items, total

    @staticmethod
    def create(db: Session, data: dict):
        obj = ExtratoBancario(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: ExtratoBancario, data: dict):
        for key, value in data.items():
            setattr(obj, key, value)

        db.commit()
        db.refresh(obj)
        return obj
       
    @staticmethod
    def delete(db: Session, obj: ExtratoBancario):
        db.delete(obj)
        db.commit()