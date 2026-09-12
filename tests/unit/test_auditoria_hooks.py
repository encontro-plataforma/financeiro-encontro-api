from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.integracao.regras.dtos import ItemDetalhamento
from app.models.enums import TipoDetalhamento
from app.services.auditoria.hooks import _aplicar_biscoitos, _aplicar_taxa_cartao


def test_primeiro_match_desconta_taxa_da_inscricao_e_acrescenta_item_de_taxa():
    itens = [
        (ItemDetalhamento(TipoDetalhamento.INSCRICAO_ENCONTRISTA, Decimal("160"), 1), "Inscrição"),
        (ItemDetalhamento(TipoDetalhamento.OUTRO, Decimal("20"), None, "Biscoitos"), "Biscoitos"),
    ]

    ajustados = _aplicar_taxa_cartao(itens, Decimal("10.06"), ja_tem_taxa=False, origem_taxa="TAXA")

    assert [(item.tipo, item.valor, origem) for item, origem in ajustados] == [
        (TipoDetalhamento.INSCRICAO_ENCONTRISTA, Decimal("149.94"), "Inscrição"),
        (TipoDetalhamento.OUTRO, Decimal("20"), "Biscoitos"),
        (TipoDetalhamento.OUTRO, Decimal("10.06"), "TAXA"),
    ]
    # soma final continua batendo com o valor bruto do lançamento (180)
    assert sum(item.valor for item, _ in ajustados) == Decimal("180")


def test_proximo_match_do_mesmo_lancamento_nao_desconta_nem_repete_taxa():
    itens = [
        (ItemDetalhamento(TipoDetalhamento.INSCRICAO_ENCONTREIRO, Decimal("100"), 2), "Inscrição"),
    ]

    ajustados = _aplicar_taxa_cartao(itens, Decimal("11.18"), ja_tem_taxa=True, origem_taxa="TAXA")

    assert ajustados == itens


def test_sem_item_de_inscricao_desconta_do_primeiro_item():
    itens = [
        (ItemDetalhamento(TipoDetalhamento.OFERTA, Decimal("50"), None), "Oferta"),
    ]

    ajustados = _aplicar_taxa_cartao(itens, Decimal("5"), ja_tem_taxa=False, origem_taxa="TAXA")

    assert [(item.tipo, item.valor) for item, _ in ajustados] == [
        (TipoDetalhamento.OFERTA, Decimal("45")),
        (TipoDetalhamento.OUTRO, Decimal("5")),
    ]


def test_biscoitos_primeiro_match_seta_descricao_com_ficha_e_padrinho():
    encontrista = MagicMock(id=6, padrinho_id=42)
    padrinho = MagicMock(nome="Karen Maiara")
    itens = [
        (
            ItemDetalhamento(TipoDetalhamento.INSCRICAO_ENCONTRISTA, Decimal("160"), 6),
            "Inscrição (valor no pagamento)",
        ),
        (ItemDetalhamento(TipoDetalhamento.OUTRO, Decimal("20"), None), "Biscoitos"),
    ]

    with patch(
        "app.services.auditoria.hooks.EncontreiroRepository.get_by_id",
        return_value=padrinho,
    ):
        ajustados, aplicado = _aplicar_biscoitos(
            db=None, itens_com_origem=itens, encontrista=encontrista, ja_tem_biscoitos=False
        )

    assert aplicado is True
    biscoitos_item, origem = ajustados[1]
    assert origem == "Biscoitos"
    assert biscoitos_item.descricao == "Biscoitos da ficha 6 - Karen Maiara"


def test_biscoitos_proximo_match_do_mesmo_lancamento_nao_repete():
    encontrista = MagicMock(id=7, padrinho_id=42)
    itens = [
        (
            ItemDetalhamento(TipoDetalhamento.INSCRICAO_ENCONTRISTA, Decimal("160"), 7),
            "Inscrição (valor no pagamento)",
        ),
        (ItemDetalhamento(TipoDetalhamento.OUTRO, Decimal("20"), None), "Biscoitos"),
    ]

    ajustados, aplicado = _aplicar_biscoitos(
        db=None, itens_com_origem=itens, encontrista=encontrista, ja_tem_biscoitos=True
    )

    assert aplicado is False
    assert [item.tipo for item, _ in ajustados] == [TipoDetalhamento.INSCRICAO_ENCONTRISTA]
