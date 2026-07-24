import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional


def remover_acentos(texto: str) -> str:
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalizar_cabecalho(texto: str) -> str:
    """Normaliza um cabeçalho de CSV para comparação: sem acento, maiúsculo,
    sem espaços duplicados/nas bordas."""
    texto = remover_acentos(texto or "").strip().upper()
    return " ".join(texto.split())


def parse_bool(valor: Optional[str]) -> bool:
    if not valor:
        return False
    return normalizar_cabecalho(valor) in {"SIM", "S", "X", "TRUE", "1"}


def parse_decimal_br(valor: Optional[str]) -> Optional[Decimal]:
    if valor is None or not valor.strip():
        return None
    try:
        return Decimal(valor.strip().replace(".", "").replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError(f"Valor monetário inválido: '{valor}'") from exc


def parse_date_br(valor: Optional[str]) -> Optional[date]:
    if valor is None or not valor.strip():
        return None
    try:
        return datetime.strptime(valor.strip(), "%d/%m/%Y").date()
    except ValueError as exc:
        raise ValueError(f"Data inválida: '{valor}' (esperado dd/mm/aaaa)") from exc
