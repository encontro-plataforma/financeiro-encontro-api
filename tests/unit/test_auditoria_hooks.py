from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.integracao.regras.dtos import ItemDetalhamento
from app.models.enums import TipoDetalhamento
from app.services.auditoria.hooks import _aplicar_biscoitos


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
