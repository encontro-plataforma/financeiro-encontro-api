from sqlalchemy.orm import Session

from app.models.regra_grupo import RegraGrupo
from app.models.regra import Regra
from app.models.regra_condicao import RegraCondicao
from app.models.enums import EscopoRegraGrupo, ModoExtracaoRegra, TipoDetalhamento

# Um grupo por escopo (nome sempre igual ao escopo — não faz sentido ter
# dois grupos com o mesmo escopo). Cada grupo (EXTRACAO_ENCONTREIRO /
# EXTRACAO_ENCONTRISTA) carrega, ele mesmo, tanto a(s) Regra(s) de Inscrição
# quanto a de Oferta — não existe mais um RegraGrupo "OFERTAS" separado.
# "Parar no primeiro match" vale por `tipo_detalhamento_resultado`: a Regra
# de Inscrição e a de Oferta têm tipos diferentes, então são avaliadas
# independentemente (podem gerar 2 Detalhamentos a partir da mesma
# observação, ex.: "90 de inscrição e 10 de oferta").
#
# O motor normaliza a observação (remove acento, minúsculo) antes de aplicar
# os padrões — por isso os regex abaixo são escritos sem acento. O valor pode
# aparecer antes ou depois do token (ex.: "inscrição 90" ou "90,00 de
# inscrição"), por isso cada padrão tenta as duas ordens.
_PADRAO_INSCRICAO = r"(?:inscricao\D*?(\d+(?:[.,]\d{2})?)|(\d+(?:[.,]\d{2})?)\D*?inscricao)"
_PADRAO_OFERTA = r"(?:oferta\D*?(\d+(?:[.,]\d{2})?)|(\d+(?:[.,]\d{2})?)\D*?oferta)"

DEFAULT_GRUPOS = [
    {
        "escopo": EscopoRegraGrupo.EXTRACAO_ENCONTREIRO,
        "ordem": 10,
        "tipo_inscricao": TipoDetalhamento.INSCRICAO_ENCONTREIRO,
    },
    {
        "escopo": EscopoRegraGrupo.EXTRACAO_ENCONTRISTA,
        "ordem": 10,
        "tipo_inscricao": TipoDetalhamento.INSCRICAO_ENCONTRISTA,
    },
]


