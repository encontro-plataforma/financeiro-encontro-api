from sqlalchemy.orm import Session
from app.repositories.extrato_bancario_repository import ExtratoBancarioRepository
from app.core.exceptions import NotFoundException
from datetime import datetime


class ExtratoBancarioService:

    @staticmethod
    def list_all(db: Session, params):
        return ExtratoBancarioRepository.list_all(db, params)

    @staticmethod
    def list(db: Session, params):
        items, total = ExtratoBancarioRepository.list_with_count(db, params)

        return {
            "items": items,
            "total": total,
            "skip": params.skip,
            "limit": params.limit
        }

    @staticmethod
    def get_by_id(db: Session, extrato_id: int):
        obj = ExtratoBancarioRepository.get_by_id(db, extrato_id)

        if not obj:
            raise NotFoundException("Extrato bancário")

        return obj

    @staticmethod
    def create(db: Session, data: dict):
        return ExtratoBancarioRepository.create(db, data)

    @staticmethod
    def update_status(db: Session, extrato_id: int, status):
        obj = ExtratoBancarioRepository.get_by_id(db, extrato_id)

        if not obj:
            raise NotFoundException("Extrato bancário")

        return ExtratoBancarioRepository.update(
            db,
            obj,
            {
                "status": status, 
                "processado_em": datetime.utcnow()
            }
        )
        
    @staticmethod
    def delete(db: Session, extrato_id: int):
        obj = ExtratoBancarioRepository.get_by_id(db, extrato_id)

        if not obj:
            raise NotFoundException("Extrato bancário")

        ExtratoBancarioRepository.delete(db, obj)