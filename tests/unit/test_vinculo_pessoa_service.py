from decimal import Decimal

from app.services.vinculo_pessoa_service import (
    calcular_saldo_pendente,
    excede_saldo_pessoa,
    soma_bate_com_pagamento,
)


def test_soma_igual_ao_pagamento_e_auditado():
    assert soma_bate_com_pagamento(Decimal("100.00"), Decimal("100.00")) is True


def test_soma_dentro_da_tolerancia_e_auditado():
    assert soma_bate_com_pagamento(Decimal("99.99"), Decimal("100.00")) is True


def test_soma_abaixo_da_tolerancia_nao_e_auditado():
    assert soma_bate_com_pagamento(Decimal("99.98"), Decimal("100.00")) is False


def test_soma_maior_que_pagamento_e_auditado():
    assert soma_bate_com_pagamento(Decimal("150.00"), Decimal("100.00")) is True


def test_pagamento_none_nao_e_auditado():
    assert soma_bate_com_pagamento(Decimal("0"), None) is False


def test_saldo_pendente_zero_quando_pago_integralmente():
    assert calcular_saldo_pendente(Decimal("100.00"), Decimal("100.00")) == Decimal("0")


def test_saldo_pendente_positivo_quando_parcial():
    assert calcular_saldo_pendente(Decimal("60.00"), Decimal("100.00")) == Decimal("40.00")


def test_saldo_pendente_zero_quando_soma_ultrapassa_pagamento():
    assert calcular_saldo_pendente(Decimal("120.00"), Decimal("100.00")) == Decimal("0")


def test_saldo_pendente_none_quando_pagamento_none():
    assert calcular_saldo_pendente(Decimal("0"), None) is None


def test_multiplos_vinculos_somam_corretamente_para_pagamento_parcial():
    # Duas parcelas de 40 pra um pagamento esperado de 100 — ainda pendente.
    soma = sum((Decimal("40.00"), Decimal("40.00")), Decimal("0"))
    assert soma_bate_com_pagamento(soma, Decimal("100.00")) is False
    assert calcular_saldo_pendente(soma, Decimal("100.00")) == Decimal("20.00")


def test_multiplos_vinculos_somam_corretamente_para_pagamento_completo():
    # Três parcelas cobrindo exatamente o pagamento esperado.
    soma = sum((Decimal("33.34"), Decimal("33.33"), Decimal("33.33")), Decimal("0"))
    assert soma_bate_com_pagamento(soma, Decimal("100.00")) is True
    assert calcular_saldo_pendente(soma, Decimal("100.00")) == Decimal("0")


def test_excede_saldo_pessoa_quando_soma_ultrapassa_pagamento():
    assert excede_saldo_pessoa(Decimal("60.00"), Decimal("50.00"), Decimal("100.00")) is True


def test_excede_saldo_pessoa_quando_soma_dentro_do_pagamento():
    assert excede_saldo_pessoa(Decimal("60.00"), Decimal("40.00"), Decimal("100.00")) is False


def test_excede_saldo_pessoa_pagamento_none_nunca_excede():
    assert excede_saldo_pessoa(Decimal("1000.00"), Decimal("500.00"), None) is False
