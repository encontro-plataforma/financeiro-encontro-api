from app.integracao.regras.deteccao_pagamento_multiplo import eh_pagamento_multiplo


def test_reconhece_pagamento_multiplo_simples():
    assert eh_pagamento_multiplo("Pagamento múltiplo, ver planilha") is True


def test_reconhece_case_insensitive():
    assert eh_pagamento_multiplo("PAGAMENTO MULTIPLO") is True


def test_reconhece_sem_acento():
    assert eh_pagamento_multiplo("pagamento multiplo") is True


def test_reconhece_plural():
    assert eh_pagamento_multiplo("Pagamentos múltiplos, dividido em 2 pix") is True


def test_nao_reconhece_texto_nao_relacionado():
    assert eh_pagamento_multiplo("Pix de Fulano de Tal") is False


def test_nao_reconhece_abreviacao():
    assert eh_pagamento_multiplo("pagto multiplo") is False


def test_observacao_none():
    assert eh_pagamento_multiplo(None) is False


def test_observacao_vazia():
    assert eh_pagamento_multiplo("") is False
