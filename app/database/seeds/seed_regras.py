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


def _regras_padrao(tipo_inscricao: TipoDetalhamento) -> list[dict]:
    return [
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
        {
            "nome": "Oferta",
            "ordem": 3,
            "ativo": True,
            "tipo_detalhamento_resultado": TipoDetalhamento.OFERTA,
            "modo_extracao": ModoExtracaoRegra.TOKEN_VALOR,
            "condicoes": [RegraCondicao(ordem=1, padrao_regex=_PADRAO_OFERTA)],
        },
    ]


def seed_regras(db: Session):
    try:
        inserted = False

        for item in DEFAULT_GRUPOS:
            existente = db.query(RegraGrupo).filter(RegraGrupo.escopo == item["escopo"]).first()

            if existente:
                continue

            grupo = RegraGrupo(
                nome=item["escopo"].value,
                descricao="Lê a observação da pendência em busca de valores a detalhar.",
                escopo=item["escopo"],
                ordem=item["ordem"],
                ativo=True,
                regras=[Regra(**r) for r in _regras_padrao(item["tipo_inscricao"])],
            )
            db.add(grupo)
            inserted = True

        if inserted:
            db.commit()
        else:
            db.rollback()

    except Exception:
        db.rollback()
        raise
