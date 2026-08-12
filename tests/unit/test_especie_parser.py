from decimal import Decimal

from app.integracao.conciliacao.parsers.especie_parser import EspecieParser

_CABECALHO = "data;tipo;nome;descricao;valor;observacao"


def test_parseia_linhas_validas():
    conteudo = (
        f"{_CABECALHO}\n"
        "10/08/2026;ENCONTREIRO;Samuel Augusto;;100,00;\n"
        "10/08/2026;OFERTA;;Oferta do culto de domingo;50,00;\n"
        "10/08/2026;PERSONALIZADO;;Caneca personalizada;30,00;Cor azul, tamanho G\n"
    )

    linhas = EspecieParser().parse(conteudo)

    assert len(linhas) == 3
    assert linhas[0].tipo == "ENCONTREIRO"
    assert linhas[0].nome == "Samuel Augusto"
    assert linhas[0].valor == Decimal("100.00")
    assert linhas[2].observacao == "Cor azul, tamanho G"


def test_ignora_linhas_antes_do_cabecalho():
    conteudo = "lixo antes\n" + _CABECALHO + "\n10/08/2026;OFERTA;;Oferta;50,00;\n"

    linhas = EspecieParser().parse(conteudo)

    assert len(linhas) == 1


def test_linha_sem_valor_vira_erro():
    conteudo = f"{_CABECALHO}\n10/08/2026;OFERTA;;Oferta;;\n"

    parser = EspecieParser()
    linhas = parser.parse(conteudo)

    assert len(linhas) == 0
    assert len(parser.erros) == 1
    assert parser.erros[0]["linha"] == 2


def test_linha_com_poucas_colunas_vira_erro():
    conteudo = f"{_CABECALHO}\n10/08/2026;OFERTA;50,00\n"

    parser = EspecieParser()
    linhas = parser.parse(conteudo)

    assert len(linhas) == 0
    assert len(parser.erros) == 1


def test_linhas_identicas_ganham_sufixo_ocor_na_observacao():
    conteudo = (
        f"{_CABECALHO}\n"
        "10/08/2026;OFERTA;;Oferta;50,00;\n"
        "10/08/2026;OFERTA;;Oferta;50,00;\n"
    )

    linhas = EspecieParser().parse(conteudo)

    assert len(linhas) == 2
    assert linhas[0].observacao is None
    assert linhas[1].observacao == "ocor: 2"


def test_reprocessar_mesmo_conteudo_reproduz_mesma_sequencia():
    conteudo = (
        f"{_CABECALHO}\n"
        "10/08/2026;OFERTA;;Oferta;50,00;\n"
        "10/08/2026;OFERTA;;Oferta;50,00;\n"
    )

    parser = EspecieParser()
    primeira = parser.parse(conteudo)
    segunda = parser.parse(conteudo)

    assert [l.observacao for l in primeira] == [l.observacao for l in segunda]
