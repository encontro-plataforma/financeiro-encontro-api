from sqlalchemy.orm import Session

from app.models.regra_grupo import RegraGrupo
from app.models.regra import Regra
from app.models.regra_condicao import RegraCondicao
from app.models.enums import EscopoRegraGrupo, TipoDetalhamento

# Um grupo por escopo (nome sempre igual ao escopo — não faz sentido ter
# dois grupos com o mesmo escopo). Cada grupo é avaliado só quando faz
# sentido para o que está sendo processado:
#   - EXTRACAO_ENCONTREIRO / EXTRACAO_ENCONTRISTA: só quando a pendência
#     sendo auditada é do tipo correspondente (acha a inscrição da própria
#     pessoa na observação).
#   - OFERTAS: avaliado sempre, independente do tipo de pendência (não
#     duplicado dentro dos grupos de inscrição).
# Se nenhuma regra do(s) grupo(s) aplicável(is) casar, o motor cai no
# fallback padrão (1 Detalhamento com o valor total pago).
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
        "regra_nome": "Inscrição",
        "tipo_detalhamento_resultado": TipoDetalhamento.INSCRICAO_ENCONTREIRO,
        "padrao_regex": _PADRAO_INSCRICAO,
    },
    {
        "escopo": EscopoRegraGrupo.EXTRACAO_ENCONTRISTA,
        "ordem": 10,
        "regra_nome": "Inscrição",
        "tipo_detalhamento_resultado": TipoDetalhamento.INSCRICAO_ENCONTRISTA,
        "padrao_regex": _PADRAO_INSCRICAO,
    },
    {
        "escopo": EscopoRegraGrupo.OFERTAS,
        "ordem": 20,
        "regra_nome": "Oferta",
        "tipo_detalhamento_resultado": TipoDetalhamento.OFERTA,
        "padrao_regex": _PADRAO_OFERTA,
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
                regras=[
                    Regra(
                        nome=item["regra_nome"],
                        ordem=1,
                        ativo=True,
                        tipo_detalhamento_resultado=item["tipo_detalhamento_resultado"],
                        condicoes=[RegraCondicao(ordem=1, padrao_regex=item["padrao_regex"])],
                    ),
                ],
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
