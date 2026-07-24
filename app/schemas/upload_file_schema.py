from pydantic import BaseModel
from datetime import datetime


class UploadFileResponse(BaseModel):
    id: int
    nome_arquivo: str
    tamanho_bytes: int | None
    processado_em: datetime
    error_code: str | None
    error_message: str | None

    class Config:
        from_attributes = True
