from typing import Optional

from pydantic import BaseModel


class TotaisResponse(BaseModel):
    total_receitas: float
    total_despesas: float
    saldo: float
    quantidade: int


class PorDiaItem(BaseModel):
    dia: str
    total_receitas: float
    total_despesas: float
    saldo: float


class PorMesItem(BaseModel):
    mes: str
    total_receitas: float
    total_despesas: float
    saldo: float


class PorFinalidadeItem(BaseModel):
    finalidade_id: Optional[int]
    nome: str
    total_valor: float
    quantidade: int
