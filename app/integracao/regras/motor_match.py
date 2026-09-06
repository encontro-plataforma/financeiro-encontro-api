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
# "Crédito"/"débito" também são reconhecidos sozinhos, sem a palavra
# "cartão" junto (ex.: "pagamento via crédito em 1 parcela") — sempre como
# cartão, já que não existe crédito/débito fora de cartão neste domínio.
_TOKENS_FORMA_PAGAMENTO = [
    (re.compile(r"cartao\s+de\s+credito"), FormaPagamento.CARTAO_CREDITO),
    (re.compile(r"cartao\s+de\s+debito"), FormaPagamento.CARTAO_DEBITO),
    (re.compile(r"cartao"), FormaPagamento.CARTAO_CREDITO),
    (re.compile(r"\bcredito\b"), FormaPagamento.CARTAO_CREDITO),
    (re.compile(r"\bdebito\b"), FormaPagamento.CARTAO_DEBITO),
    (re.compile(r"pix"), FormaPagamento.PIX),
    (re.compile(r"dinheiro"), FormaPagamento.DINHEIRO),
    (re.compile(r"especie"), FormaPagamento.DINHEIRO),
]


def _forma_pagamento_mencionada(texto_normalizado: str) -> FormaPagamento:
    for padrao, forma in _TOKENS_FORMA_PAGAMENTO:
        if padrao.search(texto_normalizado):
            return forma
    return FormaPagamento.PIX


_FORMAS_CARTAO = (FormaPagamento.CARTAO_CREDITO, FormaPagamento.CARTAO_DEBITO)

_RE_PARCELAS = re.compile(r"(\d+)\s*parcelas?")


def _parcelas_mencionadas(texto_normalizado: str) -> int:
    """Lê quantas parcelas a própria pendência menciona na observação (ex.:
    "pagamento via cartão de crédito em 2 parcelas") -- usado só como
    desempate quando várias vendas do extrato de cartão batem em data/valor/
    forma de pagamento. O padrão é 1 parcela (à vista) quando a observação
    não menciona nada."""
    match = _RE_PARCELAS.search(texto_normalizado)
    return int(match.group(1)) if match else 1


def selecionar_lancamento(
    pendencia: PendenciaAuditoria,
    candidatos: list[CandidatoLancamento],
) -> Optional[CandidatoLancamento]:
    """Etapa A (Match): entre os candidatos (já filtrados por mesma data,
    tipo RECEITA, status NAO_CONCILIADO e valor mínimo na consulta ao banco),
    escolhe o lançamento cujo VALOR ORIGINAL comporta o valor de referência
    da pendência (usar o valor original, não a capacidade restante, é o que
    permite que várias pessoas compartilhando o mesmo lançamento -- ex.: 1
    PIX cobrindo 2 inscrições -- continuem encontrando o mesmo candidato
    mesmo depois que a primeira já consumiu parte dele; só a Etapa B decide,
    lendo a observação, quanto cabe a cada uma). Um lançamento já 100%
    consumido é descartado.

    Se a forma de pagamento mencionada na observação da pendência for
    cartão (crédito/débito): o lançamento vem do extrato da maquininha, que
    nunca tem nome de ninguém na descrição -- então o match ignora nome e
    usa só valor + forma de pagamento, desempatando por parcelas (o que a
    observação da pendência menciona vs. o `cart_parcelas` do candidato) e,
    por fim, menor id.

    Nos demais casos (PIX/dinheiro): exige que o nome do pagador da
    pendência apareça na descrição do lançamento (comparação sempre
    case-insensitive e sem acento), e então filtra pela forma de pagamento
    mencionada na observação ("espécie" tratado como sinônimo de dinheiro;
    se a observação não mencionar nenhuma forma reconhecível, assume PIX).
    Em caso de empate, vence o de menor id (mais antigo)."""
    candidatos_valor_ok = [
        candidato for candidato in candidatos
        if candidato.valor >= pendencia.pagamento - _TOLERANCIA
        and (candidato.valor - candidato.soma_detalhamentos) > _TOLERANCIA
    ]
    if not candidatos_valor_ok:
        return None

    texto_observacao = remover_acentos(pendencia.observacao or "").lower()
    forma_assumida = _forma_pagamento_mencionada(texto_observacao)

    if forma_assumida in _FORMAS_CARTAO:
        validos = [c for c in candidatos_valor_ok if c.forma_pagamento == forma_assumida]
        if not validos:
            return None

        if len(validos) > 1:
            parcelas_pendencia = _parcelas_mencionadas(texto_observacao)
            com_parcela_igual = [c for c in validos if c.cart_parcelas == parcelas_pendencia]
            if com_parcela_igual:
                validos = com_parcela_igual

        return min(validos, key=lambda candidato: candidato.id)

    if not pendencia.nome_pagador:
        return None

    nome_normalizado = remover_acentos(pendencia.nome_pagador).lower()

    validos = [
        candidato for candidato in candidatos_valor_ok
        if nome_normalizado in remover_acentos(candidato.descricao or "").lower()
    ]
    if not validos:
        return None

    validos = [c for c in validos if c.forma_pagamento == forma_assumida]
    if not validos:
        return None

    return min(validos, key=lambda candidato: candidato.id)
