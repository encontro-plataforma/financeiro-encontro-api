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
        {
            "nome": "Inscrição",
            "ordem": 1,
            "ativo": True,
            "tipo_detalhamento_resultado": tipo_inscricao,
            "modo_extracao": ModoExtracaoRegra.TOKEN_VALOR,
            "condicoes": [RegraCondicao(ordem=1, padrao_regex=_PADRAO_INSCRICAO)],
        },
        {
            "nome": "Inscrição (lista compartilhada)",
            "ordem": 2,
            "ativo": True,
            "tipo_detalhamento_resultado": tipo_inscricao,
            "modo_extracao": ModoExtracaoRegra.NOME_NA_LISTA,
            "condicoes": [],
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
                RegraCondicao(ordem=1, padrao_regex=r"pagamento\s+via\D*?(\d+(?:[.,]\d{2})?)"),
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
                    padrao_regex=r"(?:biscoitos?\D*?(\d+(?:[.,]\d{2})?)|(\d+(?:[.,]\d{2})?)\D*?biscoitos?)",
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
    principal de `seed_regras` só cria grupos do zero."""
    nomes_existentes = {regra.nome for regra in grupo.regras}
    adicionou = False

    for item in _regras_padrao(grupo.escopo, tipo_inscricao):
        if item["nome"] in nomes_existentes:
            continue
        grupo.regras.append(Regra(**item))
        adicionou = True

    return adicionou


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
