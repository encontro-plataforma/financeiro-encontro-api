import re
from decimal import Decimal
from typing import Optional

from app.integracao.regras.dtos import CandidatoLancamento, PendenciaAuditoria
from app.models.enums import FormaPagamento
from app.utils.parse_utils import remover_acentos

_TOLERANCIA = Decimal("0.01")

# Compostos ("cartao de credito"/"cartao de debito") avaliados antes do
# genérico ("cartao"), senão o genérico casaria primeiro e mascararia o
# débito. "Cartão" sozinho (sem dizer crédito/débito) é tratado como crédito.
_TOKENS_FORMA_PAGAMENTO = [
    (re.compile(r"cartao\s+de\s+credito"), FormaPagamento.CARTAO_CREDITO),
    (re.compile(r"cartao\s+de\s+debito"), FormaPagamento.CARTAO_DEBITO),
    (re.compile(r"cartao"), FormaPagamento.CARTAO_CREDITO),
    (re.compile(r"pix"), FormaPagamento.PIX),
    (re.compile(r"dinheiro"), FormaPagamento.DINHEIRO),
]


def _forma_pagamento_mencionada(texto_normalizado: str) -> Optional[FormaPagamento]:
    for padrao, forma in _TOKENS_FORMA_PAGAMENTO:
        if padrao.search(texto_normalizado):
            return forma
    return None


def selecionar_lancamento(
    pendencia: PendenciaAuditoria,
    candidatos: list[CandidatoLancamento],
) -> Optional[CandidatoLancamento]:
    """Etapa A (Match): entre os candidatos (já filtrados por mesma data e
    tipo RECEITA na consulta ao banco), escolhe o lançamento cujo VALOR
    ORIGINAL comporta o valor de referência da pendência e cujo nome do
    pagador aparece na descrição do lançamento (comparação sempre
    case-insensitive e sem acento). Usar o valor original (não a capacidade
    restante) é o que permite que várias pessoas compartilhando o mesmo
    lançamento (ex.: 1 PIX cobrindo 2 inscrições) continuem encontrando o
    mesmo candidato mesmo depois que a primeira já consumiu parte dele — só
    a Etapa B decide, lendo a observação, quanto cabe a cada uma. Ainda
    assim, um lançamento já 100% consumido (sem nenhuma capacidade sobrando)
    é descartado. Se a observação da pendência mencionar uma forma de
    pagamento reconhecível (pix/dinheiro/cartão de crédito/cartão de
    débito), filtra os candidatos mais uma vez por essa forma — evita ligar,
    por exemplo, um lançamento via cartão a uma inscrição paga via pix. Em
    caso de empate, vence o de menor id (mais antigo)."""
    if not pendencia.nome_pagador:
        return None

    nome_normalizado = remover_acentos(pendencia.nome_pagador).lower()

    validos = [
        candidato for candidato in candidatos
        if candidato.valor >= pendencia.pagamento - _TOLERANCIA
        and candidato.capacidade_restante > _TOLERANCIA
        and nome_normalizado in remover_acentos(candidato.descricao or "").lower()
    ]

    if not validos:
        return None

    texto_observacao = remover_acentos(pendencia.observacao or "").lower()
    forma_mencionada = _forma_pagamento_mencionada(texto_observacao)
    if forma_mencionada is not None:
        validos = [c for c in validos if c.forma_pagamento == forma_mencionada]
        if not validos:
            return None

    return min(validos, key=lambda candidato: candidato.id)
