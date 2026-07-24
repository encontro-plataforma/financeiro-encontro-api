from sqlalchemy.orm import Session
from app.repositories.equipe_repository import EquipeRepository
from app.core.exceptions import NotFoundException


class EquipeService:

    @staticmethod
    def list_all(db: Session, params):
        return EquipeRepository.list_all(db, params)

    @staticmethod
    def list(db: Session, params):
        items, total = EquipeRepository.list_with_count(db, params)

        return {
            "items": items,
            "total": total,
            "skip": params.skip,
            "limit": params.limit
        }

    @staticmethod
    def get_by_id(db: Session, equipe_id: int):
        obj = EquipeRepository.get_by_id(db, equipe_id)

        if not obj:
            raise NotFoundException("Equipe")

        return obj

    @staticmethod
    def create(db: Session, data: dict):
        return EquipeRepository.create(db, data)

    @staticmethod
    def update(db: Session, equipe_id: int, data: dict):
        obj = EquipeRepository.get_by_id(db, equipe_id)

        if not obj:
            raise NotFoundException("Equipe")

        return EquipeRepository.update(db, obj, data)

    @staticmethod
    def delete(db: Session, equipe_id: int):
        obj = EquipeRepository.get_by_id(db, equipe_id)

        if not obj:
            raise NotFoundException("Equipe")

        EquipeRepository.delete(db, obj)
