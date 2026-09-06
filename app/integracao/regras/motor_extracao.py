import re
from decimal import Decimal, InvalidOperation

from app.integracao.regras.dtos import ItemDetalhamento, PendenciaAuditoria
from app.models.enums import ModoExtracaoRegra, TipoDetalhamento
from app.models.regra import Regra
from app.utils.parse_utils import remover_acentos

_TIPOS_INSCRICAO = {
    TipoDetalhamento.INSCRICAO_ENCONTREIRO,
    TipoDetalhamento.INSCRICAO_ENCONTRISTA,
}

# Conectores comuns em português que separam o nome do valor em observações
# tipo "Fulano de 100 reais" sem fazerem parte do nome de ninguém.
_CONECTORES_NOME = {"de", "da", "do", "das", "dos", "e", "para", "no", "na"}
_TOKEN_NOME_OU_VALOR = re.compile(r"[a-z]+|\d+(?:[.,]\d{2})?")


def _parse_valor(bruto: str) -> Decimal | None:
    try:
        return Decimal(bruto.replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


def _valor_com_regex(regra, texto_normalizado: str) -> Decimal | None:
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


def _valor_por_token_de_nome(
    nome_pessoa: str, texto_normalizado: str
) -> Decimal | None:
    """Modo NOME_NA_LISTA: cobre um único pagamento cobrindo várias
    inscrições nomeadas na mesma observação (ex.: "Luiza Rochelle de 100
    reais, Samuel Augusto de 100 reais..."). Ancora na primeira palavra do
    nome da própria pessoa (palavra inteira) e então caminha palavra por
    palavra até achar o valor: cada palavra intermediária só é aceita se
    estiver contida em algum trecho do nome da pessoa (ex.: "cunha",
    "dourado" ou até um pedaço parcial como "ourado" de "dourado" — sempre
    sem acento e case-insensitive) ou for um conector comum em português
    (`_CONECTORES_NOME`, ex. "de"/"e"/"para"). Qualquer outra palavra nesse
    meio (ex.: "santos", de um "Anderson Santos" que não é esta pessoa) torna
    o trecho ambíguo e a função devolve None em vez de arriscar um valor
    errado."""
    if not nome_pessoa:
        return None

    nome_normalizado = remover_acentos(nome_pessoa).lower()
    palavras_nome = nome_normalizado.split()
    if not palavras_nome:
        return None

    ancora = re.search(
        r"\b" + re.escape(palavras_nome[0]) + r"\b", texto_normalizado, re.IGNORECASE
    )
    if not ancora:
        return None

    for token in _TOKEN_NOME_OU_VALOR.finditer(texto_normalizado, ancora.end()):
        texto_token = token.group()
        if texto_token[0].isdigit():
            return _parse_valor(texto_token)
        if texto_token not in nome_normalizado and texto_token not in _CONECTORES_NOME:
            return None

    return None


def _valor_se_regra_bater(
    regra, pendencia: PendenciaAuditoria, texto_normalizado: str
) -> Decimal | None:
    if regra.tipo_detalhamento_resultado == TipoDetalhamento.OUTRO and re.search(
        r"\bsem\s+biscoitos?\b", texto_normalizado
    ):
        return None
    if regra.modo_extracao == ModoExtracaoRegra.NOME_NA_LISTA:
        return _valor_por_token_de_nome(pendencia.nome, texto_normalizado)
    return _valor_com_regex(regra, texto_normalizado)


def extrair_detalhamentos(
    pendencia_auditoria: PendenciaAuditoria,
    grupos: list,
    tipo_detalhamento: TipoDetalhamento,
    permite_fallback: bool = True,
) -> list[ItemDetalhamento]:
    """Etapa B (Extração): lê `inscricaoPendente.observacao` e avalia as Regras
    ativas dos grupos aplicáveis, agrupadas por `tipo_detalhamento_resultado`
    — dentro de cada tipo, para na primeira Regra (em ordem) que bater;
    tipos diferentes (ex. Inscrição vs Oferta) são avaliados independentemente
    e podem gerar Detalhamentos ao mesmo tempo. Se nenhum tipo bateu e
    `permite_fallback` é True, cai no fallback: 1 item com o valor total
    pago, vinculado à própria pendência. `permite_fallback` deve vir False
    quando o lançamento já tem outro Detalhamento vinculado (pagamento
    compartilhado entre várias pessoas) — nesse caso `inscricaoPendente.pagamento` é
    só uma referência ao total do grupo, não ao valor real desta pessoa, e
    usá-lo às cegas criaria um Detalhamento errado. Sem regra que consiga
    extrair o valor certo da observação, a função devolve lista vazia e
    nada é criado."""
    obs_normalizado = remover_acentos(pendencia_auditoria.observacao or "").lower()

    regras_por_tipo: dict = {}
    for grupo in grupos:
        for regra in grupo.regras:
            if not regra.ativo:
                continue
            regras_por_tipo.setdefault(regra.tipo_detalhamento_resultado, []).append(
                regra
            )

    itens: list[ItemDetalhamento] = []
    for tipo, regras in regras_por_tipo.items():
        for regra in sorted(regras, key=lambda r: r.ordem):
            valor = _valor_se_regra_bater(regra, pendencia_auditoria, obs_normalizado)
            if valor is None or valor <= 0:
                continue

            referencia_id = pendencia_auditoria.id if tipo in _TIPOS_INSCRICAO else None
            itens.append(
                ItemDetalhamento(tipo=tipo, valor=valor, referencia_id=referencia_id)
            )
            break

    if not itens and permite_fallback:
        itens.append(
            ItemDetalhamento(
                tipo=tipo_detalhamento,
                valor=pendencia_auditoria.pagamento,
                referencia_id=pendencia_auditoria.id,
            )
        )

    return itens


def diagnosticar_detalhamentos(
    pendencia_auditoria: PendenciaAuditoria,
    grupos: list,
) -> list[tuple[Regra, list[ItemDetalhamento]]]:
    """Retorna somente as regras que casaram e os itens que elas gerariam."""
    texto = remover_acentos(pendencia_auditoria.observacao or "").lower()
    regras_por_tipo: dict = {}
    for grupo in grupos:
        for regra in grupo.regras:
            if regra.ativo:
                regras_por_tipo.setdefault(
                    regra.tipo_detalhamento_resultado, []
                ).append(regra)

    resultado = []
    for tipo, regras in regras_por_tipo.items():
        for regra in sorted(regras, key=lambda r: r.ordem):
            valor = _valor_se_regra_bater(regra, pendencia_auditoria, texto)
            if valor is None or valor <= 0:
                continue
            referencia_id = pendencia_auditoria.id if tipo in _TIPOS_INSCRICAO else None
            resultado.append(
                (
                    regra,
                    [
                        ItemDetalhamento(
                            tipo=tipo, valor=valor, referencia_id=referencia_id
                        )
                    ],
                )
            )
            break
    return resultado
