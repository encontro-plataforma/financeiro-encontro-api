from collections import namedtuple
from decimal import Decimal

from app.services.vinculo_pessoa_service import excede_saldo_pessoa

# Réplica simples de um Detalhamento (id + valor) — evita precisar de DB só
# pra testar a lógica de "somar os outros, excluindo o que está sendo editado",
# que é exatamente o que DetalhamentoService._validar_soma_pessoa faz.
FakeDetalhamento = namedtuple("FakeDetalhamento", ["id", "valor"])


def _soma_outros(detalhamentos, excluir_id=None):
    return sum((d.valor for d in detalhamentos if d.id != excluir_id), Decimal("0"))


def test_soma_dentro_do_pagamento_nao_excede():
    assert excede_saldo_pessoa(Decimal("60.00"), Decimal("30.00"), Decimal("100.00")) is False


def test_soma_ultrapassa_pagamento_excede():
    assert excede_saldo_pessoa(Decimal("60.00"), Decimal("50.00"), Decimal("100.00")) is True


def test_soma_no_limite_exato_da_tolerancia_nao_excede():
    # 90 + 10.01 = 100.01, exatamente pagamento + tolerância (100 + 0.01).
    assert excede_saldo_pessoa(Decimal("90.00"), Decimal("10.01"), Decimal("100.00")) is False


def test_soma_um_centavo_alem_da_tolerancia_excede():
    # 90 + 10.02 = 100.02, um centavo além do limite de 100.01.
    assert excede_saldo_pessoa(Decimal("90.00"), Decimal("10.02"), Decimal("100.00")) is True


def test_edicao_excluindo_o_proprio_detalhamento_do_calculo():
    detalhamentos = [
        FakeDetalhamento(id=1, valor=Decimal("40.00")),
        FakeDetalhamento(id=2, valor=Decimal("50.00")),
    ]
    pagamento = Decimal("100.00")

    # Editando o detalhamento id=2 pra 60: sem excluir o próprio valor do
    # cálculo, a soma dos "outros" ficaria errada (40+50=90, 90+60 excederia).
    # Excluindo-o (excluir_id=2), soma_outros = 40, e 40+60=100 não excede.
    soma_outros = _soma_outros(detalhamentos, excluir_id=2)
    assert soma_outros == Decimal("40.00")
    assert excede_saldo_pessoa(soma_outros, Decimal("60.00"), pagamento) is False


def test_edicao_sem_excluir_saldo_correto_quando_novo_valor_excede():
    detalhamentos = [
        FakeDetalhamento(id=1, valor=Decimal("40.00")),
        FakeDetalhamento(id=2, valor=Decimal("50.00")),
    ]
    pagamento = Decimal("100.00")

    soma_outros = _soma_outros(detalhamentos, excluir_id=2)
    assert excede_saldo_pessoa(soma_outros, Decimal("65.00"), pagamento) is True


def test_pagamento_none_nunca_bloqueia_criacao_de_detalhamento():
    assert excede_saldo_pessoa(Decimal("500.00"), Decimal("500.00"), None) is False
