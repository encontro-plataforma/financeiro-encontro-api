from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.circulo_schema import CirculoResponse
from app.schemas.equipe_schema import EquipeResponse
from app.schemas.lancamento_schema import LancamentoResumo


class PadrinhoResumo(BaseModel):
    id: int
    nome: str
    apelido: str | None
    equipe: EquipeResponse | None

    class Config:
        from_attributes = True


class EncontristaResponse(BaseModel):
    id: int
    dt_entrega: date | None
    dt_validade: date | None
    padrinho_id: int
    padrinho: PadrinhoResumo | None
    carta: bool
    album: bool
    nome: str
    apelido: str | None
    dt_nascimento: date | None
    idade: int | None
    circulo_id: int | None
    circulo: CirculoResponse | None
    onde_veio_ficha: str | None
    instagram: str | None
    contato: str | None
    religiao: str | None
    igreja: str | None
    endereco: str | None
    cidade: str | None
    camisa: str | None
    blusa: bool
    veiculo: str | None
    contato_emerg: str | None
    nome_emerg: str | None
    parentesco_emerg: str | None
    medicacao: str | None
    alergia_comorbidade: str | None
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


class EncontristaCreate(BaseModel):
    dt_entrega: date | None = None
    dt_validade: date | None = None
    padrinho_id: int
    carta: bool = False
    album: bool = False
    nome: str
    apelido: str | None = None
    dt_nascimento: date | None = None
    idade: int | None = None
    circulo_id: int | None = None
    onde_veio_ficha: str = ""
    instagram: str | None = None
    contato: str | None = None
    religiao: str | None = None
    igreja: str | None = None
    endereco: str | None = None
    cidade: str | None = None
    camisa: str | None = None
    blusa: bool = False
    veiculo: str | None = None
    contato_emerg: str | None = None
    nome_emerg: str | None = None
    parentesco_emerg: str | None = None
    medicacao: str | None = None
    alergia_comorbidade: str | None = None
    dt_pagamento: date | None = None
    nome_pagador: str | None = None
    pagamento: Decimal | None = None
    observacao: str | None = None


class EncontristaUpdate(BaseModel):
    dt_entrega: date | None = None
    dt_validade: date | None = None
    padrinho_id: int | None = None
    carta: bool | None = None
    album: bool | None = None
    nome: str | None = None
    apelido: str | None = None
    dt_nascimento: date | None = None
    idade: int | None = None
    circulo_id: int | None = None
    onde_veio_ficha: str | None = None
    instagram: str | None = None
    contato: str | None = None
    religiao: str | None = None
    igreja: str | None = None
    endereco: str | None = None
    cidade: str | None = None
    camisa: str | None = None
    blusa: bool | None = None
    veiculo: str | None = None
    contato_emerg: str | None = None
    nome_emerg: str | None = None
    parentesco_emerg: str | None = None
    medicacao: str | None = None
    alergia_comorbidade: str | None = None
    dt_pagamento: date | None = None
    nome_pagador: str | None = None
    pagamento: Decimal | None = None
    observacao: str | None = None
