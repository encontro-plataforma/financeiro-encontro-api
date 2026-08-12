from pydantic import BaseModel
from datetime import datetime

from app.models.enums import StatusProcessamento, TipoOrigemUpload


class UploadFileResponse(BaseModel):
    id: int
    nome_arquivo: str
    tamanho_bytes: int | None
    processado_em: datetime
    status: StatusProcessamento
    tipo_origem: TipoOrigemUpload | None
    error_code: str | None
    error_message: str | None
    resultado_processamento: str | None

    class Config:
        from_attributes = True


class UploadFileStatusResponse(BaseModel):
    id: int
    status: StatusProcessamento

    class Config:
        from_attributes = True
