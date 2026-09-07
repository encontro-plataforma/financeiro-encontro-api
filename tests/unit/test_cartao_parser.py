from collections import Counter
from decimal import Decimal
from pathlib import Path

from app.integracao.conciliacao.parsers.cartao_parser import CartaoParser
from app.services.cartao_service import _montar_observacao

_CSV_CARTOES = (
    Path(__file__).resolve().parents[2] / "07-01 ATE 09-01 - PAG_BANK - CARTOES.csv"
)


def test_parseia_export_pagbank_fornecido():
    parser = CartaoParser()
    linhas = parser.parse(_CSV_CARTOES.read_text(encoding="utf-8"))

    assert len(linhas) == 33
    assert parser.erros == []
    assert parser.ignoradas == []
    assert len({linha.codigo_transacao for linha in linhas}) == 33
    assert Counter(linha.forma_pagamento.value for linha in linhas) == {
        "CARTAO_CREDITO": 28,
        "CARTAO_DEBITO": 5,
    }
    assert sum(linha.valor_bruto for linha in linhas) == Decimal("4070.00")
    assert sum(linha.valor_taxa for linha in linhas) == Decimal("206.16")
    assert sum(linha.valor_liquido for linha in linhas) == Decimal("3863.84")


def test_parseia_bom_utf8_do_export_pagbank():
    conteudo = _CSV_CARTOES.read_text(encoding="utf-8")

    linhas = CartaoParser().parse(conteudo)

    assert len(linhas) == 33


def test_observacao_da_venda_identifica_a_receita_da_taxa():
    linha = CartaoParser().parse(_CSV_CARTOES.read_text(encoding="utf-8"))[0]

    observacao = _montar_observacao(linha)

    assert f"{linha.num_parcelas}x" in observacao
    assert linha.codigo_transacao in observacao
    assert linha.status in observacao
