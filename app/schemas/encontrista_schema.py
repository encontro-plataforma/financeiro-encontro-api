from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class EncontristaResponse(BaseModel):
    id: int
    dt_entrega: Optional[date]
    dt_validade: Optional[date]
    padrinho_id: int
    carta: bool
    album: bool
    nome: str
    apelido: Optional[str]
    dt_nascimento: Optional[date]
    idade: Optional[int]
    circulo_id: Optional[int]
    instagram: Optional[str]
    contato: Optional[str]
    religiao: Optional[str]
    igreja: Optional[str]
    endereco: Optional[str]
    cidade: Optional[str]
    camisa: Optional[str]
    blusa: bool
    veiculo: Optional[str]
    contato_emerg: Optional[str]
    nome_emerg: Optional[str]
    parentesco_emerg: Optional[str]
    medicacao: Optional[str]
    alergia_comorbidade: Optional[str]
    dt_pagamento: Optional[date]
    nome_pagador: Optional[str]
    pagamento: Optional[Decimal]
    observacao: Optional[str]
    criado_em: datetime
    auditado: bool

    class Config:
        from_attributes = True


class EncontristaCreate(BaseModel):
    dt_entrega: Optional[date] = None
    dt_validade: Optional[date] = None
    padrinho_id: int
    carta: bool = False
    album: bool = False
    nome: str
    apelido: Optional[str] = None
    dt_nascimento: Optional[date] = None
    idade: Optional[int] = None
    circulo_id: Optional[int] = None
    instagram: Optional[str] = None
    contato: Optional[str] = None
    religiao: Optional[str] = None
    igreja: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    camisa: Optional[str] = None
    blusa: bool = False
    veiculo: Optional[str] = None
    contato_emerg: Optional[str] = None
    nome_emerg: Optional[str] = None
    parentesco_emerg: Optional[str] = None
    medicacao: Optional[str] = None
    alergia_comorbidade: Optional[str] = None
    dt_pagamento: Optional[date] = None
    nome_pagador: Optional[str] = None
    pagamento: Optional[Decimal] = None
    observacao: Optional[str] = None


class EncontristaUpdate(BaseModel):
    dt_entrega: Optional[date] = None
    dt_validade: Optional[date] = None
    padrinho_id: Optional[int] = None
    carta: Optional[bool] = None
    album: Optional[bool] = None
    nome: Optional[str] = None
    apelido: Optional[str] = None
    dt_nascimento: Optional[date] = None
    idade: Optional[int] = None
    circulo_id: Optional[int] = None
    instagram: Optional[str] = None
    contato: Optional[str] = None
    religiao: Optional[str] = None
    igreja: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    camisa: Optional[str] = None
    blusa: Optional[bool] = None
    veiculo: Optional[str] = None
    contato_emerg: Optional[str] = None
    nome_emerg: Optional[str] = None
    parentesco_emerg: Optional[str] = None
    medicacao: Optional[str] = None
    alergia_comorbidade: Optional[str] = None
    dt_pagamento: Optional[date] = None
    nome_pagador: Optional[str] = None
    pagamento: Optional[Decimal] = None
    observacao: Optional[str] = None
