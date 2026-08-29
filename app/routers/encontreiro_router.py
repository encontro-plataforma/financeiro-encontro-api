from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile as FastAPIUploadFile
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.enums import SituacaoCamisa
from app.schemas.encontreiro_filter_dto import EncontreiroFilterDto
from app.schemas.encontreiro_schema import (
    EncontreiroCreate,
    EncontreiroResponse,
    EncontreiroUpdate,
)
from app.schemas.pagination_schema import Page
from app.services.encontreiro_service import EncontreiroService

router = APIRouter(prefix="/encontreiros", tags=["Secretaria - Encontreiros"])


@router.get("/", response_model=Page[EncontreiroResponse])
def list_encontreiros(
    params: EncontreiroFilterDto = Depends(),
    equipe_ids: Optional[List[int]] = Query(default=None),
    situacao_camisa: Optional[List[SituacaoCamisa]] = Query(default=None),
    db: Session = Depends(get_db),
):
    params.equipe_ids = equipe_ids
    params.situacao_camisa = situacao_camisa
    return EncontreiroService.list(db, params)


@router.get("/all", response_model=List[EncontreiroResponse])
def list_all(
    params: EncontreiroFilterDto = Depends(),
    equipe_ids: Optional[List[int]] = Query(default=None),
    situacao_camisa: Optional[List[SituacaoCamisa]] = Query(default=None),
    db: Session = Depends(get_db),
):
    params.equipe_ids = equipe_ids
    params.situacao_camisa = situacao_camisa
    return EncontreiroService.list_all(db, params)


@router.get("/{encontreiro_id}", response_model=EncontreiroResponse)
def get_by_id(encontreiro_id: int, db: Session = Depends(get_db)):
    return EncontreiroService.get_by_id(db, encontreiro_id)


@router.post("/", response_model=EncontreiroResponse, status_code=201)
def create(data: EncontreiroCreate, db: Session = Depends(get_db)):
    return EncontreiroService.create(db, data.model_dump())


@router.put("/{encontreiro_id}", response_model=EncontreiroResponse)
def update(
    encontreiro_id: int,
    data: EncontreiroUpdate,
    db: Session = Depends(get_db),
):
    return EncontreiroService.update(db, encontreiro_id, data.model_dump(exclude_none=True))


@router.patch("/{encontreiro_id}/equipe/{equipe_id}", response_model=EncontreiroResponse)
def alterar_equipe(encontreiro_id: int, equipe_id: int, db: Session = Depends(get_db)):
    return EncontreiroService.alterar_equipe(db, encontreiro_id, equipe_id)


@router.delete("/{encontreiro_id}")
def delete(encontreiro_id: int, db: Session = Depends(get_db)):
    EncontreiroService.delete(db, encontreiro_id)
    return {"message": "Encontreiro removido com sucesso"}


@router.post("/conciliacao")
def conciliar(
    background_tasks: BackgroundTasks,
    file: FastAPIUploadFile = File(...),
    db: Session = Depends(get_db),
):
    upload = EncontreiroService.iniciar_conciliacao(file, db)
    background_tasks.add_task(
        EncontreiroService.processar_em_background,
        upload.id.value,
        upload.conteudo_csv.value,
    )
    return {"upload_id": upload.id, "status": upload.status}
