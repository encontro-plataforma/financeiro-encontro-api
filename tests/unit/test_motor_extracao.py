from datetime import date
from decimal import Decimal

from app.database.seeds.seed_regras import _PADRAO_INSCRICAO, _PADRAO_OFERTA
from app.integracao.regras.dtos import PendenciaAuditoria
from app.integracao.regras.motor_extracao import extrair_detalhamentos
from app.models.enums import ModoExtracaoRegra, TipoDetalhamento
from app.models.regra import Regra
from app.models.regra_condicao import RegraCondicao
from app.models.regra_grupo import RegraGrupo


def _pendencia(pagamento="100", observacao=None, pessoa_id=1, nome="Joao da Silva"):
    return PendenciaAuditoria(
        id=pessoa_id,
        nome=nome,
        nome_pagador="Joao da Silva",
        dt_pagamento=date(2026, 1, 1),
        pagamento=Decimal(pagamento),
        observacao=observacao,
    )


def _grupo_inscricao_encontreiro(inscricao_ativa=True, com_lista_compartilhada=True):
    regras = [
        Regra(
            nome="Inscrição", ordem=1, ativo=inscricao_ativa,
            tipo_detalhamento_resultado=TipoDetalhamento.INSCRICAO_ENCONTREIRO,
            modo_extracao=ModoExtracaoRegra.TOKEN_VALOR,
            condicoes=[RegraCondicao(ordem=1, padrao_regex=_PADRAO_INSCRICAO)],
        ),
        Regra(
            nome="Oferta", ordem=3, ativo=True,
            tipo_detalhamento_resultado=TipoDetalhamento.OFERTA,
            modo_extracao=ModoExtracaoRegra.TOKEN_VALOR,
            condicoes=[RegraCondicao(ordem=1, padrao_regex=_PADRAO_OFERTA)],
        ),
    ]
    if com_lista_compartilhada:
        regras.insert(1, Regra(
            nome="Inscrição (lista compartilhada)", ordem=2, ativo=True,
            tipo_detalhamento_resultado=TipoDetalhamento.INSCRICAO_ENCONTREIRO,
            modo_extracao=ModoExtracaoRegra.NOME_NA_LISTA,
            condicoes=[],
        ))

    return RegraGrupo(
        nome="EXTRACAO_ENCONTREIRO", escopo="EXTRACAO_ENCONTREIRO", ordem=10, ativo=True,
        regras=regras,
    )


def test_token_antes_do_valor_gera_dois_itens():
    pendencia = _pendencia(observacao="Pago em pix a inscricao 90 e 10 de oferta")
    grupos = [_grupo_inscricao_encontreiro()]

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
    grupos = [_grupo_inscricao_encontreiro()]

    itens = extrair_detalhamentos(pendencia, grupos, TipoDetalhamento.INSCRICAO_ENCONTREIRO)

    assert len(itens) == 1
    assert itens[0].tipo == TipoDetalhamento.INSCRICAO_ENCONTREIRO
    assert itens[0].valor == Decimal("90.00")


def test_apenas_oferta_com_valor_apos_o_token():
    pendencia = _pendencia(pagamento="15", observacao="Oferta paga em pix no valor de 15 reais")
    grupos = [_grupo_inscricao_encontreiro()]

    itens = extrair_detalhamentos(pendencia, grupos, TipoDetalhamento.INSCRICAO_ENCONTREIRO)

    assert len(itens) == 1
    assert itens[0].tipo == TipoDetalhamento.OFERTA
    assert itens[0].valor == Decimal("15")
    assert itens[0].referencia_id is None


def test_sem_observacao_cai_no_fallback():
    pendencia = _pendencia(pagamento="150", observacao=None)
    grupos = [_grupo_inscricao_encontreiro()]

    itens = extrair_detalhamentos(pendencia, grupos, TipoDetalhamento.INSCRICAO_ENCONTREIRO)

    assert len(itens) == 1
    assert itens[0].tipo == TipoDetalhamento.INSCRICAO_ENCONTREIRO
    assert itens[0].valor == Decimal("150")
    assert itens[0].referencia_id == pendencia.id


def test_observacao_sem_padrao_reconhecido_cai_no_fallback():
    pendencia = _pendencia(pagamento="80", observacao="Pagamento via pix, obrigado!")
    grupos = [_grupo_inscricao_encontreiro()]

    itens = extrair_detalhamentos(pendencia, grupos, TipoDetalhamento.INSCRICAO_ENCONTREIRO)

    assert len(itens) == 1
    assert itens[0].valor == Decimal("80")


def test_regra_inativa_e_ignorada():
    pendencia = _pendencia(pagamento="90", observacao="Pago em pix a inscricao 90")
    grupos = [_grupo_inscricao_encontreiro(inscricao_ativa=False, com_lista_compartilhada=False)]

    itens = extrair_detalhamentos(pendencia, grupos, TipoDetalhamento.INSCRICAO_ENCONTREIRO)

    # regra desativada não casa -> cai no fallback (não vira 0 itens)
    assert len(itens) == 1
    assert itens[0].valor == Decimal("90")


