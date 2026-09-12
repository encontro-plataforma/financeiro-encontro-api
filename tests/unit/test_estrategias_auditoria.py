from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.integracao.regras.dtos import ItemDetalhamento
from app.models.enums import TipoDetalhamento
from app.services.auditoria.estrategias import (
    EstrategiaAuditoriaEncontreiro,
    EstrategiaAuditoriaEncontrista,
)


def test_encontreiro_pos_processar_eh_no_op():
    estrategia = EstrategiaAuditoriaEncontreiro()
    itens = [
        (ItemDetalhamento(TipoDetalhamento.INSCRICAO_ENCONTREIRO, Decimal("100"), 1), "Inscrição")
    ]

    resultado = estrategia.pos_processar(
        db=None, itens_com_origem=itens, inscricao_pendente=None, sink=None, lancamento=None
    )

    assert resultado == itens


def test_encontrista_pos_processar_aplica_biscoitos_e_marca_sink():
    encontrista = MagicMock(id=9, padrinho_id=42)
    padrinho = MagicMock(nome="Fulano")
    sink = MagicMock()
    sink.ja_tem_biscoitos.return_value = False
    itens = [
        (ItemDetalhamento(TipoDetalhamento.INSCRICAO_ENCONTRISTA, Decimal("160"), 9), "Inscrição"),
        (ItemDetalhamento(TipoDetalhamento.OUTRO, Decimal("20"), None), "Biscoitos"),
    ]

    estrategia = EstrategiaAuditoriaEncontrista()
    with patch(
        "app.services.auditoria.hooks.EncontreiroRepository.get_by_id", return_value=padrinho
    ):
        resultado = estrategia.pos_processar(
            db=MagicMock(),
            itens_com_origem=itens,
            inscricao_pendente=encontrista,
            sink=sink,
            lancamento=MagicMock(id=1),
        )

    biscoitos_item, origem = resultado[1]
    assert origem == "Biscoitos"
    assert biscoitos_item.descricao == "Biscoitos da ficha 9 - Fulano"
    sink.marcar_biscoitos_aplicado.assert_called_once()


def test_encontrista_pos_processar_nao_marca_sink_quando_ja_tinha_biscoitos():
    sink = MagicMock()
    sink.ja_tem_biscoitos.return_value = True
    encontrista = MagicMock(id=9, padrinho_id=42)
    itens = [
        (ItemDetalhamento(TipoDetalhamento.INSCRICAO_ENCONTRISTA, Decimal("160"), 9), "Inscrição"),
        (ItemDetalhamento(TipoDetalhamento.OUTRO, Decimal("20"), None), "Biscoitos"),
    ]

    estrategia = EstrategiaAuditoriaEncontrista()
    resultado = estrategia.pos_processar(
        db=MagicMock(),
        itens_com_origem=itens,
        inscricao_pendente=encontrista,
        sink=sink,
        lancamento=MagicMock(id=1),
    )

    assert [item.tipo for item, _ in resultado] == [TipoDetalhamento.INSCRICAO_ENCONTRISTA]
    sink.marcar_biscoitos_aplicado.assert_not_called()
