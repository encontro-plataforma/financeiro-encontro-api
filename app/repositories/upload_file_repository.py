from sqlalchemy.orm import Session
from app.models.upload_file import UploadFile
from app.utils.sort_utils import apply_sort


SORT_FIELDS = {
    "nome_arquivo": UploadFile.nome_arquivo,
    "tamanho_bytes": UploadFile.tamanho_bytes,
    "processado_em": UploadFile.processado_em,
}

DEFAULT_SORT = "processado_em:desc"


class UploadFileRepository:

    @staticmethod
    def get_by_id(db: Session, upload_id: int):
        return (
            db.query(UploadFile)
            .filter(UploadFile.id == upload_id)
            .first()
        )

    @staticmethod
    def get_status_by_id(db: Session, upload_id: int):
        return (
            db.query(UploadFile.id, UploadFile.status)
            .filter(UploadFile.id == upload_id)
            .first()
        )

    @staticmethod
    def _apply_filters(query, params):
        if params.nome_arquivo:
            query = query.filter(
                UploadFile.nome_arquivo.ilike(f"%{params.nome_arquivo}%")
            )

        # 🔥 RANGE FILTER (profissional)
        if params.processado_em_inicio:
            query = query.filter(
                UploadFile.processado_em >= params.processado_em_inicio
            )

        if params.processado_em_fim:
            query = query.filter(
                UploadFile.processado_em <= params.processado_em_fim
            )

        return query

    @staticmethod
    def list_all(db: Session, params):
        query = db.query(UploadFile)

        query = UploadFileRepository._apply_filters(query, params)

        query = apply_sort(
            query,
            UploadFile,
            params.sort,
            SORT_FIELDS,
            DEFAULT_SORT
        )

        return query.offset(params.skip).limit(params.limit).all()

    @staticmethod
    def list_with_count(db: Session, params):
        query = db.query(UploadFile)

        query = UploadFileRepository._apply_filters(query, params)

        query = apply_sort(
            query,
            UploadFile,
            params.sort,
            SORT_FIELDS,
            DEFAULT_SORT
        )

        total = query.count()
        items = query.offset(params.skip).limit(params.limit).all()

        return items, total

    @staticmethod
    def create(db: Session, data: dict):
        obj = UploadFile(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, obj: UploadFile, data: dict):
        for key, value in data.items():
            setattr(obj, key, value)

        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: UploadFile):
        db.delete(obj)
        db.commit()
