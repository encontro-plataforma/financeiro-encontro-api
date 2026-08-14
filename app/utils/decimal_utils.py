from decimal import Decimal
from typing import Optional


def to_decimal(valor: Optional[object]) -> Decimal:
    """Converte para Decimal via str() (evita o erro de arredondamento de
    Decimal(float) direto). None vira Decimal("0")."""
    return Decimal(str(valor)) if valor is not None else Decimal("0")
