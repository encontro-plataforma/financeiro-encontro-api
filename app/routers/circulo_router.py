from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.circulo_filter_dto import CirculoFilterDto
from app.schemas.circulo_schema import (
    CirculoCreate,
    CirculoResponse,
    CirculoUpdate,
)
from app.schemas.pagination_schema import Page
from app.services.circulo_service import CirculoService

router = APIRouter(prefix="/circulos", tags=["Secretaria - Circulos"])


@router.get("/", response_model=Page[CirculoResponse])
def list_circulos(
    params: CirculoFilterDto = Depends(),
    db: Session = Depends(get_db),
):
    return CirculoService.list(db, params)


@router.get("/all", response_model=List[CirculoResponse])
def list_all(
    params: CirculoFilterDto = Depends(),
    db: Session = Depends(get_db),
):
    return CirculoService.list_all(db, params)


@router.get("/{circulo_id}", response_model=CirculoResponse)
def get_by_id(circulo_id: int, db: Session = Depends(get_db)):
    return CirculoService.get_by_id(db, circulo_id)


@router.post("/", response_model=CirculoResponse, status_code=201)
def create(data: CirculoCreate, db: Session = Depends(get_db)):
    return CirculoService.create(db, data.model_dump())


@router.put("/{circulo_id}", response_model=CirculoResponse)
def update(
    circulo_id: int,
    data: CirculoUpdate,
    db: Session = Depends(get_db),
):
    return CirculoService.update(db, circulo_id, data.model_dump(exclude_none=True))


@router.delete("/{circulo_id}")
def delete(circulo_id: int, db: Session = Depends(get_db)):
    CirculoService.delete(db, circulo_id)
    return {"message": "Circulo removido com sucesso"}
