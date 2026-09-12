from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.models.detalhamento import Detalhamento
from app.models.encontreiro import Encontreiro
from app.models.encontrista import Encontrista
from app.models.enums import FormaPagamento, StatusLancamento, TipoDetalhamento
from app.services.auditoria_service import AuditoriaService


def _lancamento(
    id_=1,
    valor="100",
    soma="0",
    status=StatusLancamento.NAO_CONCILIADO,
    forma_pagamento=FormaPagamento.PIX,
    descricao="PIX MARIA SOUZA",
):
    lancamento = MagicMock(id=id_, descricao=descricao)
    lancamento.valor = Decimal(valor)
    lancamento.soma_detalhamentos = Decimal(soma)
    lancamento.status = status
    lancamento.cart_taxa = None
    lancamento.cart_valor_liquido = None
    lancamento.cart_parcelas = None
    lancamento.forma_pagamento = forma_pagamento
    lancamento.data_pagamento = datetime(2026, 1, 1)
    return lancamento


def _pendente(id_, nome, nome_pagador, pagamento, observacao):
    return MagicMock(
        id=id_,
        nome=nome,
        nome_pagador=nome_pagador,
        pagamento=Decimal(str(pagamento)),
        observacao=observacao,
        dt_pagamento=date(2026, 1, 1),
    )


def _db_com(lancamento, pendente_encontreiro=None, pendente_encontrista=None, detalhamentos_existentes=None):
    db = MagicMock()

    def fake_query(modelo):
        query = MagicMock()
        if modelo is Encontreiro:
            query.filter.return_value.order_by.return_value.all.return_value = (
                [pendente_encontreiro] if pendente_encontreiro else []
            )
        elif modelo is Encontrista:
            query.filter.return_value.order_by.return_value.all.return_value = (
                [pendente_encontrista] if pendente_encontrista else []
            )
        elif modelo is Detalhamento:
            query.filter.return_value.all.return_value = detalhamentos_existentes or []
            query.count.return_value = 0
        else:  # Lancamento
            query.filter.return_value.all.return_value = [lancamento] if lancamento else []
        return query

    db.query.side_effect = fake_query
    return db


def test_simular_lancamento_conciliado_retorna_so_os_existentes_sem_rodar_pipeline():
    detalhamento_existente = MagicMock(
        id=1,
        tipo=TipoDetalhamento.INSCRICAO_ENCONTRISTA,
        valor=Decimal("100"),
        referencia_id=2,
        descricao="",
    )
    lancamento = _lancamento(status=StatusLancamento.CONCILIADO)
    db = _db_com(lancamento, detalhamentos_existentes=[detalhamento_existente])
    pessoa = MagicMock(id=2, nome="Maria Souza", pagamento=Decimal("100"), observacao="Pix")

    with patch(
        "app.services.auditoria_service.LancamentoRepository.get_by_id", return_value=lancamento
    ), patch(
        "app.services.auditoria.hooks.EncontristaRepository.get_by_id", return_value=pessoa
    ):
        resultado = AuditoriaService.simular(db, lancamento.id)

    assert resultado["ja_conciliado"] is True
    assert resultado["nao_incluidos"] == []
    assert len(resultado["detalhamentos"]) == 1
    assert resultado["detalhamentos"][0]["origem"] == "EXISTENTE"
    # com o lançamento já conciliado, a Etapa A/B nem deveria rodar --
    # nenhuma pendência (Encontreiro/Encontrista) é consultada.
    assert Encontreiro not in [c.args[0] for c in db.query.call_args_list]
    assert Encontrista not in [c.args[0] for c in db.query.call_args_list]


def test_simular_ignora_pendencia_de_pagamento_multiplo_e_simula_a_normal():
    pendente_multiplo = _pendente(1, "Joao Silva", "Joao Silva", 100, "Pagamento múltiplo, ver planilha")
    pendente_normal = _pendente(2, "Maria Souza", "Maria Souza", 100, "Pix")
    lancamento = _lancamento()

    db = _db_com(lancamento, pendente_multiplo, pendente_normal, detalhamentos_existentes=[])

    with patch(
        "app.services.auditoria_service.LancamentoRepository.get_by_id", return_value=lancamento
    ), patch(
        "app.services.auditoria.pipeline.RegraRepository.list_ativos_por_escopos", return_value=[]
    ):
        resultado = AuditoriaService.simular(db, lancamento.id)

    assert resultado["ja_conciliado"] is False
    assert resultado["nao_incluidos"] == []  # pendência de pagamento múltiplo é irrelevante aqui, não aparece
    assert len(resultado["detalhamentos"]) == 1
    item = resultado["detalhamentos"][0]
    assert item["origem"] == "SIMULADO"
    assert item["referencia_id"] == 2
    assert item["valor"] == Decimal("100")


def test_processar_grava_detalhamento_e_reporta_pagamento_multiplo_em_nao_auditados():
    pendente_multiplo = _pendente(1, "Joao Silva", "Joao Silva", 100, "Pagamentos múltiplos")
    pendente_normal = _pendente(2, "Maria Souza", "Maria Souza", 100, "Pix")
    lancamento = _lancamento()

    db = _db_com(lancamento, pendente_multiplo, pendente_normal, detalhamentos_existentes=[])

    with patch(
        "app.services.auditoria.pipeline.RegraRepository.list_ativos_por_escopos", return_value=[]
    ), patch("app.services.auditoria.sink.DetalhamentoService.create") as mock_create:
        resultado = AuditoriaService.processar(db)

    mock_create.assert_called_once()
    assert resultado["vinculados_encontreiro"] == 0
    assert resultado["vinculados_encontrista"] == 1
    assert resultado["nao_auditados"] == 1
    assert "múltiplo" in resultado["detalhes_nao_auditados"][0]["motivo"].lower()
    assert "mensagem" in resultado
    assert "detalhamentos_extras_via_observacao" in resultado