def _regras_padrao(escopo: EscopoRegraGrupo, tipo_inscricao: TipoDetalhamento) -> list[dict]:
    regras = [
        # "Lista compartilhada" vem antes da genérica "Inscrição": ela só
        # produz valor quando o nome da própria pessoa aparece de fato perto
        # de um valor no texto, então é sempre a mais precisa quando bate.
        # Colocá-la depois faria a genérica (que só exige a palavra
        # "inscricao" perto de um número, sem checar nome nenhum) sequestrar
        # o match de observações com múltiplas inscrições nomeadas -- toda
        # pessoa da lista receberia o mesmo primeiro valor encontrado, esteja
        # ou não o nome dela na observação.
        {
            "nome": "Inscrição (lista compartilhada)",
            "ordem": 1,
            "ativo": True,
            "tipo_detalhamento_resultado": tipo_inscricao,
            "modo_extracao": ModoExtracaoRegra.NOME_NA_LISTA,
            "condicoes": [],
        },
        {
            "nome": "Inscrição",
            "ordem": 2,
            "ativo": True,
            "tipo_detalhamento_resultado": tipo_inscricao,
            "modo_extracao": ModoExtracaoRegra.TOKEN_VALOR,
            "condicoes": [RegraCondicao(ordem=1, padrao_regex=_PADRAO_INSCRICAO)],
        },
    ]

    if escopo == EscopoRegraGrupo.EXTRACAO_ENCONTRISTA:
        # Encontrista pode pagar biscoitos junto da inscrição. A observação
        # sempre precisa trazer explicitamente o valor da inscrição (via
        # "pagamento via <forma> de <valor>") — Oferta e Biscoitos nunca
        # aparecem sozinhos na observação; se aparecerem sem esse valor, a
        # observação está incompleta e nada deve ser criado.
        regras.append({
            "nome": "Inscrição (valor no pagamento)",
            "ordem": 3,
            "ativo": True,
            "tipo_detalhamento_resultado": tipo_inscricao,
            "modo_extracao": ModoExtracaoRegra.TOKEN_VALOR,
            "condicoes": [
                # Exige o "de" literal antes do valor (o \D*? antigo parava no
                # primeiro dígito depois de "via", que podia ser o número de
                # parcelas -- ex.: "via cartao de credito em 3 parcelas de R$
                # 160,00" capturava "3" em vez de "160,00"). Usar ".*?" (que
                # também pula dígitos) até um "de" respeita a semântica real
                # da regra -- "o valor vem logo depois de um 'de'" -- e o
                # "de" de "cartao de credito" é automaticamente descartado
                # porque não é seguido de um valor, forçando a busca a
                # continuar até o "de" que precede o valor de fato.
                RegraCondicao(
                    ordem=1,
                    padrao_regex=r"pagamento\s+via.*?de\s*r?\$?\s*(\d+(?:[.,]\d{2})?)",
                ),
            ],
        })

    regras.append({
        "nome": "Oferta",
        "ordem": 4,
        "ativo": True,
        "tipo_detalhamento_resultado": TipoDetalhamento.OFERTA,
        "modo_extracao": ModoExtracaoRegra.TOKEN_VALOR,
        "condicoes": [RegraCondicao(ordem=1, padrao_regex=_PADRAO_OFERTA)],
    })

    if escopo == EscopoRegraGrupo.EXTRACAO_ENCONTRISTA:
        # "de X pacotes"/"pct" -> entrega física, não é cobrança (não gera
        # Detalhamento). Um valor em reais perto de "biscoito" só conta se a
        # observação também trouxer o valor da inscrição (3ª condição) —
        # biscoito nunca aparece sozinho.
        regras.append({
            "nome": "Biscoitos",
            "ordem": 5,
            "ativo": True,
            "tipo_detalhamento_resultado": TipoDetalhamento.OUTRO,
            "modo_extracao": ModoExtracaoRegra.TOKEN_VALOR,
            "condicoes": [
                RegraCondicao(
                    ordem=1,
                    # [^\d/] em vez de \D: sem isso, "R$ 80,00 / Biscoitos: R$ 20,00"
                    # deixava o ramo "valor antes de biscoito" pular por cima da
                    # barra e capturar o valor da inscrição (80,00) em vez do
                    # valor que está de fato ao lado de "biscoito" (20,00) — a
                    # barra e outro dígito não colidem, então continuam servindo
                    # de fronteira entre campos distintos da observação.
                    padrao_regex=r"(?:biscoitos?[^\d/]*?(\d+(?:[.,]\d{2})?)|(\d+(?:[.,]\d{2})?)[^\d/]*?biscoitos?)",
                ),
                RegraCondicao(ordem=2, padrao_regex=r"(?s)^(?:(?!pacotes?|pct\b).)*$"),
                RegraCondicao(ordem=3, padrao_regex=r"pagamento\s+via\D*?\d+(?:[.,]\d{2})?"),
            ],
        })

    return regras


def _adicionar_regras_faltantes(db: Session, grupo: RegraGrupo, tipo_inscricao: TipoDetalhamento) -> bool:
    """Completa um RegraGrupo já existente com as regras padrão (por nome)
    que ele ainda não tem — permite entregar novas regras padrão (ex.:
    Biscoitos) sem precisar de uma migration de dados, já que o laço
    principal de `seed_regras` só cria grupos do zero. Também resincroniza a
    `ordem` das regras padrão já existentes (por nome) com o valor atual de
    `_regras_padrao` — necessário para correções de prioridade entre regras
    (ex.: "lista compartilhada" precisar rodar antes da "Inscrição" genérica)
    alcançarem ambientes que já tinham sido seedados com a ordem antiga."""
    regras_existentes = {regra.nome: regra for regra in grupo.regras}
    alterou = False

    for item in _regras_padrao(grupo.escopo, tipo_inscricao):
        existente = regras_existentes.get(item["nome"])
        if existente is None:
            grupo.regras.append(Regra(**item))
            alterou = True
            continue
        if existente.ordem != item["ordem"]:
            existente.ordem = item["ordem"]
            alterou = True

    return alterou


def seed_regras(db: Session):
    try:
        alterou = False

        for item in DEFAULT_GRUPOS:
            existente = db.query(RegraGrupo).filter(RegraGrupo.escopo == item["escopo"]).first()

            if existente:
                if _adicionar_regras_faltantes(db, existente, item["tipo_inscricao"]):
                    alterou = True
                continue

            grupo = RegraGrupo(
                nome=item["escopo"].value,
                descricao="Lê a observação da pendência em busca de valores a detalhar.",
                escopo=item["escopo"],
                ordem=item["ordem"],
                ativo=True,
                regras=[Regra(**r) for r in _regras_padrao(item["escopo"], item["tipo_inscricao"])],
            )
            db.add(grupo)
            alterou = True

        if alterou:
            db.commit()
        else:
            db.rollback()

    except Exception:
        db.rollback()
        raise
