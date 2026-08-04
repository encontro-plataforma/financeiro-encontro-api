import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from app.integracao.regras.dtos import ItemDetalhamento, PendenciaAuditoria
from app.models.enums import TipoDetalhamento
from app.utils.parse_utils import remover_acentos

_TIPOS_INSCRICAO = {TipoDetalhamento.INSCRICAO_ENCONTREIRO, TipoDetalhamento.INSCRICAO_ENCONTRISTA}


def _parse_valor(bruto: str) -> Optional[Decimal]:
    try:
        return Decimal(bruto.replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


def _valor_se_regra_casar(regra, texto_normalizado: str) -> Optional[Decimal]:
    """Todas as RegraCondicao da regra precisam casar (AND) para a regra
    "casar". O valor do Detalhamento vem do grupo de captura da primeira
    condição, em ordem, que tiver um."""
    valor = None
    for condicao in regra.condicoes:
        match = re.search(condicao.padrao_regex, texto_normalizado, re.IGNORECASE)
        if not match:
            return None
        if valor is None and match.groups():
            valor = _parse_valor(match.group(1))
    return valor


def extrair_detalhamentos(
    pendencia: PendenciaAuditoria,
    grupos: list,
    tipo_inscricao_padrao: TipoDetalhamento,
) -> list[ItemDetalhamento]:
    """Etapa B (Extração): lê `pendencia.observacao` e avalia, independentemente,
    cada Regra ativa dos grupos aplicáveis (o grupo do próprio tipo de pendência
    + o grupo OFERTAS) — cada Regra que casar gera 1 ItemDetalhamento. Se
    nenhuma regra casar, cai no fallback: 1 item com o valor total pago,
    vinculado à própria pendência."""
    texto = remover_acentos(pendencia.observacao or "").lower()
    itens: list[ItemDetalhamento] = []

    for grupo in grupos:
        for regra in grupo.regras:
            if not regra.ativo:
                continue

            valor = _valor_se_regra_casar(regra, texto)
            if valor is None or valor <= 0:
                continue

            referencia_id = pendencia.id if regra.tipo_detalhamento_resultado in _TIPOS_INSCRICAO else None
            itens.append(ItemDetalhamento(
                tipo=regra.tipo_detalhamento_resultado,
                valor=valor,
                referencia_id=referencia_id,
            ))

    if not itens:
        itens.append(ItemDetalhamento(
            tipo=tipo_inscricao_padrao,
            valor=pendencia.pagamento,
            referencia_id=pendencia.id,
        ))

    return itens
