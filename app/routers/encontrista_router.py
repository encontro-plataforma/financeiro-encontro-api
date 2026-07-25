from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile as FastAPIUploadFile
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.encontrista_filter_dto import EncontristaFilterDto
from app.schemas.encontrista_schema import (
    EncontristaCreate,
    EncontristaResponse,
    EncontristaUpdate,
    PadrinhoResumo,
)
from app.schemas.pagination_schema import Page
from app.services.encontrista_service import EncontristaService

router = APIRouter(prefix="/encontristas", tags=["Secretaria - Encontristas"])


@router.get("/", response_model=Page[EncontristaResponse])
def list_encontristas(
    params: EncontristaFilterDto = Depends(),
    circulo_ids: Optional[List[int]] = Query(default=None),
    db: Session = Depends(get_db),
):
    params.circulo_ids = circulo_ids
    return EncontristaService.list(db, params)


@router.get("/all", response_model=List[EncontristaResponse])
def list_all(
    params: EncontristaFilterDto = Depends(),
    circulo_ids: Optional[List[int]] = Query(default=None),
    db: Session = Depends(get_db),
):
    params.circulo_ids = circulo_ids
    return EncontristaService.list_all(db, params)


@router.get("/padrinhos-disponiveis", response_model=List[PadrinhoResumo])
def padrinhos_disponiveis(db: Session = Depends(get_db)):
    return EncontristaService.padrinhos_disponiveis(db)


@router.get("/{encontrista_id}", response_model=EncontristaResponse)
def get_by_id(encontrista_id: int, db: Session = Depends(get_db)):
    return EncontristaService.get_by_id(db, encontrista_id)


@router.post("/", response_model=EncontristaResponse, status_code=201)
def create(data: EncontristaCreate, db: Session = Depends(get_db)):
    return EncontristaService.create(db, data.model_dump())


@router.put("/{encontrista_id}", response_model=EncontristaResponse)
def update(
    encontrista_id: int,
    data: EncontristaUpdate,
    db: Session = Depends(get_db),
):
    return EncontristaService.update(db, encontrista_id, data.model_dump(exclude_none=True))


@router.delete("/{encontrista_id}")
def delete(encontrista_id: int, db: Session = Depends(get_db)):
    EncontristaService.delete(db, encontrista_id)
    return {"message": "Encontrista removido com sucesso"}


@router.post("/conciliacao")
def conciliar(
    background_tasks: BackgroundTasks,
    file: FastAPIUploadFile = File(...),
    db: Session = Depends(get_db),
):
    upload = EncontristaService.iniciar_conciliacao(file, db)
    background_tasks.add_task(
        EncontristaService.processar_em_background, upload.id, upload.conteudo_csv
    )
    return {"upload_id": upload.id, "status": upload.status}
