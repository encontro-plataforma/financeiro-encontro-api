from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.integracao.regras.dtos import ItemDetalhamento
from app.models.enums import TipoDetalhamento
from app.services.auditoria.sink import PersistenciaSink, SimulacaoSink


def _lancamento(id_=1, valor="100", soma="0"):
    lancamento = MagicMock(id=id_)
    lancamento.valor = Decimal(valor)
    lancamento.soma_detalhamentos = Decimal(soma)
    return lancamento


def _db_sem_detalhamentos():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    return db


def test_simulacao_capacidade_restante_eh_lida_do_banco_uma_vez_e_cacheada():
    sink = SimulacaoSink()
    db = _db_sem_detalhamentos()
    lancamento = _lancamento(valor="100", soma="20")

    assert sink.capacidade_restante(db, lancamento) == Decimal("80")

    lancamento.soma_detalhamentos = Decimal("999")  # não deve mais ser relido do banco
    assert sink.capacidade_restante(db, lancamento) == Decimal("80")


def test_simulacao_aplicar_decrementa_capacidade_em_memoria_sem_gravar_nada():
    sink = SimulacaoSink()
    db = _db_sem_detalhamentos()
    lancamento = _lancamento(valor="100", soma="0")
    itens = [ItemDetalhamento(TipoDetalhamento.INSCRICAO_ENCONTRISTA, Decimal("60"), 1)]

    erro = sink.aplicar(db, lancamento, itens)

    assert erro is None
    assert sink.capacidade_restante(db, lancamento) == Decimal("40")
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_simulacao_aplicar_barra_pendencia_que_estoura_capacidade_ja_consumida():
    sink = SimulacaoSink()
    db = _db_sem_detalhamentos()
    lancamento = _lancamento(valor="100", soma="0")

    primeira = sink.aplicar(
        db, lancamento, [ItemDetalhamento(TipoDetalhamento.INSCRICAO_ENCONTRISTA, Decimal("70"), 1)]
    )
    segunda = sink.aplicar(
        db, lancamento, [ItemDetalhamento(TipoDetalhamento.INSCRICAO_ENCONTRISTA, Decimal("50"), 2)]
    )

    assert primeira is None
    assert segunda is not None


def test_simulacao_flags_default_do_banco_e_podem_ser_marcadas_manualmente():
    sink = SimulacaoSink()

    lancamento_com_taxa = _lancamento(id_=1)
    db_com_taxa = MagicMock()
    db_com_taxa.query.return_value.filter.return_value.first.return_value = MagicMock()
    assert sink.ja_tem_taxa_cartao(db_com_taxa, lancamento_com_taxa) is True

    lancamento_sem = _lancamento(id_=2)
    db_sem = _db_sem_detalhamentos()
    assert sink.ja_tem_biscoitos(db_sem, lancamento_sem) is False
    sink.marcar_biscoitos_aplicado(lancamento_sem)
    assert sink.ja_tem_biscoitos(db_sem, lancamento_sem) is True


def test_persistencia_sink_aplicar_cria_um_detalhamento_por_item():
    sink = PersistenciaSink()
    lancamento = _lancamento(valor="100", soma="0")
    itens = [ItemDetalhamento(TipoDetalhamento.INSCRICAO_ENCONTRISTA, Decimal("60"), 1)]

    with patch("app.services.auditoria.sink.DetalhamentoService.create") as mock_create:
        erro = sink.aplicar(MagicMock(), lancamento, itens)

    assert erro is None
    mock_create.assert_called_once()
    _, dados = mock_create.call_args.args
    assert dados["lancamento_id"] == lancamento.id
    assert dados["valor"] == Decimal("60")


def test_persistencia_sink_aplicar_propaga_erro_de_capacidade_sem_criar_nada():
    sink = PersistenciaSink()
    lancamento = _lancamento(valor="100", soma="90")
    itens = [ItemDetalhamento(TipoDetalhamento.INSCRICAO_ENCONTRISTA, Decimal("60"), 1)]

    with patch("app.services.auditoria.sink.DetalhamentoService.create") as mock_create:
        erro = sink.aplicar(MagicMock(), lancamento, itens)

    assert erro is not None
    mock_create.assert_not_called()
