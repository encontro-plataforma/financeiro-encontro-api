from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import SituacaoCamisa
from app.schemas.equipe_schema import EquipeResponse
from app.schemas.lancamento_schema import LancamentoResumo


class EncontreiroResponse(BaseModel):
    id: int
    dt_inscricao: date | None
    nome: str
    apelido: str | None
    instagram: str | None
    telefone: str | None
    estado_civil: str | None
    igreja: str | None
    religiao: str | None
    contato_emerg: str | None
    nome_emerg: str | None
    parentesco_emerg: str | None
    alergia_comorbidade: str | None
    equipe_id: int | None
    equipe: EquipeResponse | None
    camisa: str | None
    situacao_camisa: SituacaoCamisa
    veiculo: str | None
    dt_pagamento: date | None
    nome_pagador: str | None
    pagamento: Decimal | None
    observacao: str | None
    criado_em: datetime
    auditado: bool
    detalhamento_id: int | None = None
    lancamento_vinculado_id: int | None = None
    lancamento_vinculado: LancamentoResumo | None = None

    class Config:
        from_attributes = True


class EncontreiroCreate(BaseModel):
    dt_inscricao: date | None = None
    nome: str
    apelido: str | None = None
    instagram: str | None = None
    telefone: str | None = None
    estado_civil: str | None = None
    igreja: str | None = None
    religiao: str | None = None
    contato_emerg: str | None = None
    nome_emerg: str | None = None
    parentesco_emerg: str | None = None
    alergia_comorbidade: str | None = None
    equipe_id: int
    camisa: str | None = None
    situacao_camisa: SituacaoCamisa = SituacaoCamisa.SEM_BLUSA
    veiculo: str | None = None
    dt_pagamento: date | None = None
    nome_pagador: str | None = None
    pagamento: Decimal | None = None
    observacao: str | None = None


class EncontreiroUpdate(BaseModel):
    dt_inscricao: date | None = None
    nome: str | None = None
    apelido: str | None = None
    instagram: str | None = None
    telefone: str | None = None
    estado_civil: str | None = None
    igreja: str | None = None
    religiao: str | None = None
    contato_emerg: str | None = None
    nome_emerg: str | None = None
    parentesco_emerg: str | None = None
    alergia_comorbidade: str | None = None
    equipe_id: int | None = None
    camisa: str | None = None
    situacao_camisa: SituacaoCamisa | None = None
    veiculo: str | None = None
    dt_pagamento: date | None = None
    nome_pagador: str | None = None
    pagamento: Decimal | None = None
    observacao: str | None = None
