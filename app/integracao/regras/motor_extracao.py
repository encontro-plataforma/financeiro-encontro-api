import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from app.integracao.regras.dtos import ItemDetalhamento, PendenciaAuditoria
from app.models.enums import ModoExtracaoRegra, TipoDetalhamento
from app.utils.parse_utils import remover_acentos

_TIPOS_INSCRICAO = {TipoDetalhamento.INSCRICAO_ENCONTREIRO, TipoDetalhamento.INSCRICAO_ENCONTRISTA}
_PADRAO_VALOR_APOS_TOKEN = r"\D*?(\d+(?:[.,]\d{2})?)"


def _parse_valor(bruto: str) -> Optional[Decimal]:
    try:
        return Decimal(bruto.replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


def _valor_se_regra_casar(regra, texto_normalizado: str) -> Optional[Decimal]:
    """Modo TOKEN_VALOR: todas as RegraCondicao da regra precisam casar (AND)
    para a regra "casar". O valor do Detalhamento vem do primeiro grupo de
    captura não vazio da primeira condição, em ordem, que tiver um — um
    padrão pode ter mais de um grupo quando testa a mesma coisa em ordens
    diferentes (ex.: "inscrição 90" vs "90 de inscrição"), só um dos ramos
    casa por vez."""
    valor = None
    for condicao in regra.condicoes:
        match = re.search(condicao.padrao_regex, texto_normalizado, re.IGNORECASE)
        if not match:
            return None
        if valor is None:
            capturado = next((g for g in match.groups() if g is not None), None)
            if capturado is not None:
                valor = _parse_valor(capturado)
    return valor


def _valor_por_nome_na_lista(nome_pessoa: str, texto_normalizado: str) -> Optional[Decimal]:
    """Modo NOME_NA_LISTA: cobre um único pagamento cobrindo várias
    inscrições nomeadas na mesma observação (ex.: "Luiza Rochelle de 100
    reais, Samuel Augusto de 100 reais..."). Busca a primeira palavra do
    nome da própria pessoa (o nome pode estar incompleto na observação — só
    o primeiro nome, com sobrenome opcional) e captura o valor logo em
    seguida. Limitação conhecida: se duas pessoas do mesmo pagamento
    compartilharem a primeira palavra do nome, pode ambiguar — caso raro,
    fora de escopo por ora."""
    if not nome_pessoa:
        return None

    primeira_palavra = remover_acentos(nome_pessoa).lower().split()
    if not primeira_palavra:
        return None

    padrao = r"\b" + re.escape(primeira_palavra[0]) + r"\b" + _PADRAO_VALOR_APOS_TOKEN
    match = re.search(padrao, texto_normalizado, re.IGNORECASE)
    if not match:
        return None

    return _parse_valor(match.group(1))


def _valor_se_regra_bater(regra, pendencia: PendenciaAuditoria, texto_normalizado: str) -> Optional[Decimal]:
    if regra.modo_extracao == ModoExtracaoRegra.NOME_NA_LISTA:
        return _valor_por_nome_na_lista(pendencia.nome, texto_normalizado)
    return _valor_se_regra_casar(regra, texto_normalizado)


def extrair_detalhamentos(
    pendencia: PendenciaAuditoria,
    grupos: list,
    tipo_inscricao_padrao: TipoDetalhamento,
) -> list[ItemDetalhamento]:
    """Etapa B (Extração): lê `pendencia.observacao` e avalia as Regras
    ativas dos grupos aplicáveis, agrupadas por `tipo_detalhamento_resultado`
    — dentro de cada tipo, para na primeira Regra (em ordem) que bater;
    tipos diferentes (ex. Inscrição vs Oferta) são avaliados independentemente
    e podem gerar Detalhamentos ao mesmo tempo. Se nenhum tipo bateu, cai no
    fallback: 1 item com o valor total pago, vinculado à própria pendência."""
    texto = remover_acentos(pendencia.observacao or "").lower()

    regras_por_tipo: dict = {}
    for grupo in grupos:
        for regra in grupo.regras:
            if not regra.ativo:
                continue
            regras_por_tipo.setdefault(regra.tipo_detalhamento_resultado, []).append(regra)

    itens: list[ItemDetalhamento] = []
    for tipo, regras in regras_por_tipo.items():
        for regra in sorted(regras, key=lambda r: r.ordem):
            valor = _valor_se_regra_bater(regra, pendencia, texto)
            if valor is None or valor <= 0:
                continue

            referencia_id = pendencia.id if tipo in _TIPOS_INSCRICAO else None
            itens.append(ItemDetalhamento(tipo=tipo, valor=valor, referencia_id=referencia_id))
            break

    if not itens:
        itens.append(ItemDetalhamento(
            tipo=tipo_inscricao_padrao,
            valor=pendencia.pagamento,
            referencia_id=pendencia.id,
        ))

    return itens
