from datetime import date
from typing import List, Optional

from app.schemas.query_params import QueryParams


class EncontristaFilterDto(QueryParams):
    nome: Optional[str] = None
    apelido: Optional[str] = None
    nome_ou_apelido: Optional[str] = None
    nome_pagador: Optional[str] = None
    circulo_nome: Optional[str] = None
    circulo_ids: Optional[List[int]] = None  # 0 = "sem círculo" (circulo_id IS NULL)
    padrinho_id: Optional[int] = None
    auditado: Optional[bool] = None
    camisa: Optional[str] = None
    blusa: Optional[bool] = None
    carta: Optional[bool] = None
    album: Optional[bool] = None
    dt_entrega_inicio: Optional[date] = None
    dt_entrega_fim: Optional[date] = None
    dt_nascimento_inicio: Optional[date] = None
    dt_nascimento_fim: Optional[date] = None
