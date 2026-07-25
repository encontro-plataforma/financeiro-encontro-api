from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.conciliacao_service import ConciliacaoService

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
