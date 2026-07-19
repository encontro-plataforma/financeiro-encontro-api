from sqlalchemy.orm import Session
from app.repositories.finalidade_repository import FinalidadeRepository
from app.core.exceptions import NotFoundException


class FinalidadeService:

    @staticmethod
    def list_all(db: Session, params):
        return FinalidadeRepository.list_all(db, params)
    
    @staticmethod
    def list(db: Session, params):
        items, total = FinalidadeRepository.list_with_count(db, params)

        return {
            "items": items,
            "total": total,
            "skip": params.skip,
            "limit": params.limit
        }

    @staticmethod
    def get_by_id(db: Session, finalidade_id: int):
        obj = FinalidadeRepository.get_by_id(db, finalidade_id)

        if not obj:
            raise NotFoundException("Finalidade")

        return obj

    # 🔒 Métodos internos (não expostos)
    @staticmethod
    def create(db: Session, data: dict):
        return FinalidadeRepository.create(db, data)

    @staticmethod
    def update(db: Session, finalidade_id: int, data: dict):
        obj = FinalidadeRepository.get_by_id(db, finalidade_id)

        if not obj:
            raise NotFoundException("Finalidade")

        return FinalidadeRepository.update(db, obj, data)

    @staticmethod
    def delete(db: Session, finalidade_id: int):
        obj = FinalidadeRepository.get_by_id(db, finalidade_id)

        if not obj:
            raise NotFoundException("Finalidade")

        FinalidadeRepository.delete(db, obj)