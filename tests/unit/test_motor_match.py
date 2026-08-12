from datetime import date
from decimal import Decimal

from app.integracao.regras.dtos import CandidatoLancamento, PendenciaAuditoria
from app.integracao.regras.motor_match import selecionar_lancamento
from app.models.enums import FormaPagamento


def _pendencia(nome_pagador="Joao da Silva", pagamento="100", observacao=None):
    return PendenciaAuditoria(
        id=1,
        nome="Joao da Silva",
        nome_pagador=nome_pagador,
        dt_pagamento=date(2026, 1, 1),
        pagamento=Decimal(pagamento),
        observacao=observacao,
    )


def _candidato(id, descricao, capacidade_restante, forma_pagamento=FormaPagamento.PIX):
    return CandidatoLancamento(id=id, descricao=descricao, capacidade_restante=Decimal(capacidade_restante), forma_pagamento=forma_pagamento)


def test_unico_candidato_valido_casa():
    pendencia = _pendencia()
    candidato = _candidato(10, "PIX JOAO DA SILVA", "100")

    assert selecionar_lancamento(pendencia, [candidato]) is candidato


def test_nome_bate_so_em_um_dos_candidatos():
    pendencia = _pendencia()
    certo = _candidato(1, "PIX JOAO DA SILVA", "100")
    errado = _candidato(2, "PIX MARIA OLIVEIRA", "100")

    assert selecionar_lancamento(pendencia, [errado, certo]) is certo


def test_nome_nao_bate_em_nenhum_candidato():
    pendencia = _pendencia()
    candidatos = [
        _candidato(1, "PIX MARIA OLIVEIRA", "100"),
        _candidato(2, "PIX PEDRO SOUZA", "100"),
    ]

    assert selecionar_lancamento(pendencia, candidatos) is None


def test_capacidade_insuficiente_descarta_candidato():
    pendencia = _pendencia(pagamento="100")
    candidato = _candidato(1, "PIX JOAO DA SILVA", "50")

    assert selecionar_lancamento(pendencia, [candidato]) is None


def test_empate_pega_o_de_menor_id():
    pendencia = _pendencia()
    mais_novo = _candidato(7, "PIX JOAO DA SILVA", "100")
    mais_antigo = _candidato(3, "pix joao da silva", "150")

    escolhido = selecionar_lancamento(pendencia, [mais_novo, mais_antigo])

    assert escolhido is mais_antigo


def test_sem_nome_pagador_nunca_casa():
    pendencia = _pendencia(nome_pagador=None)
    candidato = _candidato(1, "PIX QUALQUER COISA", "1000")

    assert selecionar_lancamento(pendencia, [candidato]) is None


def test_sem_candidatos_nao_casa():
    pendencia = _pendencia()

    assert selecionar_lancamento(pendencia, []) is None


def test_sem_observacao_nao_filtra_por_forma_pagamento():
    # comportamento atual preservado quando a observação não menciona nada
    pendencia = _pendencia(observacao=None)
    candidato = _candidato(1, "PIX JOAO DA SILVA", "100", FormaPagamento.CARTAO_CREDITO)

    assert selecionar_lancamento(pendencia, [candidato]) is candidato


def test_unico_candidato_com_forma_errada_nao_casa():
    pendencia = _pendencia(observacao="Pagamento feito via pix de R$ 100,00")
    candidato = _candidato(1, "PIX JOAO DA SILVA", "100", FormaPagamento.CARTAO_CREDITO)

    assert selecionar_lancamento(pendencia, [candidato]) is None


def test_forma_pagamento_filtra_entre_varios_candidatos():
    pendencia = _pendencia(observacao="Pagamento feito via cartao de credito de R$ 100,00")
    pix = _candidato(1, "JOAO DA SILVA", "100", FormaPagamento.PIX)
    cartao = _candidato(2, "JOAO DA SILVA", "100", FormaPagamento.CARTAO_CREDITO)

    # pix tem o menor id, mas a forma de pagamento tem prioridade sobre o desempate
    escolhido = selecionar_lancamento(pendencia, [pix, cartao])

    assert escolhido is cartao


def test_cartao_sozinho_equivale_a_credito():
    pendencia = _pendencia(observacao="Pagamento feito via cartao de R$ 100,00")
    debito = _candidato(1, "JOAO DA SILVA", "100", FormaPagamento.CARTAO_DEBITO)
    credito = _candidato(2, "JOAO DA SILVA", "100", FormaPagamento.CARTAO_CREDITO)

    assert selecionar_lancamento(pendencia, [debito, credito]) is credito


def test_cartao_de_debito_nao_e_mascarado_pelo_padrao_generico():
    pendencia = _pendencia(observacao="Pagamento feito via cartao de debito de R$ 100,00")
    credito = _candidato(1, "JOAO DA SILVA", "100", FormaPagamento.CARTAO_CREDITO)
    debito = _candidato(2, "JOAO DA SILVA", "100", FormaPagamento.CARTAO_DEBITO)

    assert selecionar_lancamento(pendencia, [credito, debito]) is debito
