from datetime import date
from decimal import Decimal

from app.database.seeds.seed_regras import _PADRAO_INSCRICAO, _PADRAO_OFERTA
from app.integracao.regras.dtos import PendenciaAuditoria
from app.integracao.regras.motor_extracao import extrair_detalhamentos
from app.models.enums import TipoDetalhamento
from app.models.regra import Regra
from app.models.regra_condicao import RegraCondicao
from app.models.regra_grupo import RegraGrupo


def _pendencia(pagamento="100", observacao=None, pessoa_id=1):
    return PendenciaAuditoria(
        id=pessoa_id,
        nome_pagador="Joao da Silva",
        dt_pagamento=date(2026, 1, 1),
        pagamento=Decimal(pagamento),
        observacao=observacao,
    )


def _grupo_inscricao_encontreiro(ativo=True):
    return RegraGrupo(
        nome="EXTRACAO_ENCONTREIRO", escopo="EXTRACAO_ENCONTREIRO", ordem=10, ativo=True,
        regras=[
            Regra(
                nome="Inscrição", ordem=1, ativo=ativo,
                tipo_detalhamento_resultado=TipoDetalhamento.INSCRICAO_ENCONTREIRO,
                condicoes=[RegraCondicao(ordem=1, padrao_regex=_PADRAO_INSCRICAO)],
            ),
        ],
    )


def _grupo_ofertas():
    return RegraGrupo(
        nome="OFERTAS", escopo="OFERTAS", ordem=20, ativo=True,
        regras=[
            Regra(
                nome="Oferta", ordem=1, ativo=True,
                tipo_detalhamento_resultado=TipoDetalhamento.OFERTA,
                condicoes=[RegraCondicao(ordem=1, padrao_regex=_PADRAO_OFERTA)],
            ),
        ],
    )


def test_token_antes_do_valor_gera_dois_itens():
    pendencia = _pendencia(observacao="Pago em pix a inscricao 90 e 10 de oferta")
    grupos = [_grupo_inscricao_encontreiro(), _grupo_ofertas()]

    itens = extrair_detalhamentos(pendencia, grupos, TipoDetalhamento.INSCRICAO_ENCONTREIRO)

    assert len(itens) == 2
    inscricao = next(i for i in itens if i.tipo == TipoDetalhamento.INSCRICAO_ENCONTREIRO)
    oferta = next(i for i in itens if i.tipo == TipoDetalhamento.OFERTA)
    assert inscricao.valor == Decimal("90")
    assert inscricao.referencia_id == pendencia.id
    assert oferta.valor == Decimal("10")
    assert oferta.referencia_id is None


def test_valor_antes_do_token_tambem_casa():
    # ordem invertida ("token ... valor"), e valor com casas decimais
    pendencia = _pendencia(observacao="Inscricao paga em pix por 90,00 reais")
    grupos = [_grupo_inscricao_encontreiro(), _grupo_ofertas()]

    itens = extrair_detalhamentos(pendencia, grupos, TipoDetalhamento.INSCRICAO_ENCONTREIRO)

    assert len(itens) == 1
    assert itens[0].tipo == TipoDetalhamento.INSCRICAO_ENCONTREIRO
    assert itens[0].valor == Decimal("90.00")


def test_apenas_oferta_com_valor_apos_o_token():
    pendencia = _pendencia(pagamento="15", observacao="Oferta paga em pix no valor de 15 reais")
    grupos = [_grupo_inscricao_encontreiro(), _grupo_ofertas()]

    itens = extrair_detalhamentos(pendencia, grupos, TipoDetalhamento.INSCRICAO_ENCONTREIRO)

    assert len(itens) == 1
    assert itens[0].tipo == TipoDetalhamento.OFERTA
    assert itens[0].valor == Decimal("15")
    assert itens[0].referencia_id is None


def test_sem_observacao_cai_no_fallback():
    pendencia = _pendencia(pagamento="150", observacao=None)
    grupos = [_grupo_inscricao_encontreiro(), _grupo_ofertas()]

    itens = extrair_detalhamentos(pendencia, grupos, TipoDetalhamento.INSCRICAO_ENCONTREIRO)

    assert len(itens) == 1
    assert itens[0].tipo == TipoDetalhamento.INSCRICAO_ENCONTREIRO
    assert itens[0].valor == Decimal("150")
    assert itens[0].referencia_id == pendencia.id


def test_observacao_sem_padrao_reconhecido_cai_no_fallback():
    pendencia = _pendencia(pagamento="80", observacao="Pagamento via pix, obrigado!")
    grupos = [_grupo_inscricao_encontreiro(), _grupo_ofertas()]

    itens = extrair_detalhamentos(pendencia, grupos, TipoDetalhamento.INSCRICAO_ENCONTREIRO)

    assert len(itens) == 1
    assert itens[0].valor == Decimal("80")


def test_regra_inativa_e_ignorada():
    pendencia = _pendencia(pagamento="90", observacao="Pago em pix a inscricao 90")
    grupos = [_grupo_inscricao_encontreiro(ativo=False)]

    itens = extrair_detalhamentos(pendencia, grupos, TipoDetalhamento.INSCRICAO_ENCONTREIRO)

    # regra desativada não casa -> cai no fallback (não vira 0 itens)
    assert len(itens) == 1
    assert itens[0].valor == Decimal("90")
