from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.pagination_schema import Page
from app.schemas.regra_filter_dto import RegraGrupoFilterDto
from app.schemas.regra_schema import (
    RegraGrupoCreate,
    RegraGrupoResponse,
    RegraGrupoUpdate,
)
from app.services.regra_service import RegraService

router = APIRouter(prefix="/regras", tags=["Regras"])


@router.get("/grupos", response_model=Page[RegraGrupoResponse])
def list_grupos(
    params: RegraGrupoFilterDto = Depends(),
    db: Session = Depends(get_db),
):
    return RegraService.list(db, params)


@router.get("/grupos/all", response_model=List[RegraGrupoResponse])
def list_all_grupos(
    params: RegraGrupoFilterDto = Depends(),
    db: Session = Depends(get_db),
):
    return RegraService.list_all(db, params)


@router.get("/grupos/{grupo_id}", response_model=RegraGrupoResponse)
def get_by_id(grupo_id: int, db: Session = Depends(get_db)):
    return RegraService.get_by_id(db, grupo_id)


@router.post("/grupos", response_model=RegraGrupoResponse, status_code=201)
def create(data: RegraGrupoCreate, db: Session = Depends(get_db)):
    return RegraService.create(db, data.model_dump())


@router.put("/grupos/{grupo_id}", response_model=RegraGrupoResponse)
def update(
    grupo_id: int,
    data: RegraGrupoUpdate,
    db: Session = Depends(get_db),
):
    return RegraService.update(db, grupo_id, data.model_dump(exclude_none=True))


@router.delete("/grupos/{grupo_id}")
def delete(grupo_id: int, db: Session = Depends(get_db)):
    RegraService.delete(db, grupo_id)
    return {"message": "Grupo de regras removido com sucesso"}
