from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.equipe_filter_dto import EquipeFilterDto
from app.schemas.equipe_schema import (
    EquipeCreate,
    EquipeResponse,
    EquipeUpdate,
)
from app.schemas.pagination_schema import Page
from app.services.equipe_service import EquipeService

router = APIRouter(prefix="/equipes", tags=["Secretaria - Equipes"])


@router.get("/", response_model=Page[EquipeResponse])
def list_equipes(
    params: EquipeFilterDto = Depends(),
    db: Session = Depends(get_db),
):
    return EquipeService.list(db, params)


@router.get("/all", response_model=List[EquipeResponse])
def list_all(
    params: EquipeFilterDto = Depends(),
    db: Session = Depends(get_db),
):
    return EquipeService.list_all(db, params)


@router.get("/{equipe_id}", response_model=EquipeResponse)
def get_by_id(equipe_id: int, db: Session = Depends(get_db)):
    return EquipeService.get_by_id(db, equipe_id)


@router.post("/", response_model=EquipeResponse, status_code=201)
def create(data: EquipeCreate, db: Session = Depends(get_db)):
    return EquipeService.create(db, data.model_dump())


@router.put("/{equipe_id}", response_model=EquipeResponse)
def update(
    equipe_id: int,
    data: EquipeUpdate,
    db: Session = Depends(get_db),
):
    return EquipeService.update(db, equipe_id, data.model_dump(exclude_none=True))


@router.delete("/{equipe_id}")
def delete(equipe_id: int, db: Session = Depends(get_db)):
    EquipeService.delete(db, equipe_id)
    return {"message": "Equipe removida com sucesso"}
