from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.repositories.upload_file_repository import UploadFileRepository


class UploadFileService:
    @staticmethod
    def list_all(db: Session, params):
        return UploadFileRepository.list_all(db, params)

    @staticmethod
    def list(db: Session, params):
        items, total = UploadFileRepository.list_with_count(db, params)

        return {
            "items": items,
            "total": total,
            "skip": params.skip,
            "limit": params.limit,
        }

    @staticmethod
    def get_by_id(db: Session, upload_id: int):
        obj = UploadFileRepository.get_by_id(db, upload_id)

        if not obj:
            raise NotFoundException("Arquivo")

        return obj

    @staticmethod
    def get_status(db: Session, upload_id: int):
        """Consulta enxuta (não carrega conteudo_csv) usada no polling do upload."""
        obj = UploadFileRepository.get_status_by_id(db, upload_id)

        if not obj:
            raise NotFoundException("Arquivo")

        return obj

    @staticmethod
    def create(db: Session, data: dict):
        return UploadFileRepository.create(db, data)

    @staticmethod
    def update_status(
        db: Session,
        upload_id: int,
        status,
        error_code: str = None,
        error_message: str = None,
        resultado_processamento: str = None,
    ):
        obj = UploadFileRepository.get_by_id(db, upload_id)

        if not obj:
            raise NotFoundException("Arquivo")

        return UploadFileRepository.update(
            db,
            obj,
            {
                "status": status,
                "processado_em": datetime.utcnow(),
                "error_code": error_code,
                "error_message": error_message,
                "resultado_processamento": resultado_processamento,
            },
        )

    @staticmethod
    def delete(db: Session, upload_id: int):
        obj = UploadFileRepository.get_by_id(db, upload_id)

        if not obj:
            raise NotFoundException("Arquivo")

        UploadFileRepository.delete(db, obj)
