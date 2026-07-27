from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List

from app.core.exceptions import NotFoundException

from app.database.session import get_db
from app.services.upload_file_service import UploadFileService
from app.schemas.upload_file_schema import UploadFileResponse, UploadFileStatusResponse
from app.schemas.pagination_schema import Page
from app.schemas.upload_file_filter_dto import UploadFileFilterDto

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.get("/", response_model=Page[UploadFileResponse])
def list(
    params: UploadFileFilterDto = Depends(),
    db: Session = Depends(get_db),
):
    return UploadFileService.list(db, params)


@router.get("/all", response_model=List[UploadFileResponse])
def list_all(
    params: UploadFileFilterDto = Depends(),
    db: Session = Depends(get_db),
):
    return UploadFileService.list_all(db, params)


@router.get("/{upload_id}", response_model=UploadFileResponse)
def get_by_id(upload_id: int, db: Session = Depends(get_db)):
    return UploadFileService.get_by_id(db, upload_id)


@router.get("/{upload_id}/status", response_model=UploadFileStatusResponse)
def get_status(upload_id: int, db: Session = Depends(get_db)):
    return UploadFileService.get_status(db, upload_id)


@router.get("/{upload_id}/download")
def download(upload_id: int, db: Session = Depends(get_db)):
    upload = UploadFileService.get_by_id(db, upload_id)
    if not upload.conteudo_csv:
        raise NotFoundException("Arquivo não encontrado no servidor")
    return Response(
        content=upload.conteudo_csv,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={upload.nome_arquivo}"},
    )


@router.delete("/{upload_id}")
def delete(upload_id: int, db: Session = Depends(get_db)):
    UploadFileService.delete(db, upload_id)
    return {"message": "Arquivo removido com sucesso"}
