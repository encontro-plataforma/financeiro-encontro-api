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


def _candidato(id, descricao, capacidade_restante, forma_pagamento=FormaPagamento.PIX, valor=None):
    """`valor` (total original do lançamento) por padrão é igual à
    capacidade_restante -- reproduz um lançamento "intocado" (ninguém ainda
    consumiu nada dele), que é o caso da maioria dos testes existentes.
    Passe `valor` explicitamente pra simular um lançamento já parcialmente
    consumido por outra pessoa (valor > capacidade_restante)."""
    capacidade = Decimal(capacidade_restante)
    valor_final = Decimal(valor) if valor is not None else capacidade
    return CandidatoLancamento(
        id=id,
        descricao=descricao,
        valor=valor_final,
        soma_detalhamentos=valor_final - capacidade,
        forma_pagamento=forma_pagamento,
    )


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


def test_sem_observacao_assume_pix_e_casa_com_candidato_pix():
    pendencia = _pendencia(observacao=None)
    candidato = _candidato(1, "PIX JOAO DA SILVA", "100", FormaPagamento.PIX)

    assert selecionar_lancamento(pendencia, [candidato]) is candidato


def test_sem_observacao_assume_pix_e_nao_casa_com_outra_forma():
    pendencia = _pendencia(observacao=None)
    candidato = _candidato(1, "PIX JOAO DA SILVA", "100", FormaPagamento.CARTAO_CREDITO)

    assert selecionar_lancamento(pendencia, [candidato]) is None


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


def test_candidato_parcialmente_consumido_ainda_e_valido():
    # Cenário de inscrição múltipla: lançamento de 180 já tem um Detalhamento
    # de 90 (de outra pessoa), sobrando 90 de capacidade. A pendência ainda
    # registra o pagamento de referência do grupo inteiro (180) -- o match
    # usa o VALOR ORIGINAL do lançamento (180), não a capacidade restante.
    pendencia = _pendencia(nome_pagador="Responsavel", pagamento="180")
    candidato = _candidato(1, "PIX RESPONSAVEL", "90", valor="180")

    assert selecionar_lancamento(pendencia, [candidato]) is candidato


def test_candidato_totalmente_consumido_e_descartado():
    # Mesmo com o valor original batendo, um lançamento sem nenhuma
    # capacidade sobrando (já 100% vinculado a outras pessoas) não pode
    # mais ser escolhido.
    pendencia = _pendencia(nome_pagador="Responsavel", pagamento="180")
    candidato = _candidato(1, "PIX RESPONSAVEL", "0", valor="180")

    assert selecionar_lancamento(pendencia, [candidato]) is None


def test_cartao_de_debito_nao_e_mascarado_pelo_padrao_generico():
    pendencia = _pendencia(observacao="Pagamento feito via cartao de debito de R$ 100,00")
    credito = _candidato(1, "JOAO DA SILVA", "100", FormaPagamento.CARTAO_CREDITO)
    debito = _candidato(2, "JOAO DA SILVA", "100", FormaPagamento.CARTAO_DEBITO)

    assert selecionar_lancamento(pendencia, [credito, debito]) is debito


def test_especie_e_tratado_como_sinonimo_de_dinheiro():
    pendencia = _pendencia(observacao="Pagamento via espécie de R$ 100,00")
    dinheiro = _candidato(1, "JOAO DA SILVA", "100", FormaPagamento.DINHEIRO)
    pix = _candidato(2, "JOAO DA SILVA", "100", FormaPagamento.PIX)

    assert selecionar_lancamento(pendencia, [dinheiro, pix]) is dinheiro
