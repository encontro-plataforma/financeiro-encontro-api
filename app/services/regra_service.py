from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.repositories.regra_repository import RegraRepository


class RegraService:

    @staticmethod
    def list_all(db: Session, params):
        return RegraRepository.list_all(db, params)

    @staticmethod
    def list(db: Session, params):
        items, total = RegraRepository.list_with_count(db, params)

        return {
            "items": items,
            "total": total,
            "skip": params.skip,
            "limit": params.limit,
        }

    @staticmethod
    def get_by_id(db: Session, grupo_id: int):
        obj = RegraRepository.get_by_id(db, grupo_id)

        if not obj:
            raise NotFoundException("Grupo de Regras")

        return obj

    @staticmethod
    def create(db: Session, data: dict):
        return RegraRepository.create(db, data)

    @staticmethod
    def update(db: Session, grupo_id: int, data: dict):
        obj = RegraRepository.get_by_id(db, grupo_id)

        if not obj:
            raise NotFoundException("Grupo de Regras")

        return RegraRepository.update(db, obj, data)

    @staticmethod
    def delete(db: Session, grupo_id: int):
        obj = RegraRepository.get_by_id(db, grupo_id)

        if not obj:
            raise NotFoundException("Grupo de Regras")

        RegraRepository.delete(db, obj)
