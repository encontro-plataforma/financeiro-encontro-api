from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.finalidade_filter_dto import FinalidadeFilterDto
from app.schemas.finalidade_schema import (
    FinalidadeCreate,
    FinalidadeResponse,
    FinalidadeUpdate,
)
from app.schemas.pagination_schema import Page
from app.services.finalidade_service import FinalidadeService

router = APIRouter(prefix="/finalidades", tags=["Finalidades"])


@router.get("/", response_model=Page[FinalidadeResponse])
def list_finalidades(
    params: FinalidadeFilterDto = Depends(),
    db: Session = Depends(get_db),
):
    return FinalidadeService.list(db, params)


@router.get("/all", response_model=List[FinalidadeResponse])
def list_all(
    params: FinalidadeFilterDto = Depends(),
    db: Session = Depends(get_db),
):
    return FinalidadeService.list_all(db, params)


@router.get("/{finalidade_id}", response_model=FinalidadeResponse)
def get_by_id(finalidade_id: int, db: Session = Depends(get_db)):
    return FinalidadeService.get_by_id(db, finalidade_id)


@router.post("/", response_model=FinalidadeResponse, status_code=201)
def create(data: FinalidadeCreate, db: Session = Depends(get_db)):
    return FinalidadeService.create(db, data.model_dump())


@router.put("/{finalidade_id}", response_model=FinalidadeResponse)
def update(
    finalidade_id: int,
    data: FinalidadeUpdate,
    db: Session = Depends(get_db),
):
    return FinalidadeService.update(db, finalidade_id, data.model_dump(exclude_none=True))


@router.delete("/{finalidade_id}")
def delete(finalidade_id: int, db: Session = Depends(get_db)):
    FinalidadeService.delete(db, finalidade_id)
    return {"message": "Finalidade removida com sucesso"}
