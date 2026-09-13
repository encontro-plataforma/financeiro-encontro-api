import re

from app.utils.parse_utils import remover_acentos

MOTIVO_PAGAMENTO_MULTIPLO = "Pagamento múltiplo — requer tratamento manual."

_PADRAO_PAGAMENTO_MULTIPLO = re.compile(r"pagamentos?\s+multiplos?")


def eh_pagamento_multiplo(observacao: str | None) -> bool:
    """Checagem barata (sem acesso a banco) sobre a observação da própria
    pendência -- roda ANTES de buscar candidatos na Etapa A, pra não gastar
    uma query com pendências que de qualquer forma serão puladas. Fichas
    marcadas assim são identificadas, mas o match ainda não é processado
    para elas (fica pra uma tarefa futura)."""
    return bool(_PADRAO_PAGAMENTO_MULTIPLO.search(remover_acentos(observacao or "").lower()))
