from sqlalchemy.orm import Session
from app.repositories.circulo_repository import CirculoRepository
from app.core.exceptions import NotFoundException


class CirculoService:

    @staticmethod
    def list_all(db: Session, params):
        return CirculoRepository.list_all(db, params)

    @staticmethod
    def list(db: Session, params):
        items, total = CirculoRepository.list_with_count(db, params)

        return {
            "items": items,
            "total": total,
            "skip": params.skip,
            "limit": params.limit
        }

    @staticmethod
    def get_by_id(db: Session, circulo_id: int):
        obj = CirculoRepository.get_by_id(db, circulo_id)

        if not obj:
            raise NotFoundException("Circulo")

        return obj

    @staticmethod
    def create(db: Session, data: dict):
        return CirculoRepository.create(db, data)

    @staticmethod
    def update(db: Session, circulo_id: int, data: dict):
        obj = CirculoRepository.get_by_id(db, circulo_id)

        if not obj:
            raise NotFoundException("Circulo")

        return CirculoRepository.update(db, obj, data)

    @staticmethod
    def delete(db: Session, circulo_id: int):
        obj = CirculoRepository.get_by_id(db, circulo_id)

        if not obj:
            raise NotFoundException("Circulo")

        CirculoRepository.delete(db, obj)
