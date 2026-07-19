import hashlib
from datetime import datetime
import re

def _normalizar_texto(texto: str) -> str:
    """
    Normaliza texto para evitar diferenças triviais:
    - remove espaços duplicados
    - lower case
    - trim
    """
    texto = texto.lower().strip()
    texto = re.sub(r"\s+", " ", texto)
    return texto


def gerar_hash(descricao: str, valor: float, data: datetime, observacao: str) -> str:
    """
    Gera hash determinístico para identificar transações únicas.
    Campos: descricao + valor + data_pagamento + observacao.
    """
    descricao_norm  = _normalizar_texto(descricao)
    observacao_norm = _normalizar_texto(observacao)

    base = f"{descricao_norm}|{valor:.2f}|{data.strftime('%Y-%m-%d')}|{observacao_norm}"

    return hashlib.sha256(base.encode("utf-8")).hexdigest()