def test_nome_na_lista_acha_valor_de_cada_pessoa():
    observacao = (
        "Pagamento feito via pix de R$300,00 para Luiza Rochelle de 100 reais, "
        "Samuel Augusto de 100 reais e Giovanna Alves de 100 reais"
    )
    grupos = [_grupo_inscricao_encontreiro()]

    luiza = _pendencia(pessoa_id=1, nome="Luiza Rochelle", observacao=observacao)
    samuel = _pendencia(pessoa_id=2, nome="Samuel Augusto", observacao=observacao)
    giovanna = _pendencia(pessoa_id=3, nome="Giovanna Alves", observacao=observacao)

    for pendencia in (luiza, samuel, giovanna):
        itens = extrair_detalhamentos(pendencia, grupos, TipoDetalhamento.INSCRICAO_ENCONTREIRO)
        assert len(itens) == 1
        assert itens[0].tipo == TipoDetalhamento.INSCRICAO_ENCONTREIRO
        assert itens[0].valor == Decimal("100")
        assert itens[0].referencia_id == pendencia.id


def test_nome_na_lista_aceita_so_o_primeiro_nome():
    observacao = "Pagamento via pix de R$200,00 para Samuel de 100 reais e Giovanna de 100 reais"
    grupos = [_grupo_inscricao_encontreiro()]

    # cadastro tem o nome completo, mas a observação só cita o primeiro nome
    pendencia = _pendencia(nome="Samuel Augusto", observacao=observacao)

    itens = extrair_detalhamentos(pendencia, grupos, TipoDetalhamento.INSCRICAO_ENCONTREIRO)

    assert len(itens) == 1
    assert itens[0].valor == Decimal("100")


def test_nome_na_lista_nao_bate_cai_no_fallback():
    pendencia = _pendencia(pagamento="70", nome="Alguem Ausente", observacao="Pagamento via pix de R$70,00")
    grupos = [_grupo_inscricao_encontreiro()]

    itens = extrair_detalhamentos(pendencia, grupos, TipoDetalhamento.INSCRICAO_ENCONTREIRO)

    assert len(itens) == 1
    assert itens[0].valor == Decimal("70")


def test_permite_fallback_false_sem_padrao_reconhecido_nao_cria_nada():
    # Cenário de inscrição múltipla: o lançamento já tem outro Detalhamento
    # (permite_fallback=False), e a observação não menciona esta pessoa --
    # não deve inventar um Detalhamento usando o pagamento de referência
    # (que aqui representaria o total do grupo, não o valor real dela).
    pendencia = _pendencia(pagamento="180", nome="Alguem Ausente", observacao="Pagamento via pix de 180 reais")
    grupos = [_grupo_inscricao_encontreiro()]

    itens = extrair_detalhamentos(
        pendencia, grupos, TipoDetalhamento.INSCRICAO_ENCONTREIRO, permite_fallback=False,
    )

    assert itens == []


def test_permite_fallback_false_nao_afeta_regra_que_bate():
    # Quando a regra realmente encontra o valor da pessoa na observação,
    # permite_fallback=False não muda nada -- o fallback nunca chega a ser
    # avaliado.
    observacao = (
        "Pagamento via pix de 180 para Kaua Victor dos Santos Silva de 90 reais "
        "e Schynaider Sthephane Araujo da Silva Santos de 90 reais"
    )
    grupos = [_grupo_inscricao_encontreiro()]
    pendencia = _pendencia(pagamento="180", nome="Schynaider Sthephane Araujo da Silva Santos", observacao=observacao)

    itens = extrair_detalhamentos(
        pendencia, grupos, TipoDetalhamento.INSCRICAO_ENCONTREIRO, permite_fallback=False,
    )

    assert len(itens) == 1
    assert itens[0].valor == Decimal("90")
    assert itens[0].referencia_id == pendencia.id


def test_duas_regras_do_mesmo_tipo_so_a_primeira_em_ordem_conta():
    grupo = RegraGrupo(
        nome="EXTRACAO_ENCONTREIRO", escopo="EXTRACAO_ENCONTREIRO", ordem=10, ativo=True,
        regras=[
            Regra(
                nome="Inscrição A", ordem=1, ativo=True,
                tipo_detalhamento_resultado=TipoDetalhamento.INSCRICAO_ENCONTREIRO,
                modo_extracao=ModoExtracaoRegra.TOKEN_VALOR,
                condicoes=[RegraCondicao(ordem=1, padrao_regex=_PADRAO_INSCRICAO)],
            ),
            Regra(
                nome="Inscrição B", ordem=2, ativo=True,
                tipo_detalhamento_resultado=TipoDetalhamento.INSCRICAO_ENCONTREIRO,
                modo_extracao=ModoExtracaoRegra.NOME_NA_LISTA,
                condicoes=[],
            ),
        ],
    )
    # a regra A (token "inscricao") capturaria 90; a regra B (nome "Joao")
    # capturaria 50 se fosse avaliada — só a de ordem menor (A) deve valer.
    pendencia = _pendencia(pagamento="90", nome="Joao", observacao="Joao 50 reais, pagamento de 90 de inscricao")

    itens = extrair_detalhamentos(pendencia, [grupo], TipoDetalhamento.INSCRICAO_ENCONTREIRO)

    assert len(itens) == 1
    assert itens[0].valor == Decimal("90")
