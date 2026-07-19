from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List

from app.core.exceptions import NotFoundException

from app.database.session import get_db
from app.services.extrato_bancario_service import ExtratoBancarioService
from app.schemas.extrato_bancario_schema import ExtratoBancarioResponse
from app.schemas.pagination_schema import Page
from app.schemas.extrato_bancario_filter_dto import ExtratoBancarioFilterDto

router = APIRouter(prefix="/extratos-bancarios", tags=["Extratos Bancários"])


@router.get("/", response_model=Page[ExtratoBancarioResponse])
def list(
    params: ExtratoBancarioFilterDto = Depends(),
    db: Session = Depends(get_db),
):
    return ExtratoBancarioService.list(db, params)


@router.get("/all", response_model=List[ExtratoBancarioResponse])
def list_all(
    params: ExtratoBancarioFilterDto = Depends(),
    db: Session = Depends(get_db),
):
    return ExtratoBancarioService.list_all(db, params)


@router.get("/{extrato_id}", response_model=ExtratoBancarioResponse)
def get_by_id(extrato_id: int, db: Session = Depends(get_db)):
    return ExtratoBancarioService.get_by_id(db, extrato_id)


@router.get("/{extrato_id}/download")
def download(extrato_id: int, db: Session = Depends(get_db)):
    extrato = ExtratoBancarioService.get_by_id(db, extrato_id)
    if not extrato.conteudo_csv:
        raise NotFoundException("Arquivo não encontrado no servidor")
    return Response(
        content=extrato.conteudo_csv,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={extrato.nome_arquivo}"},
    )


@router.delete("/{extrato_id}")
def delete(extrato_id: int, db: Session = Depends(get_db)):
    ExtratoBancarioService.delete(db, extrato_id)
    return {"message": "Extrato bancário removido com sucesso"}