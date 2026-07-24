from sqlalchemy.orm import Session
from app.repositories.detalhamento_repository import DetalhamentoRepository
from app.core.exceptions import NotFoundException


class DetalhamentoService:

    @staticmethod
    def list_all(db: Session, params):
        return DetalhamentoRepository.list_all(db, params)

    @staticmethod
    def list(db: Session, params):
        items, total = DetalhamentoRepository.list_with_count(db, params)

        return {
            "items": items,
            "total": total,
            "skip": params.skip,
            "limit": params.limit
        }

    @staticmethod
    def get_by_id(db: Session, detalhamento_id: int):
        obj = DetalhamentoRepository.get_by_id(db, detalhamento_id)

        if not obj:
            raise NotFoundException("Detalhamento")

        return obj

    @staticmethod
    def create(db: Session, data: dict):
        return DetalhamentoRepository.create(db, data)

    @staticmethod
    def update(db: Session, detalhamento_id: int, data: dict):
        obj = DetalhamentoRepository.get_by_id(db, detalhamento_id)

        if not obj:
            raise NotFoundException("Detalhamento")

        return DetalhamentoRepository.update(db, obj, data)

    @staticmethod
    def delete(db: Session, detalhamento_id: int):
        obj = DetalhamentoRepository.get_by_id(db, detalhamento_id)

        if not obj:
            raise NotFoundException("Detalhamento")

        DetalhamentoRepository.delete(db, obj)
