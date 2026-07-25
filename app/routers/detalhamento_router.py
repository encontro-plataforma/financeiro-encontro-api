from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.detalhamento_filter_dto import DetalhamentoFilterDto
from app.schemas.detalhamento_schema import (
    DetalhamentoCreate,
    DetalhamentoResponse,
    DetalhamentoUpdate,
)
from app.schemas.pagination_schema import Page
from app.services.auditoria_service import AuditoriaService
from app.services.detalhamento_service import DetalhamentoService

router = APIRouter(prefix="/detalhamentos", tags=["Secretaria - Detalhamentos"])


@router.get("/", response_model=Page[DetalhamentoResponse])
def list_detalhamentos(
    params: DetalhamentoFilterDto = Depends(),
    db: Session = Depends(get_db),
):
    return DetalhamentoService.list(db, params)


@router.get("/all", response_model=List[DetalhamentoResponse])
def list_all(
    params: DetalhamentoFilterDto = Depends(),
    db: Session = Depends(get_db),
):
    return DetalhamentoService.list_all(db, params)


@router.get("/{detalhamento_id}", response_model=DetalhamentoResponse)
def get_by_id(detalhamento_id: int, db: Session = Depends(get_db)):
    return DetalhamentoService.get_by_id(db, detalhamento_id)


@router.post("/", response_model=DetalhamentoResponse, status_code=201)
def create(data: DetalhamentoCreate, db: Session = Depends(get_db)):
    return DetalhamentoService.create(db, data.model_dump())


@router.put("/{detalhamento_id}", response_model=DetalhamentoResponse)
def update(
    detalhamento_id: int,
    data: DetalhamentoUpdate,
    db: Session = Depends(get_db),
):
    return DetalhamentoService.update(db, detalhamento_id, data.model_dump(exclude_none=True))


@router.delete("/{detalhamento_id}")
def delete(detalhamento_id: int, db: Session = Depends(get_db)):
    DetalhamentoService.delete(db, detalhamento_id)
    return {"message": "Detalhamento removido com sucesso"}


@router.post("/auditoria")
def auditoria(db: Session = Depends(get_db)):
    return AuditoriaService.processar(db)
