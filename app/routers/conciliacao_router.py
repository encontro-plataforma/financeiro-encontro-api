from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.cartao_service import CartaoService
from app.services.conciliacao_service import ConciliacaoService
from app.services.especie_service import EspecieService

router = APIRouter(prefix="/conciliacao", tags=["Conciliação"])


@router.post("/upload")
def upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    upload_obj = ConciliacaoService.iniciar_conciliacao(file, db)
    background_tasks.add_task(
        ConciliacaoService.processar_em_background,
        upload_obj.id,
        upload_obj.conteudo_csv,
        upload_obj.nome_arquivo,
    )
    return {"upload_id": upload_obj.id, "status": upload_obj.status}


@router.post("/upload-especie")
def upload_especie(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    upload_obj = EspecieService.iniciar_conciliacao(file, db)
    background_tasks.add_task(
        EspecieService.processar_em_background,
        upload_obj.id,
        upload_obj.conteudo_csv,
    )
    return {"upload_id": upload_obj.id, "status": upload_obj.status}


@router.post("/upload-cartao")
def upload_cartao(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    upload_obj = CartaoService.iniciar_conciliacao(file, db)
    background_tasks.add_task(
        CartaoService.processar_em_background,
        upload_obj.id,
        upload_obj.conteudo_csv,
    )
    return {"upload_id": upload_obj.id, "status": upload_obj.status}
