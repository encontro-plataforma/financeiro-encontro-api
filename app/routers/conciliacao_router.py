from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.conciliacao_service import ConciliacaoService

router = APIRouter(prefix="/conciliacao", tags=["Conciliação"])


@router.post("/upload")
def upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return ConciliacaoService.upload_and_process(file, db)