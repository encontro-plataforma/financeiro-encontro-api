from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from app.schemas.circulo_schema import CirculoResponse
from app.schemas.detalhamento_schema import DetalhamentoVinculoResumo
from app.schemas.equipe_schema import EquipeResponse
from app.schemas.lancamento_schema import LancamentoResumo


class PadrinhoResumo(BaseModel):
    id: int
    nome: str
    apelido: Optional[str]
    equipe: Optional[EquipeResponse]

    class Config:
        from_attributes = True


class EncontristaResponse(BaseModel):
    id: int
    dt_entrega: Optional[date]
    dt_validade: Optional[date]
    padrinho_id: int
    padrinho: Optional[PadrinhoResumo]
    carta: bool
    album: bool
    nome: str
    apelido: Optional[str]
    dt_nascimento: Optional[date]
    idade: Optional[int]
    circulo_id: Optional[int]
    circulo: Optional[CirculoResponse]
    onde_veio_ficha: Optional[str]
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
    # Campos legados (compatibilidade) — representam sempre o vínculo mais
    # antigo (criado_em asc), mesmo quando há vários. Preferir os campos
    # abaixo para lidar com múltiplos pagamentos.
    detalhamento_id: Optional[int] = None
    lancamento_vinculado_id: Optional[int] = None
    lancamento_vinculado: Optional[LancamentoResumo] = None
    # Só vêm populados no GET /encontristas/{id} (detalhe); na listagem ficam
    # como [] — não significa "sem vínculos", só "não carregado nesta resposta".
    detalhamentos_vinculados: list[DetalhamentoVinculoResumo] = []
    lancamentos_vinculados: list[LancamentoResumo] = []
    total_vinculado: Decimal = Decimal("0")
    saldo_pendente: Optional[Decimal] = None
    quantidade_vinculos: int = 0

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
    onde_veio_ficha: str = ""
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
    onde_veio_ficha: Optional[str] = None
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
