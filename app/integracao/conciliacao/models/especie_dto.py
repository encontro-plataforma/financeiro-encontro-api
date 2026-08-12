from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class EspecieLinhaDTO:
    """Uma linha do extrato manual de espécie -- já diz explicitamente do que
    se trata (sem texto livre pra interpretar, diferente do extrato
    bancário)."""
    data: date
    tipo: str
    nome: Optional[str]
    descricao: Optional[str]
    valor: Decimal
    observacao: Optional[str]
    linha_csv: int
