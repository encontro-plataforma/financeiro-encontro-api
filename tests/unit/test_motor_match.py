from datetime import date
from decimal import Decimal

from app.integracao.regras.dtos import CandidatoLancamento, PendenciaAuditoria
from app.integracao.regras.motor_match import selecionar_lancamento


def _pendencia(nome_pagador="Joao da Silva", pagamento="100"):
    return PendenciaAuditoria(
        id=1,
        nome_pagador=nome_pagador,
        dt_pagamento=date(2026, 1, 1),
        pagamento=Decimal(pagamento),
        observacao=None,
    )


def test_unico_candidato_valido_casa():
    pendencia = _pendencia()
    candidato = CandidatoLancamento(id=10, descricao="PIX JOAO DA SILVA", capacidade_restante=Decimal("100"))

    assert selecionar_lancamento(pendencia, [candidato]) is candidato


def test_nome_bate_so_em_um_dos_candidatos():
    pendencia = _pendencia()
    certo = CandidatoLancamento(id=1, descricao="PIX JOAO DA SILVA", capacidade_restante=Decimal("100"))
    errado = CandidatoLancamento(id=2, descricao="PIX MARIA OLIVEIRA", capacidade_restante=Decimal("100"))

    assert selecionar_lancamento(pendencia, [errado, certo]) is certo


def test_nome_nao_bate_em_nenhum_candidato():
    pendencia = _pendencia()
    candidatos = [
        CandidatoLancamento(id=1, descricao="PIX MARIA OLIVEIRA", capacidade_restante=Decimal("100")),
        CandidatoLancamento(id=2, descricao="PIX PEDRO SOUZA", capacidade_restante=Decimal("100")),
    ]

    assert selecionar_lancamento(pendencia, candidatos) is None


def test_capacidade_insuficiente_descarta_candidato():
    pendencia = _pendencia(pagamento="100")
    candidato = CandidatoLancamento(id=1, descricao="PIX JOAO DA SILVA", capacidade_restante=Decimal("50"))

    assert selecionar_lancamento(pendencia, [candidato]) is None


def test_empate_pega_o_de_menor_id():
    pendencia = _pendencia()
    mais_novo = CandidatoLancamento(id=7, descricao="PIX JOAO DA SILVA", capacidade_restante=Decimal("100"))
    mais_antigo = CandidatoLancamento(id=3, descricao="pix joao da silva", capacidade_restante=Decimal("150"))

    escolhido = selecionar_lancamento(pendencia, [mais_novo, mais_antigo])

    assert escolhido is mais_antigo


def test_sem_nome_pagador_nunca_casa():
    pendencia = _pendencia(nome_pagador=None)
    candidato = CandidatoLancamento(id=1, descricao="PIX QUALQUER COISA", capacidade_restante=Decimal("1000"))

    assert selecionar_lancamento(pendencia, [candidato]) is None


def test_sem_candidatos_nao_casa():
    pendencia = _pendencia()

    assert selecionar_lancamento(pendencia, []) is None
